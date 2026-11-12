param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$StreamedRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$StreamedArtifacts = Join-Path $StreamedRoot 'artifacts'
New-Item -ItemType Directory -Path $StreamedArtifacts -Force | Out-Null
if ((Get-PSDrive -Name C).Free -lt (11GB)) {
    throw 'Refusing image/test work: Windows C: has less than the 10 GiB reserve plus 1 GiB build allowance.'
}
if (-not $SkipBuild) {
    & docker build -t macos-streamed-guest:local -f (Join-Path $StreamedRoot 'Dockerfile') $StreamedRoot 2>&1 |
        Tee-Object -FilePath (Join-Path $StreamedArtifacts 'docker-build.log')
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed: $LASTEXITCODE" }
}
$StreamedParent = Split-Path $StreamedRoot -Parent
$StreamedFrozen = Join-Path $StreamedParent 'full-system\converter-snapshot'
$StreamedAPFS = Join-Path $StreamedParent 'apfs-tools\src'
$StreamedDockerArgs = @('run', '--rm', '--network', 'none', '--read-only', '--memory', '512m',
    '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
    '--tmpfs', '/tmp:rw,nosuid,nodev,size=67108864',
    '--mount', "type=bind,source=$StreamedRoot,target=/streamed-disk,readonly",
    '--mount', "type=bind,source=$StreamedFrozen,target=/frozen,readonly",
    '--mount', "type=bind,source=$StreamedAPFS,target=/apfs-src,readonly",
    '--mount', "type=bind,source=$StreamedArtifacts,target=/artifacts",
    '--env', 'ARTIFACT_DIR=/artifacts', '--entrypoint', '/usr/bin/python3',
    'macos-streamed-guest:local', '/streamed-disk/test_streamed_disk.py')
& docker @StreamedDockerArgs 2>&1 | Tee-Object -FilePath (Join-Path $StreamedArtifacts 'offline-tests.log')
if ($LASTEXITCODE -ne 0) { throw "Offline tests failed: $LASTEXITCODE" }
& docker image inspect macos-streamed-guest:local macos-orchard-runtime:local |
    Set-Content -LiteralPath (Join-Path $StreamedArtifacts 'image-inspect.json') -Encoding utf8
$StreamedPackageCheck = @'
import hashlib,json,subprocess
from pathlib import Path
print(json.dumps({"files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path("/streamed-disk").glob("*.py")}, "nbdkit": subprocess.check_output(["nbdkit","--version"],text=True).strip()}))
'@
$StreamedPackaged = & docker run --rm --network none --read-only --memory 128m --pids-limit 32 `
    --cap-drop ALL --security-opt no-new-privileges --entrypoint /usr/bin/python3 `
    macos-streamed-guest:local -c $StreamedPackageCheck
if ($LASTEXITCODE -ne 0) { throw 'Packaged image verification failed.' }
$StreamedPackaged | Set-Content -LiteralPath (Join-Path $StreamedArtifacts 'packaged-files.json') -Encoding utf8
$StreamedPackagedFiles = ($StreamedPackaged | ConvertFrom-Json).files
foreach ($StreamedFile in (Get-ChildItem -LiteralPath $StreamedRoot -Filter '*.py' -File)) {
    if ($StreamedPackagedFiles.($StreamedFile.Name) -ne (Get-FileHash -LiteralPath $StreamedFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()) {
        throw "Packaged source mismatch: $($StreamedFile.Name)"
    }
}
$StreamedHashes = Get-ChildItem -LiteralPath $StreamedRoot -File |
    Where-Object { $_.Extension -in '.py', '.ps1', '.md' -or $_.Name -in 'Dockerfile', '.dockerignore' } |
    ForEach-Object { @{ name = $_.Name; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() } }
@{ captured_at = (Get-Date).ToUniversalTime().ToString('o'); windows_c_free_bytes = (Get-PSDrive -Name C).Free;
   files = @($StreamedHashes) } | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $StreamedArtifacts 'implementation-hashes.json') -Encoding utf8
