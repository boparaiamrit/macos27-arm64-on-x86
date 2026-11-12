#!/bin/bash
set -Eeuo pipefail
export PYTHONNOUSERSITE=1
if [ ! -d /build/darwin-vm/.git ]; then
    git clone --depth 1 https://github.com/jprx/darwin-vm.git /build/darwin-vm
fi
cd /build/darwin-vm
git submodule update --init --depth 1 qemu-sptm
mkdir -p /build/darwin-emulator
cd /build/darwin-emulator
if [ ! -f build.ninja ]; then
    /build/darwin-vm/qemu-sptm/configure --target-list=aarch64-softmmu \
        --disable-docs --disable-werror --disable-debug-info \
        --disable-gtk --disable-sdl --disable-opengl --disable-vnc \
        --disable-xen --disable-kvm
fi
ninja -j6 qemu-system-aarch64
./qemu-system-aarch64 --version
./qemu-system-aarch64 -machine help | grep darwin
git -C /build/darwin-vm rev-parse HEAD
git -C /build/darwin-vm/qemu-sptm rev-parse HEAD
