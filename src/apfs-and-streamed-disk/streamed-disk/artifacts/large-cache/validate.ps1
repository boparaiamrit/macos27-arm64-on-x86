param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$largeEvidence = $PSScriptRoot
$largeRoot = [System.IO.Path]::GetFullPath((Join-Path $largeEvidence '..\..'))
$largeParent = Split-Path $largeRoot -Parent
$largeRepository = [System.IO.Path]::GetFullPath((Join-Path $largeParent '..\..'))
$largeFrozen = Join-Path $largeParent 'full-system\converter-snapshot'
$largeAPFS = Join-Path $largeParent 'apfs-tools\src'
$largeExpectedBase = 'sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635'
$largeBase = & docker image inspect macos-streamed-guest:local --format '{{.Id}}'
if ($LASTEXITCODE -ne 0 -or $largeBase -ne $largeExpectedBase) { throw 'Required base image identity mismatch.' }
if ((Get-PSDrive -Name C).Free -lt 11GB) { throw 'Need the 10GiB host reserve plus 1GiB offline build allowance.' }
if (-not $SkipBuild) {
    & docker build --network none --pull=false -t macos-streamed-guest-large:local `
        -f (Join-Path $largeRoot 'Dockerfile.large-cache.offline') $largeRoot 2>&1 |
        Tee-Object -FilePath (Join-Path $largeEvidence 'docker-build.log')
    if ($LASTEXITCODE -ne 0) { throw 'Offline COPY-only image build failed.' }
}
$largeImagesJson = & docker image inspect macos-streamed-guest:local macos-streamed-guest-large:local
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect offline image identities.' }
$largeImagesJson | Set-Content -LiteralPath (Join-Path $largeEvidence 'image-inspect.json') -Encoding utf8
$largeImages = @($largeImagesJson | ConvertFrom-Json)
if ($largeImages[0].Id -ne $largeExpectedBase) { throw 'Base image changed during build.' }
if ($largeImages[1].RootFS.Layers.Count -ne $largeImages[0].RootFS.Layers.Count + 1) { throw 'New image is not a single COPY layer over base.' }
for ($largeIndex = 0; $largeIndex -lt $largeImages[0].RootFS.Layers.Count; $largeIndex++) {
    if ($largeImages[1].RootFS.Layers[$largeIndex] -ne $largeImages[0].RootFS.Layers[$largeIndex]) { throw 'Base filesystem layer mismatch.' }
}
$largePackagedCode = @'
import ast,hashlib,json,subprocess
from pathlib import Path
root=Path('/streamed-disk')
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')}
for p in root.glob('*.py'):
    ast.parse(p.read_bytes(),filename=str(p))
print(json.dumps({'files':files,'python_syntax':'PASS','nbdkit':subprocess.check_output(['nbdkit','--version'],text=True).strip()}))
'@
$largePackaged = & docker run --rm --network none --read-only --memory 128m --memory-swap 128m --cpus 2 `
    --pids-limit 32 --cap-drop ALL --security-opt no-new-privileges --entrypoint /usr/bin/python3 `
    macos-streamed-guest-large:local -B -c $largePackagedCode
if ($LASTEXITCODE -ne 0) { throw 'Packaged source/syntax verification failed.' }
$largePackaged | Set-Content -LiteralPath (Join-Path $largeEvidence 'packaged-files.json') -Encoding utf8
$largePackageFiles = ($largePackaged | ConvertFrom-Json).files
$largeHostFiles = @(Get-ChildItem -LiteralPath $largeRoot -Filter '*.py' -File)
if (@($largePackageFiles.PSObject.Properties).Count -ne $largeHostFiles.Count) { throw 'Packaged Python file set mismatch.' }
foreach ($largeFile in $largeHostFiles) {
    if ($largePackageFiles.($largeFile.Name) -ne (Get-FileHash -LiteralPath $largeFile.FullName -Algorithm SHA256).Hash.ToLowerInvariant()) {
        throw "Packaged source mismatch: $($largeFile.Name)"
    }
}
$largeBaseSourceCode = @'
import json
from pathlib import Path
print(json.dumps({name:Path('/streamed-disk',name).read_text() for name in ['streamed_raw.py','serve.py','nbdkit_streamed.py']}))
'@
$largeBaseSource = & docker run --rm --network none --read-only --memory 128m --memory-swap 128m --cpus 2 `
    --pids-limit 32 --cap-drop ALL --security-opt no-new-privileges --entrypoint /usr/bin/python3 `
    macos-streamed-guest:local -B -c $largeBaseSourceCode
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect required base source.' }
$largeBaseSource | Set-Content -LiteralPath (Join-Path $largeEvidence 'base-image-source.json') -Encoding utf8
& docker run --rm --network none --read-only --memory 128m --memory-swap 128m --cpus 2 `
    --pids-limit 32 --cap-drop ALL --security-opt no-new-privileges `
    --mount "type=bind,source=$largeEvidence,target=/artifacts" --entrypoint /usr/bin/timeout `
    macos-streamed-guest-large:local 10s /usr/bin/python3 -B /artifacts/audit-invariants.py
if ($LASTEXITCODE -ne 0) { throw 'Protected behavior source audit failed.' }
$largeCommands = @()
foreach ($largeSuite in @(
    @{ name='legacy'; memory='512m'; seconds='100s'; file='test_streamed_disk.py' },
    @{ name='large-cache'; memory='6g'; seconds='70s'; file='test_large_cache.py' }
)) {
    $largeArgs = @('run','--rm','--network','none','--read-only','--memory',$largeSuite.memory,
        '--memory-swap',$largeSuite.memory,'--cpus','2','--pids-limit','128',
        '--cap-drop','ALL','--security-opt','no-new-privileges',
        '--tmpfs','/tmp:rw,nosuid,nodev,size=67108864',
        '--mount',"type=bind,source=$largeFrozen,target=/frozen,readonly",
        '--mount',"type=bind,source=$largeAPFS,target=/apfs-src,readonly",
        '--mount',"type=bind,source=$largeEvidence,target=/artifacts",
        '--env','ARTIFACT_DIR=/artifacts','--entrypoint','/usr/bin/timeout',
        'macos-streamed-guest-large:local','--signal=TERM','--kill-after=7s',$largeSuite.seconds,
        '/usr/bin/python3','-B','/artifacts/offline-entry.py',$largeSuite.name,"/streamed-disk/$($largeSuite.file)")
    $largeCommands += @{ suite=$largeSuite.name; docker_arguments=$largeArgs; image_id=$largeImages[1].Id }
    & docker @largeArgs 2>&1 | Tee-Object -FilePath (Join-Path $largeEvidence "offline-$($largeSuite.name)-tests.log")
    if ($LASTEXITCODE -ne 0) { throw "Offline $($largeSuite.name) suite failed: $LASTEXITCODE" }
}
$largeCommands | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $largeEvidence 'test-commands.json') -Encoding utf8
$largeAdmissionCode = @'
import json
from unittest.mock import patch
from frozen import oci
from streamed_raw import VerifiedSource,CacheBudgetError,cgroup_memory_limit
limit=cgroup_memory_limit()
assert limit == 512 << 20, limit
with patch.object(oci.LayerSource,'__init__',side_effect=AssertionError('base allocation reached')) as base:
    for count in range(3,9):
        try:
            VerifiedSource(None,None,cache_layers=count,guard=None,report=lambda *a,**k:None)
        except CacheBudgetError:
            pass
        else:
            raise AssertionError('inadequate actual cgroup limit admitted')
    base.assert_not_called()
