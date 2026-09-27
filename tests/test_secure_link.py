"""Real loopback TLS and production-receiver tests. All input/clipboard are fakes."""
from pathlib import Path
import concurrent.futures
import socket
import ssl
import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'win_app'))
sys.path.insert(0, str(ROOT/'win_app/tests'))
import secure_transport as tls
import protocol
import receiver
import no_unlock
from fakes import FakeInjector, FakeClipboard, FakeDesktop
from return_edge import Rect


def wait_until(predicate, seconds=4):
    deadline = time.monotonic()+seconds
    while not predicate():
        if time.monotonic() >= deadline:
            raise AssertionError('Condition timed out')
        time.sleep(.01)


def connected_pair(key):
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0)); listener.listen()
    raw = socket.create_connection(listener.getsockname(), timeout=2)
    peer, _ = listener.accept(); listener.close()
    def server():
        wrapped=tls.prepare_server(peer,key)
        wrapped.settimeout(3); wrapped.do_handshake()
        return tls.TLSStream(wrapped)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future=pool.submit(server)
        client=tls.wrap_client(raw,key)
        return client,future.result(timeout=4)


def captured_tls_client_stream(key, payload):
    """Record real TLS records from an in-memory handshake plus application data."""
    ci, co, si, so = [ssl.MemoryBIO() for _ in range(4)]
    client=tls.context(key,server=False).wrap_bio(ci,co,server_side=False)
    server=tls.context(key,server=True).wrap_bio(si,so,server_side=True)
    transcript=bytearray(); c_done=s_done=False
    for _ in range(20):
        try:
            if not c_done: client.do_handshake(); c_done=True
        except ssl.SSLWantReadError: pass
        flight=co.read(); transcript.extend(flight)
        if flight: si.write(flight)
        try:
            if not s_done: server.do_handshake(); s_done=True
        except ssl.SSLWantReadError: pass
        flight=so.read()
        if flight: ci.write(flight)
        if c_done and s_done: break
    assert c_done and s_done
    client.write(payload)
    application=co.read(); transcript.extend(application); si.write(application)
    assert server.read(len(payload)) == payload
    return bytes(transcript)


class TransportTests(unittest.TestCase):
    def test_generated_key_and_validation(self):
        self.assertEqual(len(tls.key_bytes(tls.new_key())),32)
        self.assertNotEqual(tls.new_key(),tls.new_key())
        for bad in ('', '123456','password', 'f'*63, 'F'*64, None):
            with self.assertRaises(OSError): tls.context(bad,server=False)

    def test_missing_psk_fails_closed(self):
        with patch.object(ssl,'HAS_PSK',False):
            with self.assertRaises(OSError): tls.context(tls.new_key(),server=False)

    def test_requires_tls13_disables_tickets(self):
        ctx=tls.context(tls.new_key(),server=True)
        self.assertEqual(ctx.minimum_version,ssl.TLSVersion.TLSv1_3)
        self.assertEqual(ctx.maximum_version,ssl.TLSVersion.TLSv1_3)
        self.assertEqual(ctx.num_tickets,0)

    def test_full_duplex_stress_and_receive_timeout(self):
        left,right=connected_pair(tls.new_key())
        self.addCleanup(left.close); self.addCleanup(right.close)
        left.settimeout(8); right.settimeout(8)
        a=b'A'*1024*1024; b=b'B'*1024*1024
        def receive(stream, count):
            result=bytearray()
            while len(result)<count: result.extend(stream.recv(min(4096,count-len(result))))
            return bytes(result)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures=[pool.submit(receive,left,len(b)),pool.submit(receive,right,len(a)),
                     pool.submit(left.sendall,a),pool.submit(right.sendall,b)]
            self.assertEqual(futures[0].result(timeout=10),b)
            self.assertEqual(futures[1].result(timeout=10),a)
            for f in futures[2:]: f.result(timeout=10)
        left.settimeout(.05)
        with self.assertRaises(socket.timeout): left.recv(1)

    def test_close_interrupts_receive(self):
        left,right=connected_pair(tls.new_key())
        self.addCleanup(left.close); self.addCleanup(right.close)
        left.settimeout(3)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future=pool.submit(left.recv,1)
            time.sleep(.02); left.close()
            try: self.assertEqual(future.result(timeout=1),b'')
            except OSError: pass

    def test_shared_modules_identical(self):
        for name in ('secure_transport.py','protocol.py','receiver.py','pairing.py'):
            self.assertEqual((ROOT/'mac_app'/name).read_bytes(),(ROOT/'win_app'/name).read_bytes(),name)


