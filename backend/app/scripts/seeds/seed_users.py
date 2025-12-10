"""
Seed de usuarios iniciales del sistema.

IMPORTANTE: El superadmin de desarrollo (admin/admin) solo se crea
si el usuario confirma explícitamente. Esto evita crear credenciales
inseguras en producción por accidente.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domains.autenticacion.models import User, UserRole, UserStatus
from app.domains.autenticacion.security import PasswordSecurity


def seed_superadmin(session: Session, force: bool = False) -> None:
    """
    Crea el usuario superadmin de desarrollo.

    Args:
        session: Sesión de base de datos
        force: Si True, no pregunta confirmación (para scripts automatizados)

    Credenciales:
    - Email: admin@admin.com
    - Contraseña: admin
    - Rol: SUPERADMIN

    ADVERTENCIA: Solo usar en desarrollo local.
    En producción usar: make superadmin
    """
    # Verificar si ya existe
    existing_admin = session.query(User).filter(User.email == "admin@admin.com").first()

    if existing_admin:
        print("  ⚠️  Superadmin de desarrollo ya existe (admin@admin.com)")
        return

    # Preguntar confirmación si no es forzado
    if not force:
        print("\n⚠️  ADVERTENCIA: Esto creará un superadmin con credenciales inseguras:")
        print("   Email: admin@admin.com")
        print("   Password: admin")
        print("\n   Solo usar en desarrollo local. En producción usar: make superadmin")

        try:
            respuesta = (
                input("\n¿Crear superadmin de desarrollo? [y/N]: ").strip().lower()
            )
            if respuesta not in ["y", "yes", "si", "sí"]:
                print("  ⏭️  Omitido. Usar 'make superadmin' para crear uno seguro.")
                return
        except EOFError:
            # No hay stdin (ej: pipe), omitir
            print("  ⏭️  Omitido (no hay terminal interactiva)")
            return

    print("\n🔐 Creando superadmin de desarrollo...")

    hashed_password = PasswordSecurity.obtener_hash_contrasena("admin")

    superadmin = User(
        email="admin@admin.com",
        contrasena_hasheada=hashed_password,
        nombre="Admin",
        apellido="Dev",
        rol=UserRole.SUPERADMIN,
        estado=UserStatus.ACTIVE,
        es_email_verificado=True,
        created_at=datetime.now(timezone.utc),
    )

    session.add(superadmin)
    session.commit()

    print("  ✅ Superadmin de desarrollo creado")
    print("     Email: admin@admin.com")
    print("     Password: admin")
