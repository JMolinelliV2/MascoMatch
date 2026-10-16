"""Generate a private, local SMTP fixture certificate. Never used by the public site."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

directory=Path(sys.argv[1])
key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,"mailpit")])
now=datetime.now(timezone.utc)
cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
      .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
      .not_valid_after(now+timedelta(days=2))
      .add_extension(x509.SubjectAlternativeName([x509.DNSName("mailpit")]),critical=False)
      .add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).sign(key,hashes.SHA256()))
for filename,payload in (("smoke_smtp_cert",cert.public_bytes(serialization.Encoding.PEM)),
        ("smoke_smtp_key",key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))):
    path=directory/filename
    if path.exists():path.chmod(0o600)
    path.write_bytes(payload);path.chmod(0o444)
