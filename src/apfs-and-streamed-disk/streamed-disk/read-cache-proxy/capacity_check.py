"""Offline full-capacity verification, only in a new disposable test volume."""
import hashlib
import json
import os
from pathlib import Path
import time
from cache import BlockCache
from common import BLOCK, DATA_LIMIT, Guard, MAX_READ, admit_resources

admit_resources()
root=Path('/capacity')
assert root.is_dir() and not list(root.iterdir()), 'new empty owned test volume required'
cache=root/'cache';cache.mkdir()
sample=root/'fixture-host-sample.json'


def refresh():
    sample.write_text(json.dumps(dict(drive='C:\\',free_bytes=30*1024**3,observed_at=time.time())))


refresh()
guard=Guard(sample,cache)
size=DATA_LIMIT+BLOCK+17
identifier=hashlib.sha256(b'offline full capacity identity').digest()


class Source:
    calls=0
    def pread(self,count,offset):
        self.calls+=1
        return bytes([offset//BLOCK%251])*count


source=Source();started=time.monotonic();c=BlockCache(cache,identifier,size,guard)
for offset in range(0,DATA_LIMIT,MAX_READ):
    refresh()
    data=c.read(source,offset,MAX_READ)
    assert data==bytes([offset//BLOCK%251])*MAX_READ
assert c.count==DATA_LIMIT//BLOCK==8192
before=guard.check()
for _ in range(3):
    refresh()
    data=c.read(source,DATA_LIMIT,17)
    assert data==bytes([DATA_LIMIT//BLOCK%251])*17
assert c.count==8192 and guard.check()==before
c.close();refresh();c=BlockCache(cache,identifier,size,guard)
calls=source.calls
assert c.read(source,0,100)==bytes(100)
assert source.calls==calls
c.close()
result=dict(status='PASS',block_bytes=BLOCK,cached_blocks=8192,cached_payload_bytes=DATA_LIMIT,
            disk_bytes=before,uncached_budget_overflow_served=True,restart_hit_verified=True,
            elapsed_seconds=time.monotonic()-started,
            resources={name:(Path('/sys/fs/cgroup')/name).read_text() for name in
                       ('memory.peak','memory.events','memory.max','memory.swap.max','cpu.max','pids.max')})
Path('/artifacts/capacity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
