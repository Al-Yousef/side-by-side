"""SideBySide's mandatory TLS 1.3 transport (Python 3.13+ / OpenSSL PSK).

The 256-bit randomly generated pairing key authenticates BOTH endpoints through
TLS-PSK. CERT_NONE here selects PSK authentication, not anonymous TLS. There is
no certificate, plaintext, legacy pairing, early-data or session-ticket fallback.
Never use a password or a short numeric code as the key.
"""
from __future__ import annotations

import re
import secrets
import select
import socket
import ssl
import threading
import time

IDENTITY = "sidebyside-v1"
HANDSHAKE_TIMEOUT = 5.0


class TransportError(OSError):
    pass


def new_key() -> str:
    return secrets.token_hex(32)


def key_bytes(key: str) -> bytes:
    # Canonical lowercase matters: the inner framing also derives from this text.
    if not isinstance(key, str) or re.fullmatch(r"[0-9a-f]{64}", key) is None:
        raise TransportError("Use the 64-character pairing key generated on Windows.")
    return bytes.fromhex(key)


def context(key: str, *, server: bool) -> ssl.SSLContext:
    secret = key_bytes(key)
    if not getattr(ssl, "HAS_PSK", False):
        raise TransportError("SideBySide requires Python 3.13+ with OpenSSL TLS-PSK support.")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.maximum_version = ssl.TLSVersion.TLSv1_3
    ctx.options |= ssl.OP_NO_TICKET
    if server:
        ctx.num_tickets = 0
        ctx.set_psk_server_callback(lambda identity: secret if identity == IDENTITY else b"")
    else:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_psk_client_callback(lambda hint: (IDENTITY, secret))
    return ctx


def prepare_server(raw: socket.socket, key: str) -> ssl.SSLSocket:
    """Caller tracks/owns the returned socket and performs a bounded handshake."""
    return context(key, server=True).wrap_socket(
        raw, server_side=True, do_handshake_on_connect=False, suppress_ragged_eofs=False)


def wrap_client(raw: socket.socket, key: str) -> TLSStream:
    """Take ownership even on failure; never return an unauthenticated stream."""
    wrapped = None
    try:
        raw.settimeout(HANDSHAKE_TIMEOUT)
        wrapped = context(key, server=False).wrap_socket(
            raw, do_handshake_on_connect=False, suppress_ragged_eofs=False)
        wrapped.do_handshake()
        return TLSStream(wrapped)
    except BaseException:
        (wrapped or raw).close()
        raise


class TLSStream:
    """Socket-shaped full-duplex adapter for the inherited threaded application.

All OpenSSL operations on an SSL object are serialized. Network waits happen
outside that lock using a nonblocking socket, so an idle receive never stalls
the other thread's heartbeat, input or clipboard writes. Separate read/write
locks preserve stream ordering. TLS itself is entirely supplied by OpenSSL.
"""
    def __init__(self, sock: ssl.SSLSocket):
        if not isinstance(sock, ssl.SSLSocket) or sock.version() != "TLSv1.3":
            raise TransportError("An authenticated TLS 1.3 handshake is required.")
        self._sock = sock
        self._timeout = sock.gettimeout()
        self._ssl_lock = threading.RLock()
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._closed = False
        sock.setblocking(False)

    def settimeout(self, timeout):
        if timeout is not None and timeout <= 0:
            raise ValueError("SideBySide expects a positive timeout or None")
        self._timeout = timeout

    def gettimeout(self):
        return self._timeout

    def _deadline(self):
        timeout = self._timeout
        return None if timeout is None else time.monotonic() + timeout

    def _wait(self, writing, deadline):
        if self._closed:
            raise OSError("TLS stream closed")
        left = None if deadline is None else deadline - time.monotonic()
        if left is not None and left <= 0:
            raise socket.timeout("TLS I/O deadline exceeded")
        try:
            readable, writable, _ = select.select(
                [] if writing else [self._sock], [self._sock] if writing else [], [], left)
        except ValueError as exc:
            raise OSError("TLS stream closed") from exc
        if not readable and not writable:
            raise socket.timeout("TLS I/O deadline exceeded")

    def recv(self, size):
        deadline = self._deadline()
        with self._read_lock:
            while True:
                try:
                    with self._ssl_lock:
                        if self._closed:
                            raise OSError("TLS stream closed")
                        return self._sock.recv(size)
                except ssl.SSLWantReadError:
                    self._wait(False, deadline)
                except ssl.SSLWantWriteError:
                    self._wait(True, deadline)

    def sendall(self, data):
        deadline = self._deadline()
        with self._write_lock:
            remaining = memoryview(data)
            while remaining:
                try:
                    with self._ssl_lock:
                        if self._closed:
                            raise OSError("TLS stream closed")
                        count = self._sock.send(remaining)
                    if count == 0:
                        raise OSError("TLS stream closed during write")
                    remaining = remaining[count:]
                except ssl.SSLWantReadError:
                    self._wait(False, deadline)
                except ssl.SSLWantWriteError:
                    self._wait(True, deadline)

    def setsockopt(self, *args):
        with self._ssl_lock:
            return self._sock.setsockopt(*args)

    def shutdown(self, how):
        # Emergency Stop must not block waiting for the peer's TLS close_notify.
        with self._ssl_lock:
            if not self._closed:
                self._sock.shutdown(how)

    def close(self):
        with self._ssl_lock:
            if not self._closed:
                self._closed = True
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self._sock.close()

    def fileno(self):
        return self._sock.fileno()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
