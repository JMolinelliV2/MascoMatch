"""Authenticated encrypted backups of one PostgreSQL snapshot and its private photos."""
import argparse
import base64
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import subprocess
import tarfile
import tempfile
import time
from uuid import uuid4

from botocore.exceptions import ClientError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import psycopg
from redis import Redis
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.image_storage import _client

MAGIC = b"MASCOMATCH-BACKUP\x01"
CHUNK = 1024 * 1024
MAX_BYTES = 1024 * 1024 * 1024


def key():
    value = base64.urlsafe_b64decode(settings.backup_key.get_secret_value())
    if len(value) != 32:
        raise ValueError("A separate 32-byte backup key is required")
    return value


class EncryptWriter:
    def __init__(self, stream, secret):
        nonce = secrets.token_bytes(12)
        self.stream, self.count = stream, 0
        self.cipher = Cipher(algorithms.AES(secret), modes.GCM(nonce)).encryptor()
        self.cipher.authenticate_additional_data(MAGIC)
        stream.write(MAGIC + nonce)

    def write(self, payload):
        self.count += len(payload)
        if self.count > MAX_BYTES:
            raise ValueError("Backup exceeds the configured MVP size limit")
        self.stream.write(self.cipher.update(payload))
        return len(payload)

    def finish(self):
        self.stream.write(self.cipher.finalize())
        self.stream.write(self.cipher.tag)


def decrypt(source, destination, secret):
    size = Path(source).stat().st_size
    header_size = len(MAGIC) + 12
    if size > MAX_BYTES + header_size + 16 or size < header_size + 16:
        raise ValueError("Invalid backup size")
    with Path(source).open("rb") as stream:
        if stream.read(len(MAGIC)) != MAGIC:
            raise ValueError("Unsupported backup format")
        nonce = stream.read(12)
        stream.seek(-16, os.SEEK_END)
        tag = stream.read(16)
        stream.seek(header_size)
        cipher = Cipher(algorithms.AES(secret), modes.GCM(nonce, tag)).decryptor()
        cipher.authenticate_additional_data(MAGIC)
        left = size-header_size-16
        try:
            with Path(destination).open("xb") as result:
                while left:
                    payload = stream.read(min(CHUNK, left))
                    if not payload:
                        raise ValueError("Truncated backup")
                    result.write(cipher.update(payload))
                    left -= len(payload)
                result.write(cipher.finalize())
        except InvalidTag as exc:
            raise ValueError("Backup integrity check failed") from exc


def connection_url(value):
    return make_url(value).set(drivername="postgresql").render_as_string(hide_password=False)


def pg_environment(value, directory):
    url = make_url(value)
    def escape(part):
        return str(part).replace("\\", "\\\\").replace(":", "\\:")
    password = Path(directory) / "pgpass"
    password.write_text(":".join(escape(part) for part in (url.host or "localhost", url.port or 5432, url.database, url.username, url.password or ""))+"\n")
    password.chmod(0o600)
    return {**os.environ, "PGHOST":url.host or "localhost", "PGPORT":str(url.port or 5432),
            "PGDATABASE":url.database, "PGUSER":url.username, "PGPASSFILE":str(password)}


def run_pg(arguments, environment):
    result = subprocess.run(arguments, env=environment, capture_output=True)
    if result.returncode:
        # Subprocess details may contain SQL evidence or connection information.
        raise RuntimeError("PostgreSQL backup/restore command failed")


class HashReader:
    def __init__(self, stream):
        self.stream, self.digest = stream, sha256()

    def read(self, size=-1):
        payload = self.stream.read(size)
        self.digest.update(payload)
        return payload


def photo_object(client, storage_key, mime):
    try:
        return client.get_object(Bucket=settings.s3_bucket, Key=storage_key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"NoSuchKey","404"}:
            raise
        # Production keys are immutable UUIDs and deletes retain their versions.
        versions = client.list_object_versions(Bucket=settings.s3_bucket, Prefix=storage_key).get("Versions", [])
        versions = [item for item in versions if item["Key"] == storage_key]
        if not versions:
            raise ValueError("A referenced photo is missing") from exc
        latest = max(versions, key=lambda item:item["LastModified"])
        return client.get_object(Bucket=settings.s3_bucket, Key=storage_key, VersionId=latest["VersionId"])


def safe_name(name):
    path = PurePosixPath(name)
    return not path.is_absolute() and not any(part in {"..", "."} for part in path.parts) and "\\" not in name


