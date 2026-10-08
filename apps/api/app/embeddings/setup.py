"""Explicit installation of public model weights; inference never downloads photos or calls an API."""
from pathlib import Path
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.embeddings.provider import checkpoint_path
from app.models import Photo


def main():
    import open_clip
    import torch
    from app.embeddings.service import schedule_embedding
    target = checkpoint_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    config = open_clip.get_pretrained_cfg(settings.embedding_model, settings.embedding_pretrained)
    source = Path(open_clip.download_pretrained(config, cache_dir=str(target.parent), prefer_hf_hub=False))
    # OpenCLIP verifies the official download checksum. Convert the trusted TorchScript
    # checkpoint once to tensors so regular inference keeps weights_only loading enabled.
    if not target.is_file():
        state = torch.jit.load(str(source), map_location="cpu").state_dict()
    else:
        state = torch.load(target, map_location="cpu", weights_only=True)
    if not target.is_file() or any(key in state for key in ("input_resolution", "context_length", "vocab_size")):
        for key in ("input_resolution", "context_length", "vocab_size"):
            state.pop(key, None)
        temporary = target.with_suffix(".tmp")
        torch.save(state, temporary)
        temporary.replace(target)
    if settings.embeddings_enabled:
        with SessionLocal() as db:
            photos = list(db.scalars(select(Photo)))
            for photo in photos:
                schedule_embedding(db, photo)
            db.commit()
        print(f"Modelo visual instalado; fotos registradas para procesamiento local: {len(photos)}.")
    else:
        print("Modelo visual instalado. Activá EMBEDDINGS_ENABLED para generar vectores.")


if __name__ == "__main__":
    main()
