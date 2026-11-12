#!/bin/bash
set -Eeuo pipefail
export PYTHONNOUSERSITE=1
source_root=/build/source
build_dir=/build/emulator
if [ ! -e "$source_root/configure" ]; then
    mkdir -p "$source_root"
    git -c safe.directory=/work/27on86 -C /work/27on86 archive HEAD | tar -x -C "$source_root"
fi
test -L "$source_root/subprojects/libvhost-user/standard-headers/linux"
mkdir -p "$build_dir"
cd "$build_dir"
if [ ! -e build.ninja ]; then
    "$source_root/configure" --target-list=aarch64-softmmu \
        --disable-docs --disable-werror --disable-debug-info \
        --disable-gtk --disable-sdl --disable-opengl --disable-vnc \
        --disable-xen --disable-kvm
fi
ninja -j8 qemu-system-aarch64
QEMU_27ON86_BUILD_DIR="$build_dir" QEMU_27ON86_OUTPUT_DIR=/work/evidence \
    bash "$source_root/scripts/27on86/check-vmapple-tcg.sh"
cp "$build_dir/qemu-system-aarch64" /work/evidence/
sha256sum /work/evidence/qemu-system-aarch64
