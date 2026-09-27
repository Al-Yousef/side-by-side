"""Manual pairing only. No broadcast discovery or six-digit key exchange."""
import socket
from protocol import PAIRING_PORT

class Announcer:
    code = None
    error = None
    def __init__(self, *args, **kwargs): pass
    def start(self): pass
    def stop(self): pass

class Discovery:
    error = None
    def __init__(self, *args, **kwargs): pass
    def start(self): pass
    def stop(self): pass
    def pcs(self): return []

def local_address_towards(address):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((address, 24830))
        return sock.getsockname()[0]

def _local_ipv4_addresses():
    """Keep the sender's self-connection guard working without discovery."""
    found = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = info[4][0]
            if not address.startswith("127.") and address not in found:
                found.append(address)
    except OSError:
        pass
    return found