class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.key=tls.new_key(); self.status=[]
        self.injector=FakeInjector(); self.clipboard=FakeClipboard()
        self.server=receiver.ReceiverServer(lambda *args:self.status.append(args),
            injector=self.injector,clipboard=self.clipboard,unlock=no_unlock,
            desktop=FakeDesktop([Rect(0,0,1920,1080)]))
        self.stop=threading.Event(); self.threads=[]
        self.config=SimpleNamespace(auth_token=self.key,port=24830)

    def tearDown(self):
        self.stop.set()
        with self.server._lock: connections=list(self.server._connections)
        for conn in connections: self.server._close_socket(conn)
        for thread in self.threads:
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive())
        self.assertEqual(self.server._pending,0)
        self.assertFalse(self.server._connections)

    def raw_connection(self):
        listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen()
        raw=socket.create_connection(listener.getsockname(),timeout=2)
        peer,address=listener.accept(); listener.close()
        with self.server._lock: self.server._pending+=1
        thread=threading.Thread(target=self.server._session_thread,
            args=(peer,address,self.config,self.stop),daemon=True)
        self.threads.append(thread); thread.start()
        return raw

    def connect(self):
        stream=tls.wrap_client(self.raw_connection(),self.key)
        self.addCleanup(stream.close)
        session=protocol.SecureSession(self.key)
        stream.sendall(session.preamble()); protocol.recv_preamble(stream,session)
        protocol.send_msg(stream,session,protocol.hello_msg())
        self.assertEqual(protocol.recv_msg(stream,session),protocol.welcome_msg())
        return stream,session

    def test_good_pair_dispatches_input_and_clipboard(self):
        stream,session=self.connect()
        protocol.send_msg(stream,session,{'type':'keydown','data':{'key':'a'}})
        protocol.send_msg(stream,session,protocol.clipboard_msg('test clipboard',None))
        wait_until(lambda: bool(self.injector.calls) and bool(self.clipboard.set_calls))
        self.assertEqual(self.injector.calls,[('key',('a',True))])
        self.assertEqual(self.clipboard.set_calls,[('test clipboard',None)])

    def test_wrong_key_never_dispatches(self):
        raw=self.raw_connection()
        with self.assertRaises(OSError):
            stream=tls.wrap_client(raw,tls.new_key())
            # TLS 1.3 clients can learn rejection only on the next read.
            try: stream.sendall(b'hello'); stream.recv(1)
            finally: stream.close()
        wait_until(lambda:self.server._pending==0)
        self.assertEqual(self.injector.calls,[])
        self.assertNotIn(receiver.ServerState.CONNECTED,[s for s,_ in self.status])

    def replay(self, data):
        raw=self.raw_connection()
        try:
            raw.sendall(data)
            try:
                while raw.recv(16384): pass
            except (ConnectionError,ssl.SSLError): pass
        finally: raw.close()
        wait_until(lambda:self.server._pending==0)
        self.assertEqual(self.injector.calls,[])
        self.assertNotIn(receiver.ServerState.CONNECTED,[s for s,_ in self.status])

    def test_plaintext_recording_rejected_and_reconnect_works(self):
        session=protocol.SecureSession(self.key)
        recording=session.preamble()+session.seal(protocol.hello_msg())+session.seal(
            {'type':'keydown','data':{'key':'a'}})
        self.replay(recording)
        self.connect()

    def test_recorded_tls_stream_rejected_on_fresh_connection(self):
        session=protocol.SecureSession(self.key)
        payload=session.preamble()+session.seal(protocol.hello_msg())+session.seal(
            {'type':'keydown','data':{'key':'a'}})
        self.replay(captured_tls_client_stream(self.key,payload))
        self.connect()

    def test_stalled_tls_handshake_releases_slot(self):
        with patch.object(receiver,'HELLO_TIMEOUT_SECONDS',.15):
            raw=self.raw_connection()
            try: wait_until(lambda:self.server._pending==0)
            finally: raw.close()
        self.connect()


if __name__=='__main__': unittest.main(verbosity=2)