print(json.dumps({'status':'PASS','cgroup_memory_max_bytes':limit,'rejected_capacities':list(range(3,9)),
                  'before_base_allocation':True,'before_fetch':True,'network':'none'}))
'@
$largeAdmission = & docker run --rm --network none --read-only --memory 512m --memory-swap 512m --cpus 2 `
    --pids-limit 32 --cap-drop ALL --security-opt no-new-privileges `
    --mount "type=bind,source=$largeFrozen,target=/frozen,readonly" `
    --mount "type=bind,source=$largeAPFS,target=/apfs-src,readonly" `
    --entrypoint /usr/bin/timeout macos-streamed-guest-large:local --signal=TERM --kill-after=2s 10s `
    /usr/bin/python3 -B -c $largeAdmissionCode
if ($LASTEXITCODE -ne 0) { throw 'Actual insufficient cgroup admission smoke failed.' }
$largeAdmission | Set-Content -LiteralPath (Join-Path $largeEvidence 'actual-cgroup-admission.json') -Encoding utf8
$largeBaseline = Get-Content -LiteralPath (Join-Path $largeEvidence 'baseline.json') -Raw | ConvertFrom-Json
$largeProtected = @($largeBaseline.files | Where-Object { $_.path -notmatch '/(streamed_raw.py|serve.py|nbdkit_streamed.py|README.md)$' })
foreach ($largeFile in $largeProtected) {
    $largeAbsolute = Join-Path $largeRepository $largeFile.path
    if ((Get-FileHash -LiteralPath $largeAbsolute -Algorithm SHA256).Hash.ToLowerInvariant() -ne $largeFile.sha256) {
        throw "Protected source changed from baseline: $($largeFile.path)"
    }
}
$largeReaderBaseline = Get-Content -LiteralPath (Join-Path $largeEvidence 'reader-dependency-baseline.json') -Raw | ConvertFrom-Json
foreach ($largeFile in $largeReaderBaseline) {
    if ((Get-FileHash -LiteralPath (Join-Path $largeRepository $largeFile.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $largeFile.sha256) {
        throw "Parent reader dependency changed during validation: $($largeFile.path)"
    }
}
$largeFrozenFiles = @('oci_stream.py','asif_plan.py','asif_to_raw.py') | ForEach-Object {
    @{ name=$_; sha256=(Get-FileHash -LiteralPath (Join-Path $largeFrozen $_) -Algorithm SHA256).Hash.ToLowerInvariant() }
}
$largeSourceFiles = @(Get-ChildItem -LiteralPath $largeRoot -File | Where-Object { $_.Extension -in '.py','.md' -or $_.Name -eq 'Dockerfile.large-cache.offline' } | ForEach-Object {
    @{ name=$_.Name; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
})
$largeLegacy = Get-Content -LiteralPath (Join-Path $largeEvidence 'test-results.json') -Raw | ConvertFrom-Json
$largeNewTests = Get-Content -LiteralPath (Join-Path $largeEvidence 'large-cache-tests.json') -Raw | ConvertFrom-Json
$largeResources = @('legacy-resources.json','large-cache-resources.json') | ForEach-Object {
    Get-Content -LiteralPath (Join-Path $largeEvidence $_) -Raw | ConvertFrom-Json
}
$largeCancellation = @(Get-Content -LiteralPath (Join-Path $largeEvidence 'offline-cancellation-telemetry.jsonl') | ForEach-Object { $_ | ConvertFrom-Json })
if (-not $largeLegacy.successful -or $largeLegacy.tests -ne 29 -or -not $largeNewTests.successful -or $largeNewTests.tests -ne 14) { throw 'Test count or success gate failed.' }
if (@($largeResources | Where-Object { -not $_.within_1gib_actual_memory_bound -or $_.exit_code -ne 0 }).Count) { throw 'Resource gate failed.' }
if (@($largeCancellation | Where-Object { -not $_.process_group_gone }).Count) { throw 'Cancellation process group gate failed.' }
if ((& docker image inspect macos-streamed-guest:local --format '{{.Id}}') -ne $largeExpectedBase) { throw 'Original image tag changed.' }
$largePhysical = Get-CimInstance -ClassName Win32_OperatingSystem
@{ gate='PASS'; scope='offline fixture implementation only; parent live review required';
   captured_at=(Get-Date).ToUniversalTime().ToString('o'); base_image_id=$largeBase; new_image_id=$largeImages[1].Id;
   source_hashes=$largeSourceFiles; frozen_hashes=@($largeFrozenFiles); reader_dependency_hashes=@($largeReaderBaseline); packaged_python_files=$largeHostFiles.Count;
   protected_baseline_hashes_unchanged=$true; invariant_audit='invariant-audit.json'; rootfs_change='exactly one COPY layer over required base';
   legacy_tests=$largeLegacy; large_cache_tests=$largeNewTests; resources=@($largeResources); actual_cgroup_admission=($largeAdmission | ConvertFrom-Json);
   cancellation_samples=$largeCancellation.Count; maximum_cancellation_seconds=($largeCancellation | Measure-Object seconds_to_stop -Maximum).Maximum;
   windows_c_free_bytes=(Get-PSDrive -Name C).Free; physical_free_bytes=([long]$largePhysical.FreePhysicalMemory * 1024);
   live_golden_fetch=$false; backend_restart=$false; vm_run=$false; existing_tag_replaced=$false;
   profile_file='proposed-live-profile.ps1.txt'; proposed_cache_layers=8; proposed_memory_bytes=6GB; proposed_cpus=2
} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $largeEvidence 'handoff.json') -Encoding utf8
Write-Output "PASS: 29 legacy + 14 cache tests; packaged hashes match; parent image and protected code unchanged."
