# Commands and execution boundary

`run-once.ps1` records the exact guarded production commands. It was invoked once with `& ./test-output/arm-macos/full-system/r9-boot-test/run-once.ps1` and terminated at line15 (Other VM process running). Its migration, CheckOnly and actual-launch lines were not reached. The transcript retains the guard failure.

Synthetic tests executed once in the pinned sha256:13d68aa0979e77f326648f3e4c1f023f1fe90d74feb8cc0167a09dbccdc50635 image:

```powershell
docker run --rm --name r9-boot-synthetic --read-only --network none --cpus=2 --memory=512m --memory-swap=512m --pids-limit=128 --ulimit core=0 --tmpfs /tmp:rw,nosuid,nodev,size=64m --mount "type=bind,source=$base,target=/parent,readonly" -e PYTHONDONTWRITEBYTECODE=1 --entrypoint /usr/bin/python3 $img -m unittest discover -s /parent/full-system/r9-boot-test -p 'test_fence*.py' -v
```

Here $base is <WORKSPACE>/macos/test-output/arm-macos and $img is the pinned image above. Output is synthetic-tests.txt.

Pre/final state inspections used the same image, --rm, read-only root, network none, cpus2, memory512m, pids128, core0, read-only macos-orchard-build at /work, read-only macos-golden-pristine-guest at /control, and read-only $base at /parent, entrypoint /usr/bin/python3, argument /parent/full-system/r9-boot-test/inspect-state.py. Owned names: r9-boot-prestate and r9-boot-final-state. Outputs: pre-state.json/post-state.json.

Read-only host checks used Get-Process -Id 84568, Get-CimInstance Win32_Process filtered to qemu-system/vmware-vmx/VirtualBoxVM names, Get-FileHash on the two host artifacts, Get-Content host-space-live.json, docker ps, docker volume inspect, and docker inspect macos-golden-local-raw. No command stopped the conflicting VM.
