# Security design and limits

Every inbound production connection performs a TLS 1.3 handshake before any
Beamer-derived framing or input is accepted. Both outgoing senders use the same
mandatory transport. Authentication uses a randomly generated 32-byte external
PSK. It is represented as exactly 64 lowercase hexadecimal characters; short
codes and arbitrary passwords are rejected. Standard Python/OpenSSL TLS-PSK is
used rather than a custom pairing proof. `CERT_NONE` on the TLS client selects
PSK authentication; there is no anonymous/certificate/plaintext fallback.

TLS is restricted to version 1.3. Contexts are fresh per connection, session
tickets are disabled and no early data is used. Recorded ciphertext from a
previous connection fails under the fresh TLS handshake. The inherited inner
ChaCha20-Poly1305 framing is still present, **and is not independently replay
safe**. It must never be exposed outside this transport.

The TLS I/O adapter serializes OpenSSL calls while allowing concurrent input
and heartbeat threads to wait for socket readiness outside its lock. Pending
receiver handshakes retain the upstream limit of four, with a five-second TLS
timeout followed by a separate five-second application handshake deadline.
Unauthenticated clients can still create denial-of-service pressure on a LAN.

No UDP discovery or six-digit pairing service runs in this version. The key is
generated locally and transferred manually. Each computer stores it in its own
user configuration file (macOS file mode 0600). It is not protected by Windows
DPAPI or macOS Keychain yet; another process running as that user may read it.
Clipboard history/cloud sync can retain keys copied with the Copy button.
Compromised endpoints or a stolen key are not defended by TLS.

Windows runs as the signed-in user. No firewall repair, network-category change,
GameInput service restart or lock-screen provider signal is performed. Input
hooks/Accessibility permission and clipboard access are still powerful and
necessary for the requested functionality. Public-network reachability is
controlled by the operating-system firewall, not inferred by the application.

This is a focused remediation and prototype, not a full audit of the inherited
input parser, native hooks, dependencies or binaries. Do not describe it as
certified safe. The original Beamer installation is separate and unchanged.

References:
- https://docs.python.org/3.13/library/ssl.html#ssl.SSLContext.set_psk_client_callback
- https://docs.python.org/3.13/library/ssl.html#ssl.SSLContext.set_psk_server_callback
- https://github.com/kalkman-code/beamer/tree/387aeff00f52a9eea65d8ba734a814e511f5019e
