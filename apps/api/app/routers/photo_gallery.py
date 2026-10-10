"""Serve enlarged, metadata-free images after the caller validates report access."""
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, Response

from app.core.image_storage import load_display_image
from app.models import Photo


def gallery_photo_response(photo: Photo):
    try:
        payload, mime_type = load_display_image(photo.storage_key, photo.mime_type)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            raise HTTPException(status_code=404, detail="La foto ya no está disponible.") from exc
        raise HTTPException(status_code=503, detail="No pudimos cargar la foto por ahora.") from exc
    except (BotoCoreError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="No pudimos cargar la foto por ahora.") from exc
    return Response(content=payload, media_type=mime_type, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})
