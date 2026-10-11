"""Private operator command; reserve one verified account, even before signup."""
import argparse
import re
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import AdminAccess, User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="Cuenta administradora; se puede reservar antes de registrarla")
    args = parser.parse_args()
    address = (args.email or input("Correo de la única cuenta administradora: ")).strip().lower()
    if len(address) > 320 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address):
        raise SystemExit("Indicá un correo válido.")
    with SessionLocal() as db:
        access = db.scalar(select(AdminAccess).where(AdminAccess.id == 1).with_for_update())
        if access is None:
            raise SystemExit("Aplicá las migraciones antes de reservar la administración.")
        user = db.scalar(select(User).where(User.email == address))
        if user and user.status != "ACTIVE":
            raise SystemExit("La cuenta está bloqueada; no se modificó el acceso.")
        enabled = bool(user and user.email_verified)
        access.owner = user if enabled else None
        access.pending_email = None if enabled else address
        if enabled:
            user.role = "ADMIN"
        db.commit()
    print("Acceso exclusivo habilitado. Volvé a ingresar en la web." if enabled else
          "Acceso exclusivo reservado. Creá la cuenta y confirmá su correo para habilitarlo.")


if __name__=="__main__":main()