def file_hash(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for payload in iter(lambda:stream.read(CHUNK), b""):
            digest.update(payload)
    return digest.hexdigest()


def create_backup(directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    filename = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex + ".mbak"
    target, temporary = directory / filename, directory / (filename + ".partial")
    secret = key()
    client = _client(settings.s3_endpoint)
    manifest = {"format":1, "created_at":datetime.now(timezone.utc).isoformat(), "photos":[]}
    try:
        with tempfile.TemporaryDirectory(prefix="mascomatch-backup-") as workspace:
            dump = Path(workspace) / "database.dump"
            with psycopg.connect(connection_url(settings.database_url)) as db:
                db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                snapshot = db.execute("SELECT pg_export_snapshot()").fetchone()[0]
                rows = db.execute("SELECT storage_key,mime_type FROM photos ORDER BY id").fetchall()
                run_pg(["pg_dump", "--format=custom", "--no-owner", "--no-acl", "--snapshot="+snapshot, "--file="+str(dump)], pg_environment(settings.database_url, workspace))
            manifest["database_sha256"] = file_hash(dump)
            with temporary.open("xb") as stream:
                temporary.chmod(0o600)
                writer = EncryptWriter(stream, secret)
                with tarfile.open(fileobj=writer, mode="w|") as archive:
                    archive.add(dump, arcname="database.dump", recursive=False)
                    for storage_key, mime in rows:
                        name = "photos/" + storage_key
                        if not safe_name(name) or len(manifest["photos"]) >= 20000:
                            raise ValueError("Invalid or excessive photo evidence")
                        photo = photo_object(client, storage_key, mime)
                        try:
                            info = tarfile.TarInfo(name)
                            info.size, info.mode = photo["ContentLength"], 0o600
                            reader = HashReader(photo["Body"])
                            archive.addfile(info, reader)
                            manifest["photos"].append({"key":storage_key, "mime":mime, "sha256":reader.digest.hexdigest()})
                        finally:
                            photo["Body"].close()
                    payload = json.dumps(manifest).encode()
                    info = tarfile.TarInfo("manifest.json")
                    info.size, info.mode = len(payload), 0o600
                    archive.addfile(info, BytesIO(payload))
                writer.finish()
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(target)
        with Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2) as redis:
            redis.set("mascomatch:backup:last_success", str(time.time()))
        return target
    finally:
        temporary.unlink(missing_ok=True)


def verified_archive(source, workspace):
    decrypted = Path(workspace) / "archive.tar"
    decrypt(source, decrypted, key())
    with tarfile.open(decrypted, "r:") as archive:
        members = archive.getmembers()
        names = [item.name for item in members]
        if len(members) > 20002 or len(set(names)) != len(names) or any(not item.isreg() or not safe_name(item.name) for item in members):
            raise ValueError("Unsafe backup archive")
        manifest_member = archive.getmember("manifest.json")
        if manifest_member.size > 10*1024*1024:
            raise ValueError("Excessive manifest")
        manifest = json.loads(archive.extractfile(manifest_member).read())
        expected = {"database.dump":manifest["database_sha256"], **{"photos/"+item["key"]:item["sha256"] for item in manifest["photos"]}}
        if set(names) != {*expected, "manifest.json"}:
            raise ValueError("Manifest does not match backup evidence")
        for name, digest in expected.items():
            stream = archive.extractfile(name)
            hasher = sha256()
            with stream:
                for payload in iter(lambda:stream.read(CHUNK), b""):
                    hasher.update(payload)
            if hasher.hexdigest() != digest:
                raise ValueError("Evidence checksum failed")
    return decrypted, manifest


def restore_backup(source, target_database_url):
    # Authenticate every byte before touching either recovery destination.
    with tempfile.TemporaryDirectory(prefix="mascomatch-restore-") as workspace:
        decrypted, manifest = verified_archive(source, workspace)
        client = _client(settings.s3_endpoint)
        with psycopg.connect(connection_url(target_database_url)) as db:
            existing = db.execute("""SELECT 1 FROM pg_class c JOIN pg_namespace n ON c.relnamespace=n.oid
                WHERE c.relkind IN ('r','p') AND n.nspname NOT IN ('pg_catalog','information_schema')
                AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid=c.oid AND d.classid='pg_class'::regclass AND d.deptype='e') LIMIT 1""").fetchone()
            if existing:
                raise ValueError("Recovery database must contain no application tables")
        if client.list_objects_v2(Bucket=settings.s3_bucket, MaxKeys=1).get("KeyCount", 0):
            raise ValueError("Recovery photo bucket must be empty")
        uploaded = []
        try:
            with tarfile.open(decrypted, "r:") as archive:
                dump = Path(workspace) / "database.dump"
                with archive.extractfile("database.dump") as payload, dump.open("xb") as output:
                    for block in iter(lambda:payload.read(CHUNK), b""):
                        output.write(block)
                for item in manifest["photos"]:
                    with archive.extractfile("photos/"+item["key"]) as payload:
                        client.upload_fileobj(payload, settings.s3_bucket, item["key"], ExtraArgs={"ContentType":item["mime"]})
                    uploaded.append(item["key"])
            run_pg(["pg_restore", "--no-owner", "--no-acl", "--exit-on-error", "--single-transaction", "--dbname="+make_url(target_database_url).database, str(dump)], pg_environment(target_database_url, workspace))
        except Exception:
            for storage_key in uploaded:
                client.delete_object(Bucket=settings.s3_bucket, Key=storage_key)
            raise
    print("Backup restored to empty recovery destinations")


def serve(directory):
    interval = max(3600, int(os.getenv("BACKUP_INTERVAL_SECONDS", "86400")))
    while True:
        try:
            result = create_backup(directory)
            # Keep fourteen completed, owned archives. No recursive directory deletion.
            completed = sorted(Path(directory).glob("????????T??????Z-"+"?"*32+".mbak"))
            for old in completed[:-14]:
                if old.is_file() and not old.is_symlink():
                    old.unlink()
            print("backup_completed", result.name, flush=True)
        except Exception as exc:
            print("backup_failed", type(exc).__name__, flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create","verify","restore","serve"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--target-database-file", type=Path)
    args = parser.parse_args()
    if args.action == "create":
        print("Encrypted backup created:", create_backup(args.path).name)
    elif args.action == "verify":
        with tempfile.TemporaryDirectory() as directory:
            _, manifest = verified_archive(args.path, directory)
            print("Backup authenticated; photo count:", len(manifest["photos"]))
    elif args.action == "restore":
        if not args.target_database_file:
            parser.error("An explicit empty recovery database file is required")
        restore_backup(args.path, args.target_database_file.read_text().strip())
    else:
        serve(args.path)
