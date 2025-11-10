"""
Seed de usuarios iniciales del sistema
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.autenticacion.models import User, UserRole, UserStatus
from app.domains.autenticacion.security import PasswordSecurity


def seed_superadmin(session: Session) -> None:
    """
    Crea el usuario superadmin inicial

    Credenciales:
    - Email: admin@admin.com
    - Contraseña: admin
    - Rol: SUPERADMIN
    """
    print("\n🔐 Creando usuario SUPERADMIN...")

    # Verificar si ya existe
    existing_admin = session.query(User).filter(User.email == "admin@admin.com").first()

    if existing_admin:
        print("  ⚠️  Usuario admin@admin.com ya existe, omitiendo...")
        return

    # Crear superadmin
    # Nota: La contraseña "admin" no cumple requisitos de seguridad en producción
    # pero es útil para desarrollo/testing
    hashed_password = PasswordSecurity.get_password_hash("admin")

    superadmin = User(
        email="admin@admin.com",
        hashed_password=hashed_password,
        nombre="Admin",
        apellido="Sistema",
        role=UserRole.SUPERADMIN,
        status=UserStatus.ACTIVE,
        is_email_verified=True,  # Ya verificado para evitar paso extra
        created_at=datetime.now(timezone.utc),
    )

    session.add(superadmin)
    session.commit()

    print("  ✅ Superadmin creado exitosamente")
    print(f"     Email: admin@admin.com")
    print(f"     Contraseña: admin")
    print(f"     Rol: {UserRole.SUPERADMIN}")
    print(f"     Estado: {UserStatus.ACTIVE}")
