"""Mac sender logic against real TLS on Windows; native macOS APIs are faked."""
from pathlib import Path
import contextlib
import socket
import sys
import threading
import time
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'mac_app'),str(ROOT/'mac_app/tests')]
if sys.platform!='darwin':
    sys.modules['objc']=types.SimpleNamespace(autorelease_pool=contextlib.nullcontext)
    sys.modules['Quartz']=types.ModuleType('Quartz')
from test_bridge import FakeQuartz, FakeClipboard, make_config
import bridge
import receiver
import no_unlock
import protocol
import secure_transport


class MacTransportTests(unittest.TestCase):
    def test_mac_sender_tls_and_input_dispatch(self):
        key=secure_transport.new_key()
        cfg=make_config(); cfg.host='127.0.0.1'; cfg.auth_token=key
        listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen()
        self.addCleanup(listener.close); cfg.port=listener.getsockname()[1]
        calls=[]
        spy=types.SimpleNamespace(inject_key=lambda key,down:calls.append((key,down)))
        server=receiver.ReceiverServer(lambda *args:None,injector=spy,unlock=no_unlock)
        stop=threading.Event()
        def serve():
            connection,address=listener.accept()
            server._pending+=1
            server._session_thread(connection,address,cfg,stop)
        thread=threading.Thread(target=serve,daemon=True);thread.start()
        controller=bridge.KVMController(cfg,quartz=FakeQuartz,clipboard=FakeClipboard(),macos_major=26)
        try:
            self.assertTrue(controller._connect_once(),controller.connection_status)
            controller._send_raw({'type':'keydown','data':{'key':'a'}})
            deadline=time.monotonic()+3
            while not calls and time.monotonic()<deadline: time.sleep(.01)
            self.assertEqual(calls,[('a',True)])
        finally:
            stop.set()
            if controller.sock: controller.sock.close()
            thread.join(timeout=3)
        self.assertFalse(thread.is_alive())


if __name__=='__main__': unittest.main(verbosity=2)
