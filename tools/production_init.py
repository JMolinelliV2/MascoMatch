"""Generate private deployment files. Never overwrite an existing installation."""
import argparse
import base64
import os
from pathlib import Path
import re
import secrets
import json
from urllib.parse import quote


def initialize(root: Path, domain="mascomatch.com"):
    root = root.resolve()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain) or "." not in domain:
        raise ValueError("Use a domain name without protocol, path or port")
    directory = root / ".secrets"
    configuration = root / ".env.production"
    if directory.exists() or configuration.exists():
        raise FileExistsError("Private production files already exist; refusing to replace keys")
    root.mkdir(parents=True, exist_ok=True)
    directory.mkdir(mode=0o700)
    owner_password, app_password, redis_password = [secrets.token_urlsafe(32) for _ in range(3)]
    data = {
        "db_owner_password": owner_password,
        "app_db_password": app_password,
        "database_url": f"postgresql+psycopg://mascomatch_app:{quote(app_password)}@db:5432/mascomatch",
        "migrator_database_url": f"postgresql+psycopg://mascomatch_owner:{quote(owner_password)}@db:5432/mascomatch",
        "jwt_secret": secrets.token_urlsafe(48),
        "redis_password": redis_password,
        "redis_url": f"redis://:{quote(redis_password)}@redis:6379/0",
        "redis_config": f"bind 0.0.0.0\nprotected-mode yes\nrequirepass {redis_password}\nappendonly yes\nmaxmemory 256mb\nmaxmemory-policy noeviction\n",
        "photos_admin_secret": secrets.token_urlsafe(32),
        "s3_secret_key": secrets.token_urlsafe(32),
        "vision_s3_secret": secrets.token_urlsafe(32),
        "smtp_password": "",
        "metrics_token": secrets.token_urlsafe(48),
        "backup_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    }
    data["photos_config"] = json.dumps({"identities":[
        {"name":"operator","credentials":[{"accessKey":"mascomatch_admin","secretKey":data["photos_admin_secret"]}],"actions":["Admin","Read","Write","List"]},
        {"name":"application","credentials":[{"accessKey":"mascomatch_app","secretKey":data["s3_secret_key"]}],"actions":["Read:pet-photos","Write:pet-photos","List:pet-photos"]},
        {"name":"vision","credentials":[{"accessKey":"mascomatch_vision","secretKey":data["vision_s3_secret"]}],"actions":["Read:pet-photos","List:pet-photos"]}
    ]})
    for name, value in data.items():
        with open(directory / name, "x", encoding="utf-8", newline="\n", opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
            stream.write(value + "\n")
        # Docker mounts individual files into non-root services. The host parent
        # stays private (0700); no container receives that directory as a mount.
        (directory / name).chmod(0o444)
    public = f"""# Private keys live in .secrets/, not in this file.
SITE_DOMAIN={domain}
WEB_ORIGIN=https://{domain}
PUBLIC_SITE_URL=https://{domain}
ALLOWED_HOSTS={domain},localhost,127.0.0.1,api
AI_ENABLED=false
EMBEDDINGS_ENABLED=false
MAIL_DELIVERY_MODE=disabled
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_FROM=MascoMatch <avisos@{domain}>
SMTP_TLS_MODE=starttls
NEXT_PUBLIC_SEARCH_COUNTRY=UY
BACKUP_INTERVAL_SECONDS=86400
"""
    with open(configuration, "x", encoding="utf-8", newline="\n", opener=lambda path, flags: os.open(path, flags, 0o600)) as stream:
        stream.write(public)
    return configuration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path.cwd())
    parser.add_argument("--domain", default="mascomatch.com")
    args = parser.parse_args()
    print("Created private deployment files:", initialize(args.directory, args.domain))
    print("Store backup_key separately from the server; losing it makes backups unrecoverable.")
