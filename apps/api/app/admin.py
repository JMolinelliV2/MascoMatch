"""Local operator command; no public route can assign administrator permissions."""
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import User


def main():
    address=input("Correo de una cuenta registrada que administrará MascoMatch: ").strip().lower()
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==address,User.status=="ACTIVE"))
        if user is None:raise SystemExit("No existe una cuenta activa con ese correo.")
        user.role="ADMIN";db.commit()
    print("Permiso de administrador asignado. Volvé a ingresar en la web.")


if __name__=="__main__":main()
