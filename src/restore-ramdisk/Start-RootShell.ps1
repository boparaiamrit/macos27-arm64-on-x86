param([switch]$PreflightOnly)
$ErrorActionPreference = 'Stop'
$experimentPath = $PSScriptRoot
$systemFree = (Get-Volume -DriveLetter $env:SystemDrive.Substring(0,1)).SizeRemaining
if ($systemFree -lt 2GB) {
    throw 'Free at least 2 GiB on the Windows system drive before starting another VM.'
}
foreach ($inputName in @('bootkc','dtree','ramdisk.tc','ramdisk.dmg','sptm','txm')) {
    if (-not (Test-Path -LiteralPath (Join-Path $experimentPath "darwin/firmware/$inputName"))) {
        throw "Missing local firmware input: $inputName"
    }
}
docker image inspect macos-arm-research:local --format '{{.Id}}'
if ($LASTEXITCODE -ne 0) { throw 'Missing local research image.' }
docker volume inspect macos-arm-research-build --format '{{.Name}}'
if ($LASTEXITCODE -ne 0) { throw 'Missing local emulator build volume.' }
if ($PreflightOnly) { return }
$firmware = '/work/darwin/firmware'
$dockerArgs = @(
    'run','--rm','-it','--cpus=4','--memory=10g',
    '--mount',"type=bind,source=$experimentPath,target=/work,readonly",
    '--mount','type=volume,source=macos-arm-research-build,target=/build,readonly',
    '--entrypoint','/build/darwin-emulator/qemu-system-aarch64',
    'macos-arm-research:local','-M','darwin','-accel','tcg',
    '-bootkc',"$firmware/bootkc",'-dtree',"$firmware/dtree",
    '-tc',"$firmware/ramdisk.tc",'-ramdisk',"$firmware/ramdisk.dmg",
    '-sptm',"$firmware/sptm",'-txm',"$firmware/txm",
    '-args','rd=md0 serial=3 -v -noprogress wdt=-1 wlan-olyhal-abort -s',
    '-nographic','-serial','mon:stdio','-m','8G'
)
& docker @dockerArgs
exit $LASTEXITCODE
