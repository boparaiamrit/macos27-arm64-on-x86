param(
    [ValidateSet("15", "26", "14", "13")]
    [string]$Version = "15",
    [int]$CpuCores = 16,
    [string]$RamSize = "12G",
    [string]$DiskSize = "64G",
    [switch]$UnattendedInstall
)

$ErrorActionPreference = "Stop"

Write-Host "[1/3] Enabling WSL2 Intel VT-x KVM hardware acceleration (/dev/kvm + ignore_msrs=1)..." -ForegroundColor Cyan
docker run --rm --privileged --pid=host alpine:latest nsenter -t 1 -m -u -n -i sh -c "modprobe kvm_intel && echo 1 > /sys/module/kvm/parameters/ignore_msrs && echo 0 > /sys/module/kvm/parameters/report_ignored_msrs && chmod 666 /dev/kvm && ls -la /dev/kvm"

Write-Host "[2/3] Ensuring native ext4 storage volume (macos-kvm-storage) exists..." -ForegroundColor Cyan
docker volume create macos-kvm-storage | Out-Null

$manualFlag = if ($UnattendedInstall) { "N" } else { "Y" }
Write-Host "[3/3] Launching hardware-accelerated macOS $Version container ($CpuCores cores, $RamSize RAM, MANUAL=$manualFlag)..." -ForegroundColor Cyan
docker rm -f macos 2>$null | Out-Null
docker run -d `
    --name macos `
    --device /dev/kvm `
    --device /dev/net/tun `
    --cap-add NET_ADMIN `
    -e VERSION="$Version" `
    -e CPU_CORES="$CpuCores" `
    -e RAM_SIZE="$RamSize" `
    -e DISK_SIZE="$DiskSize" `
    -e CONNECTIONS="8" `
    -e MANUAL="$manualFlag" `
    -p 8006:8006 `
    -p 5900:5900/tcp `
    -p 5900:5900/udp `
    -p 2222:22/tcp `
    -v macos-kvm-storage:/storage `
    --restart unless-stopped `
    macos-kvm:local

Write-Host "macOS KVM instance is running!" -ForegroundColor Green
Write-Host "  Web GUI (noVNC) : http://localhost:8006" -ForegroundColor Yellow
Write-Host "  Direct VNC      : localhost:5900" -ForegroundColor Yellow
Write-Host "  SSH Port        : localhost:2222" -ForegroundColor Yellow
