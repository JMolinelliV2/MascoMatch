"""Initialize an authenticated S3-compatible store and retain object versions."""
import time
from app.core.config import settings
from app.core.image_storage import _client, _ensure_bucket


def main():
    client=_client(settings.s3_endpoint)
    for attempt in range(30):
        try:
            _ensure_bucket(client)
            client.put_bucket_versioning(Bucket=settings.s3_bucket, VersioningConfiguration={"Status":"Enabled"})
            print("Private photo bucket and object versions ready")
            return
        except Exception:
            if attempt==29:
                raise RuntimeError("Photo storage could not be initialized") from None
            time.sleep(2)


if __name__=="__main__":main()
