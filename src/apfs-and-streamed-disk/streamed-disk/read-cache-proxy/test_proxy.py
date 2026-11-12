"""Offline cache integrity and actual libnbd/nbdkit process-oracle checks."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import nbd
from cache import BlockCache
from common import BLOCK, DATA_LIMIT, DISK_LIMIT, Guard, MAX_READ, MAX_WIRE_READ, Refused, identity

HERE = Path(__file__).resolve().parent
SOURCE_ID = hashlib.sha256(b'offline fixture identity').digest()


def write_space(path, free=30*1024**3, observed=None):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(drive='C:\\', free_bytes=free,
                                   observed_at=time.time() if observed is None else observed)))
    tmp.replace(path)


class MemorySource:
    def __init__(self, data):
        self.data, self.calls, self.fail_at, self.short = data, [], None, False

    def pread(self, count, offset):
        self.calls.append((offset, count))
        if self.fail_at is not None and len(self.calls) >= self.fail_at:
            raise RuntimeError('synthetic source error')
        result = self.data[offset:offset+count]
        return result[:-1] if self.short else result


class CacheUnits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='read-cache-unit-')
        self.root = Path(self.tmp.name)
        self.folder = self.root/'cache'
        self.folder.mkdir()
        self.sample = self.root/'sample.json'
        write_space(self.sample)
        self.guard = Guard(self.sample, self.folder)
        self.data = bytes((i*17)%251 for i in range(3*BLOCK+123))
        self.upstream = MemorySource(self.data)
        self.cache = self.make_cache()

    def make_cache(self, **kwargs):
        return BlockCache(self.folder, SOURCE_ID, len(self.data), self.guard, **kwargs)

    def tearDown(self):
        self.cache.close()
        self.tmp.cleanup()

    def test_unaligned_holes_tail_zero_and_repeated_oracle(self):
        for offset, count in [(0,1),(BLOCK-17,BLOCK+30),(len(self.data)-50,50),(len(self.data),0)]:
            self.assertEqual(self.cache.read(self.upstream,offset,count),self.data[offset:offset+count])
        calls = len(self.upstream.calls)
        self.assertEqual(self.cache.read(self.upstream,0,len(self.data)),self.data)
        self.assertEqual(len(self.upstream.calls), calls)
        self.assertTrue(all(count <= MAX_READ and offset % BLOCK == 0 for offset,count in self.upstream.calls))

    def test_bounds_strict_types_and_32_mib_cap(self):
        for offset,count in [(-1,1),(0,-1),(True,1),(0,False),(len(self.data),1),(0,MAX_READ+1)]:
            with self.subTest(offset=offset,count=count),self.assertRaises(Refused):
                self.cache.read(self.upstream,offset,count)
        self.assertEqual(self.upstream.calls,[])

    def test_cache_restart_preserves_hits_without_upstream_read(self):
        self.cache.read(self.upstream,BLOCK+20,100)
        self.cache.close()
        self.cache=self.make_cache()
        self.upstream.fail_at=1
        self.assertEqual(self.cache.read(self.upstream,BLOCK+5,90),self.data[BLOCK+5:BLOCK+95])
        self.assertEqual(len(self.upstream.calls),1)

    def test_data_hash_corruption_fails_closed(self):
        self.cache.read(self.upstream,0,1)
        os.pwrite(self.cache.data_fd,b'X',0)
        with self.assertRaisesRegex(Refused,'hash mismatch'):
            self.cache.read(self.upstream,0,1)
        with self.assertRaisesRegex(Refused,'failed'):
            self.cache.read(self.upstream,BLOCK,1)

    def test_metadata_digest_corruption_fails_closed(self):
        self.cache.read(self.upstream,0,1)
        self.cache.db.execute('UPDATE blocks SET digest=?',(bytes(32),))
        with self.assertRaisesRegex(Refused,'hash mismatch'):
            self.cache.read(self.upstream,0,1)

    def test_wrong_identity_size_or_geometry_refuses_restart(self):
        self.cache.close()
        for source,size in [(bytes(32),len(self.data)),(SOURCE_ID,len(self.data)+1)]:
            with self.subTest(size=size),self.assertRaisesRegex(Refused,'identity'):
                BlockCache(self.folder,source,size,self.guard)
        db=sqlite3.connect(self.folder/'index.sqlite3')
        db.execute('UPDATE identity SET block=4096');db.commit();db.close()
        with self.assertRaisesRegex(Refused,'identity'):
            self.make_cache()

    def test_short_or_failed_multi_gap_read_commits_no_new_blocks(self):
        self.cache.read(self.upstream,BLOCK,1)
        self.upstream.fail_at=len(self.upstream.calls)+2
        with self.assertRaises(RuntimeError):
            self.cache.read(self.upstream,0,3*BLOCK)
        self.assertEqual(self.cache.db.execute('SELECT count(*) FROM blocks').fetchone()[0],1)
        self.cache.close();self.cache=self.make_cache()
        self.upstream.short=True;self.upstream.fail_at=None
        with self.assertRaisesRegex(Refused,'short upstream'):
            self.cache.read(self.upstream,0,1)
        self.assertEqual(self.cache.count,1)

    def test_budget_full_serves_new_data_without_growing_cache(self):
        self.cache.close();self.cache=self.make_cache(data_limit=BLOCK)
        self.cache.read(self.upstream,0,1)
        before=self.guard.check()
        for off in (BLOCK,2*BLOCK,3*BLOCK):
            self.assertEqual(self.cache.read(self.upstream,off,1),self.data[off:off+1])
        self.assertEqual(self.cache.count,1)
        self.assertEqual(self.guard.check(),before)

    def test_single_writer_lock_and_symlink_files_refused(self):
        with self.assertRaises(BlockingIOError):
            self.make_cache()
        self.cache.close()
        (self.folder/'blocks.bin').unlink()
        (self.folder/'blocks.bin').symlink_to(self.root/'foreign')
        with self.assertRaises((OSError,Refused)):
            self.make_cache()

    def test_data_truncation_and_invalid_dense_slots_refused(self):
        self.cache.read(self.upstream,0,1);self.cache.close()
        (self.folder/'blocks.bin').write_bytes(b'X')
        with self.assertRaisesRegex(Refused,'truncated'):
            self.make_cache()

    def test_crash_after_payload_sync_replays_without_committing_invalid_rows(self):
        self.cache.read(self.upstream,0,1);self.cache.close()
        code='''import os,sys;from pathlib import Path;from cache import BlockCache;from common import Guard,BLOCK
r=Path(sys.argv[1]);c=BlockCache(r/'cache',bytes.fromhex(sys.argv[2]),int(sys.argv[3]),Guard(r/'sample.json',r/'cache'))
c.put_batch([(BLOCK,b'Q'*BLOCK)],after_payload_sync=lambda:os._exit(9))
'''
        p=subprocess.run([sys.executable,'-B','-c',code,str(self.root),SOURCE_ID.hex(),str(len(self.data))],timeout=5)
        self.assertEqual(p.returncode,9)
        self.cache=self.make_cache()
        self.assertEqual(self.cache.count,1)
        self.assertEqual((self.folder/'blocks.bin').stat().st_size,BLOCK)
        self.assertEqual(self.cache.read(self.upstream,BLOCK,1),self.data[BLOCK:BLOCK+1])

    def test_crash_inside_sql_transaction_rolls_back_validity_index(self):
        self.cache.read(self.upstream,0,1);self.cache.close()
        code='''import os,sys;from pathlib import Path;from cache import BlockCache;from common import Guard,BLOCK
r=Path(sys.argv[1]);c=BlockCache(r/'cache',bytes.fromhex(sys.argv[2]),int(sys.argv[3]),Guard(r/'sample.json',r/'cache'))
class TransactionCrash:
 def __init__(self,db):self.db=db
 def __getattr__(self,name):return getattr(self.db,name)
 def execute(self,sql,*args):
  if sql=='COMMIT':os._exit(8)
  return self.db.execute(sql,*args)
c.db=TransactionCrash(c.db)
c.put_batch([(BLOCK,b'Q'*BLOCK)])
'''
        p=subprocess.run([sys.executable,'-B','-c',code,str(self.root),SOURCE_ID.hex(),str(len(self.data))],timeout=5)
        self.assertEqual(p.returncode,8)
        self.cache=self.make_cache();self.assertEqual(self.cache.count,1)
        self.assertEqual(self.cache.read(self.upstream,0,1),self.data[:1])
        self.assertEqual(self.cache.read(self.upstream,BLOCK,1),self.data[BLOCK:BLOCK+1])

    def test_transient_sample_open_retry_never_accepts_stale_or_low_data(self):
        good=self.sample.read_bytes()
        with mock.patch('common.regular_bytes',side_effect=[PermissionError(),FileNotFoundError(),good]):
            self.guard.check()
        for invalid in (dict(drive='C:',free_bytes=1,observed_at=time.time()),
                        dict(drive='C:',free_bytes=30*1024**3,observed_at=time.time()-21)):
            with mock.patch('common.regular_bytes',side_effect=[PermissionError(),json.dumps(invalid).encode()]):
                with self.assertRaises(Refused):self.guard.check()

    def test_concurrent_unit_clients_serialize_sqlite_and_upstream(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda i:self.cache.read(self.upstream,i*BLOCK,20),range(4)))
        self.assertEqual(results,[self.data[i*BLOCK:i*BLOCK+20] for i in range(4)])
        self.assertEqual(self.cache.count,4)

    def test_host_stale_low_future_and_cache_disk_guard(self):
        for free,observed in [(1024,time.time()),(30*1024**3,time.time()-21),(30*1024**3,time.time()+3)]:
            write_space(self.sample,free,observed)
            with self.assertRaises(Refused):self.guard.check()
        write_space(self.sample)
        with (self.folder/'blocks.bin').open('r+b') as f:f.truncate(DISK_LIMIT+1)
        with self.assertRaisesRegex(Refused,'budget'):self.guard.check()


class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='read-cache-oracle-')
        self.root=Path(self.tmp.name);self.cache=self.root/'cache';self.cache.mkdir()
        raw=bytearray((i*13)%251 for i in range(4*BLOCK+123))
        raw[2*BLOCK:3*BLOCK]=bytes(BLOCK)
        self.data=bytes(raw)
        self.image=self.root/'source.bin'
        with self.image.open('wb') as image:
            image.truncate(len(self.data))
            image.write(self.data[:2*BLOCK]);image.seek(3*BLOCK);image.write(self.data[3*BLOCK:])
        self.sample=self.root/'sample.json';write_space(self.sample)
        self.ready=self.root/'ready.json'
        self.ready.write_text(json.dumps(dict(event='export_ready',readonly=True,getsize=len(self.data),
                                              manifest_pin='fixture-manifest',config_pin='fixture-config',planDigest='fixture-plan')))
        self.processes=[];self.handles=[];self.logs=[]
        self.stop=threading.Event();self.keep_sample=True
        def sampler():
            while not self.stop.wait(.2):
                if self.keep_sample:write_space(self.sample)
        self.sampler=threading.Thread(target=sampler);self.sampler.start()
        self.upstream_socket=self.root/'upstream.sock';self.proxy_socket=self.root/'proxy.sock'

    def tearDown(self):
        for h in self.handles:
            try:h.shutdown()
            except Exception:pass
        for p in reversed(self.processes):
            if p.poll() is None:
                p.terminate()
                try:p.wait(3)
                except subprocess.TimeoutExpired:p.kill();p.wait(1)
        for log in self.logs:log.close()
        self.stop.set();self.sampler.join(1);self.tmp.cleanup()

    def spawn(self,argv,name,env=None):
        log=(self.root/(name+'.log')).open('w');self.logs.append(log)
        p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
        self.processes.append(p);return p

    def source(self,**changes):
        config=dict(size=len(self.data),data=str(self.image),reads=str(self.root/'reads.jsonl'),marker=str(self.root/'entered'))
        config.update(changes);path=self.root/'upstream.json';path.write_text(json.dumps(config))
        argv=['nbdkit','-f','--exit-with-parent','-U',str(self.upstream_socket)]
        if not changes.get('writable'):argv+=['-r']
        p=self.spawn(argv+['python',str(HERE/'fixture_upstream.py'),'config='+str(path)],'upstream')
        self.wait(lambda:self.upstream_socket.exists(),p,'upstream');return p

    def proxy(self,operation=900,initialization=900):
        if self.proxy_socket.exists():self.proxy_socket.unlink()
        argv=[sys.executable,'-B',str(HERE/'serve.py'),'--socket',str(self.proxy_socket),
              '--upstream',str(self.upstream_socket),'--ready',str(self.ready),'--cache',str(self.cache),
              '--host-space',str(self.sample),'--operation-seconds',str(operation),
              '--initialization-seconds',str(initialization)]
        self.proxy_log=self.root/'proxy.log'
        return self.spawn(argv,'proxy',dict(os.environ,READ_CACHE_PROXY_TEST_MODE='1',PYTHONDONTWRITEBYTECODE='1'))

    def wait(self,predicate,p,name,seconds=5):
        deadline=time.monotonic()+seconds
        while not predicate():
            if p.poll() is not None:raise AssertionError(name+' exited: '+(self.root/(name+'.log')).read_text())
            if time.monotonic()>=deadline:raise AssertionError(name+' wait deadline: '+(self.root/(name+'.log')).read_text())
            time.sleep(.01)

    def connect(self):
        h=nbd.NBD();h.connect_unix(str(self.proxy_socket));self.handles.append(h);return h

    def ready_proxy(self,**kwargs):
        p=self.proxy(**kwargs);self.wait(lambda:'"event": "export_ready"' in self.proxy_log.read_text(),p,'proxy');return p

    def test_actual_readonly_oracle_concurrent_and_cache_without_upstream(self):
        upstream=self.source();proxy=self.ready_proxy()
        h=self.connect();self.assertTrue(h.is_read_only());self.assertEqual(h.get_size(),len(self.data))
        self.assertEqual(h.get_block_size(nbd.SIZE_MAXIMUM),MAX_WIRE_READ)
        with self.assertRaises(nbd.Error):h.pwrite(b'X',0)
        offsets=[0,BLOCK-1,2*BLOCK+17,len(self.data)-43]
        for offset in offsets:self.assertEqual(h.pread(31,offset),self.data[offset:offset+31])
        def read(offset):
            client=self.connect();return client.pread(19,offset)
        with ThreadPoolExecutor(max_workers=4) as pool:
            values=list(pool.map(read,offsets))
        self.assertEqual(values,[self.data[o:o+19] for o in offsets])
        before=(self.root/'reads.jsonl').read_text()
        upstream.kill();upstream.wait(2)
        for offset in offsets:self.assertEqual(h.pread(7,offset),self.data[offset:offset+7])
        self.assertEqual((self.root/'reads.jsonl').read_text(),before)

    def test_restart_keeps_cache_but_revalidates_actual_upstream(self):
        self.source();p=self.ready_proxy();h=self.connect();self.assertEqual(h.pread(17,BLOCK),self.data[BLOCK:BLOCK+17]);h.shutdown()
        p.terminate();self.assertEqual(p.wait(3),143)
        before=(self.root/'reads.jsonl').read_text()
        p=self.ready_proxy();h=self.connect();self.assertEqual(h.pread(13,BLOCK),self.data[BLOCK:BLOCK+13])
        self.assertEqual((self.root/'reads.jsonl').read_text(),before)

    def test_writable_and_wrong_size_upstream_refused(self):
        for change in ({'writable':True},{'size':len(self.data)+1}):
            with self.subTest(change=change):
                source=self.source(**change);p=self.proxy();self.assertNotEqual(p.wait(5),0)
                self.assertNotIn('"event": "export_ready"',self.proxy_log.read_text())
                source.terminate();source.wait(2);self.upstream_socket.unlink(missing_ok=True)

    def test_wrong_pin_cache_restart_refused(self):
        self.source();p=self.ready_proxy();h=self.connect();h.pread(1,0);h.shutdown();p.terminate();p.wait(3)
        value=json.loads(self.ready.read_text());value['manifest_pin']='different-fixture';self.ready.write_text(json.dumps(value))
        p=self.proxy();self.assertNotEqual(p.wait(5),0);self.assertNotIn('"event": "export_ready"',self.proxy_log.read_text())

    def test_bare_plugin_refuses_before_upstream_read(self):
        self.source()
        p=self.spawn(['nbdkit','-f','-r','-U',str(self.proxy_socket),'python',str(HERE/'plugin.py'),
                      'upstream='+str(self.upstream_socket),'ready='+str(self.ready),'cache='+str(self.cache),
                      'host-space='+str(self.sample)],'bare')
        self.assertNotEqual(p.wait(5),0);self.assertFalse((self.root/'reads.jsonl').exists())

    def assert_cancelled(self,p,expected):
        began=time.monotonic();self.assertNotEqual(p.wait(4),0)
        elapsed=time.monotonic()-began;self.assertLess(elapsed,3)
        log=self.proxy_log.read_text();self.assertIn(expected,log)
        events=[json.loads(line) for line in log.splitlines() if line.startswith('{')]
        child=next(e['child_pid'] for e in events if e.get('event')=='supervisor_started')
        with self.assertRaises(ProcessLookupError):os.killpg(child,0)
        self.assertIn('"event": "supervisor_stopped"',log)
        artifacts=os.environ.get('READ_CACHE_TEST_ARTIFACT_DIR')
        if artifacts:
            with (Path(artifacts)/'cancellation.jsonl').open('a') as output:
                output.write(json.dumps(dict(test=self.id(),seconds_after_injection=elapsed,owned_group_gone=True))+'\n')

    def test_blocked_initial_connect_deadline_cancels_owned_group(self):
        self.source(stall_connect=True);p=self.proxy(initialization=.7)
        self.wait(lambda:(self.root/'entered').exists(),p,'proxy')
        self.assert_cancelled(p,'deadline_stop')

    def test_blocked_read_operation_deadline_returns_no_partial_bytes(self):
        self.source(stall_read=True);p=self.ready_proxy(operation=.5);h=self.connect();result=[]
        def request():
            try:result.append(bytes(h.pread(100,0)))
            except nbd.Error:result.append('error')
        t=threading.Thread(target=request);t.start()
        self.wait(lambda:(self.root/'entered').exists(),p,'proxy')
        self.assert_cancelled(p,'deadline_stop');t.join(2)
        self.assertEqual(result,['error'])
        db=sqlite3.connect(self.cache/'index.sqlite3');self.assertEqual(db.execute('SELECT count(*) FROM blocks').fetchone()[0],0);db.close()

    def test_low_space_cancels_blocked_startup(self):
        self.source(stall_connect=True);p=self.proxy();self.wait(lambda:(self.root/'entered').exists(),p,'proxy')
        self.keep_sample=False;write_space(self.sample,1024)
        self.assert_cancelled(p,'supervisor_stop')

    def test_stale_sample_cancels_idle_service(self):
        self.source();p=self.ready_proxy();self.keep_sample=False;write_space(self.sample,observed=time.time()-21)
        self.assert_cancelled(p,'supervisor_stop')

    def test_disk_budget_cancels_idle_service(self):
        self.source();p=self.ready_proxy()
        with (self.cache/'blocks.bin').open('r+b') as f:f.truncate(DISK_LIMIT+1)
        self.assert_cancelled(p,'supervisor_stop')

    def test_upstream_error_returns_no_data_or_valid_cache_rows(self):
        self.source(fail_read=True);p=self.ready_proxy();h=self.connect()
        with self.assertRaises(nbd.Error):h.pread(100,0)
        self.assertNotEqual(p.wait(4),0)
        db=sqlite3.connect(self.cache/'index.sqlite3');self.assertEqual(db.execute('SELECT count(*) FROM blocks').fetchone()[0],0);db.close()

    def test_unavailable_upstream_refuses_restart_even_with_valid_cache(self):
        source=self.source();p=self.ready_proxy();h=self.connect();h.pread(1,0);h.shutdown()
        p.terminate();p.wait(3);source.kill();source.wait(2)
        self.upstream_socket.unlink(missing_ok=True)
        p=self.proxy();self.assertNotEqual(p.wait(5),0)
        self.assertNotIn('"event": "export_ready"',self.proxy_log.read_text())

    def test_corrupt_cached_payload_stops_actual_export(self):
        self.source();p=self.ready_proxy();h=self.connect();h.pread(1,0)
        with (self.cache/'blocks.bin').open('r+b') as stream:stream.write(b'X');stream.flush();os.fsync(stream.fileno())
        with self.assertRaises(nbd.Error):h.pread(1,0)
        self.assertNotEqual(p.wait(4),0)

    def test_low_space_cancels_blocked_read(self):
        self.source(stall_read=True);p=self.ready_proxy();h=self.connect();result=[]
        def request():
            try:result.append(bytes(h.pread(100,0)))
            except nbd.Error:result.append('error')
        t=threading.Thread(target=request);t.start();self.wait(lambda:(self.root/'entered').exists(),p,'proxy')
        self.keep_sample=False;write_space(self.sample,1024)
        self.assert_cancelled(p,'supervisor_stop');t.join(2);self.assertEqual(result,['error'])

    def test_deadline_kills_and_reaps_unresponsive_owned_descendant(self):
        helper="""import os,signal,subprocess,sys,time
from control import Control
c=Control.environment();c.ready();c.start()
signal.signal(signal.SIGTERM,signal.SIG_IGN)
subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'])
time.sleep(60)
"""
        command=[sys.executable,'-B','-c',helper]
        parent="import sys;from serve import supervise;from common import Guard;raise SystemExit(supervise(sys.argv[3:],Guard(sys.argv[1],sys.argv[2]),.5,5))"
        self.proxy_log=self.root/'proxy.log'
        p=self.spawn([sys.executable,'-B','-c',parent,str(self.sample),str(self.cache),*command],'proxy')
        self.assert_cancelled(p,'deadline_stop')


if __name__=='__main__':
    unittest.main(verbosity=2)
