#!/bin/bash
set -Eeuo pipefail
firmware=/work/darwin/firmware
evidence=/work/evidence
free_bytes=$(python3 -c 'import shutil; print(shutil.disk_usage("/work").free)')
if [ "$free_bytes" -lt 1073741824 ]; then
    echo 'At least 1 GiB of free host storage is required before another bounded boot.' >&2
    exit 3
fi
run_name="${RUN_NAME:-golden-gate-restore}"
[[ "$run_name" =~ ^[a-zA-Z0-9_-]+$ ]] || exit 2
boot_seconds="${BOOT_SECONDS:-60}"
[[ "$boot_seconds" =~ ^[0-9]+$ ]] && [ "$boot_seconds" -ge 10 ] && [ "$boot_seconds" -le 300 ] || exit 2
boot_args='rd=md0 serial=3 -v -noprogress wdt=-1 wlan-olyhal-abort'
case "${BOOT_MODE:-restore}" in
    restore) ;;
    single-user) boot_args+=' -s' ;;
    *) exit 2 ;;
esac
serial_args=(-serial mon:stdio)
if [ "${SERIAL_SOCKET:-0}" = 1 ]; then
    serial_args=(-chardev socket,id=serial0,path=/work/evidence/serial.sock,server=on,wait=off,logfile="$evidence/$run_name-serial.log" -serial chardev:serial0)
fi
for name in bootkc dtree.raw ramdisk.tc ramdisk.dmg sptm txm; do
    test -s "$firmware/$name"
done
python3 /build/darwin-vm/dt_fixup.py -nvram /build/darwin-vm/nvram.bin \
    "$firmware/dtree.raw" "$firmware/dtree"
set +e
timeout --signal=TERM --kill-after=5s "${boot_seconds}s" \
    /build/darwin-emulator/qemu-system-aarch64 \
    -M darwin -accel tcg -bootkc "$firmware/bootkc" \
    -dtree "$firmware/dtree" -tc "$firmware/ramdisk.tc" \
    -ramdisk "$firmware/ramdisk.dmg" -sptm "$firmware/sptm" -txm "$firmware/txm" \
    -args "$boot_args" \
    -nographic "${serial_args[@]}" -m 8G \
    > "$evidence/$run_name.log" 2>&1
result=$?
set -e
printf '%s\n' "$result" > "$evidence/$run_name-exit.txt"
grep -aE 'Darwin Kernel Version|Darwin Bootstrapper|Restore environment|panic\(|Error|error:|bash-[0-9]|launchd' \
    "$evidence/$run_name.log" | tail -n 24 || true
printf 'QEMU_EXIT=%s\n' "$result"
if [ "$result" -ne 0 ] && [ "$result" -ne 124 ]; then
    exit "$result"
fi
