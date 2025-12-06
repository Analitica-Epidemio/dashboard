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

    hashed_password = PasswordSecurity.obtener_hash_contrasena("admin")

    if existing_admin:
        print("  ⚠️  Usuario admin@admin.com ya existe, actualizando...")
        existing_admin.contrasena_hasheada = hashed_password
        existing_admin.rol = UserRole.SUPERADMIN
        existing_admin.estado = UserStatus.ACTIVE
        existing_admin.es_email_verificado = True
        session.commit()
        print("  ✅ Superadmin actualizado exitosamente")
        return

    # Crear superadmin
    superadmin = User(
        email="admin@admin.com",
        contrasena_hasheada=hashed_password,
        nombre="Admin",
        apellido="Sistema",
        rol=UserRole.SUPERADMIN,
        estado=UserStatus.ACTIVE,
        es_email_verificado=True,
        created_at=datetime.now(timezone.utc),
    )

    session.add(superadmin)
    session.commit()

    print("  ✅ Superadmin creado exitosamente")
    print("     Email: admin@admin.com")
    print("     Contraseña: admin")
    print(f"     Rol: {UserRole.SUPERADMIN}")
    print(f"     Estado: {UserStatus.ACTIVE}")
