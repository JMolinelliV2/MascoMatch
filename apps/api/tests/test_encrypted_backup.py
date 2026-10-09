import base64
from io import BytesIO
from pathlib import Path
import tarfile
import pytest
from pydantic import SecretStr
from app.core.config import settings
from app.ops.backup import EncryptWriter,decrypt,verified_archive,safe_name


def test_backup_cipher_checks_integrity_and_key(tmp_path):
    secret=b"x"*32
    encrypted=tmp_path/"sample.mbak"
    with encrypted.open("wb") as stream:
        writer=EncryptWriter(stream,secret)
        writer.write(b"private-example-evidence")
        writer.finish()
    assert b"private-example-evidence" not in encrypted.read_bytes()
    output=tmp_path/"clear"
    decrypt(encrypted,output,secret)
    assert output.read_bytes()==b"private-example-evidence"
    with pytest.raises(ValueError,match="integrity"):
        decrypt(encrypted,tmp_path/"wrong",b"y"*32)
    data=bytearray(encrypted.read_bytes());data[-17]^=1;encrypted.write_bytes(data)
    with pytest.raises(ValueError,match="integrity"):
        decrypt(encrypted,tmp_path/"tampered",secret)


@pytest.mark.parametrize("name",["../escape","/absolute","photos/../../escape",r"photos\escape"])
def test_unsafe_archive_paths_are_rejected(name):
    assert not safe_name(name)


def test_authenticated_archive_still_rejects_path_traversal(tmp_path,monkeypatch):
    secret=b"x"*32
    monkeypatch.setattr(settings,"backup_key",SecretStr(base64.urlsafe_b64encode(secret).decode()))
    encrypted=tmp_path/"unsafe.mbak"
    with encrypted.open("wb") as output:
        writer=EncryptWriter(output,secret)
        with tarfile.open(fileobj=writer,mode="w|") as archive:
            info=tarfile.TarInfo("../escape");info.size=1
            archive.addfile(info,BytesIO(b"x"))
        writer.finish()
    with pytest.raises(ValueError,match="Unsafe"):
        verified_archive(encrypted,tmp_path)
