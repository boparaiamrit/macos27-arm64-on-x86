param([switch]$Capacity)
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $PSScriptRoot).Path
$artifacts=Join-Path $source 'artifacts'
New-Item -ItemType Directory -Force -Path $artifacts | Out-Null
if([IO.DriveInfo]::new([IO.Path]::GetPathRoot($source)).AvailableFreeSpace -lt 11GB){throw 'Offline tests need 10 GiB reserve plus 1 GiB test headroom.'}
$stamp=[DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ').ToLowerInvariant()
$name='macos-read-cache-test-repro-'+$stamp
$image='sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635'
$dockerArgs=@('run','--rm','--name',$name,'--read-only','--network','none','--cpus=1','--memory=1g','--memory-swap=1g','--pids-limit=128',
    '--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--mount',"type=bind,source=$source,target=/proxy,readonly",'--mount',"type=bind,source=$artifacts,target=/artifacts",
    '-e','PYTHONDONTWRITEBYTECODE=1','-e','READ_CACHE_TEST_ARTIFACT_DIR=/artifacts','--workdir','/proxy','--entrypoint','/usr/bin/python3')
$volume=$null
try {
    if($Capacity){
        $volume=$name+'-capacity'
        & docker volume create --label purpose=offline-read-cache-capacity $volume | Out-Null
        if($LASTEXITCODE -ne 0){throw 'Could not create owned test volume.'}
        $dockerArgs+=@('--mount',"type=volume,source=$volume,target=/capacity",$image,'-B','/proxy/capacity_check.py')
    } else {
        $dockerArgs+=@($image,'-B','-m','unittest','-v','test_proxy')
    }
    & docker @dockerArgs 2>&1 | Tee-Object -FilePath (Join-Path $artifacts ($name+'.log'))
    if($LASTEXITCODE -ne 0){throw 'Offline qualification failed; retained its bounded test log.'}
    if([IO.DriveInfo]::new([IO.Path]::GetPathRoot($source)).AvailableFreeSpace -lt 10GB){throw 'Host reserve is below 10 GiB.'}
} finally {
    if($volume){
        $labels=& docker volume inspect $volume --format '{{json .Labels}}' | ConvertFrom-Json
        if($labels.purpose -eq 'offline-read-cache-capacity'){
            & docker volume rm $volume | Out-Null
        }
    }
}
