#!/usr/bin/env python3
"""
Command to create initial superadmin user
Usage: uv run python -m app.commands.create_superadmin
"""

import re
import sys
from getpass import getpass

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlmodel import col

from app.core.config import settings
from app.domains.autenticacion.models import User, UserRole, UserStatus
from app.domains.autenticacion.security import PasswordSecurity, SecurityTokens


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    return PasswordSecurity.validar_fortaleza_contrasena(password)


def create_superadmin():
    """Create superadmin user interactively"""
    print("🔐 Gestión de Super Administrador")
    print("=" * 40)

    # Create sync engine and session
    sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

    with SessionLocal() as db:
        # Check for existing users
        result = db.execute(select(User).order_by(User.rol, User.email))
        all_users = result.scalars().all()

        if all_users:
            print(f"⚠️  Ya existen {len(all_users)} usuario(s) en el sistema:")

            superadmins = [u for u in all_users if u.rol == UserRole.SUPERADMIN]
            others = [u for u in all_users if u.rol != UserRole.SUPERADMIN]

            if superadmins:
                print("\n🔐 Superadmins:")
                for i, admin in enumerate(superadmins, 1):
                    print(f"   {i}. {admin.email} ({admin.nombre} {admin.apellido})")

            if others:
                print("\n👤 Otros usuarios:")
                start_idx = len(superadmins) + 1
                for i, user in enumerate(others, start_idx):
                    print(
                        f"   {i}. {user.email} ({user.nombre} {user.apellido}) - {user.rol.value}"
                    )

            print("\n¿Qué desea hacer?")
            print("   1. Crear un nuevo superadmin")
            print("   2. Actualizar contraseña de cualquier usuario")
            print("   3. Salir")

            choice = input("\nSeleccione una opción (1-3): ").strip()

            if choice == "2":
                # Update password
                print("\n📝 Actualizar contraseña")
                print("-" * 20)

                # Select user to update
                while True:
                    user_choice = input(
                        f"\nSeleccione el número del usuario (1-{len(all_users)}): "
                    ).strip()
                    try:
                        idx = int(user_choice) - 1
                        if 0 <= idx < len(all_users):
                            # Combine lists in same order as displayed
                            combined_users = superadmins + others
                            selected_user = combined_users[idx]
                            break
                        else:
                            print("❌ Número inválido")
                    except ValueError:
                        print("❌ Por favor ingrese un número")

                print(f"\n✅ Seleccionado: {selected_user.email}")

                # Get new password (WITHOUT validation)
                while True:
                    password = getpass("🔑 Nueva contraseña: ")
                    if not password:
                        print("❌ La contraseña no puede estar vacía.")
                        continue

                    password_confirm = getpass("🔑 Confirmar contraseña: ")
                    if password != password_confirm:
                        print("❌ Las contraseñas no coinciden.")
                        continue
                    break

                # Update password
                try:
                    selected_user.contrasena_hasheada = (
                        PasswordSecurity.obtener_hash_contrasena(password)
                    )
                    selected_user.bloqueado_hasta = None  # Unlock if locked
                    selected_user.intentos_login = 0  # Reset login attempts

                    db.commit()
                    db.refresh(selected_user)

                    print(
                        f"\n✅ Contraseña actualizada exitosamente para {selected_user.email}!"
                    )
                    print("🎉 Ya puede iniciar sesión con la nueva contraseña.")

                except Exception as e:
                    print(f"\n❌ Error actualizando contraseña: {e!s}")
                    sys.exit(1)

                return

            elif choice == "3" or choice != "1":
                print("❌ Operación cancelada.")
                return
            print()

        # Get user input
        while True:
            email = input("📧 Email: ").strip()
            if not email:
                print("❌ El email es obligatorio.")
                continue

            if not validate_email(email):
                print("❌ Formato de email inválido.")
                continue

            # Check if email already exists
            result = db.execute(select(User).where(col(User.email) == email))
            if result.first():
                print("❌ Este email ya está registrado.")
                continue
            break

        while True:
            nombre = input("👤 Nombre: ").strip()
            if not nombre:
                print("❌ El nombre es obligatorio.")
                continue
            if len(nombre) > 100:
                print("❌ El nombre no puede tener más de 100 caracteres.")
                continue
            break

        while True:
            apellido = input("👤 Apellido: ").strip()
            if not apellido:
                print("❌ El apellido es obligatorio.")
                continue
            if len(apellido) > 100:
                print("❌ El apellido no puede tener más de 100 caracteres.")
                continue
            break

        while True:
            password = getpass("🔑 Contraseña: ")
            if not password:
                print("❌ La contraseña es obligatoria.")
                continue

            # NO validation for superadmin password - allow any password
            password_confirm = getpass("🔑 Confirmar contraseña: ")
            if password != password_confirm:
                print("❌ Las contraseñas no coinciden.")
                continue
            break

        print("\n📝 Resumen:")
        print(f"   Email: {email}")
        print(f"   Nombre: {nombre}")
        print(f"   Apellido: {apellido}")
        print("   Rol: Super Administrador")

        confirm = input("\n¿Crear usuario? (y/N): ").lower().strip()
        if confirm not in ["y", "yes", "sí", "si"]:
            print("❌ Operación cancelada.")
            return

        # Create user
        try:
            hashed_password = PasswordSecurity.obtener_hash_contrasena(password)
            verification_token = SecurityTokens.generar_token_verificacion()

            user = User(
                email=email,
                nombre=nombre,
                apellido=apellido,
                contrasena_hasheada=hashed_password,
                rol=UserRole.SUPERADMIN,
                estado=UserStatus.ACTIVE,
                token_verificacion_email=verification_token,
                es_email_verificado=True,  # Auto-verify for superadmin
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            print("\n✅ Super administrador creado exitosamente!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nombre: {user.nombre} {user.apellido}")
            print(
                f"   Fecha de creación: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print("\n🎉 Ya puede iniciar sesión en el sistema.")

        except Exception as e:
            print(f"\n❌ Error creando el usuario: {e!s}")
            sys.exit(1)


def create_dev_superadmin():
    """
    Crea un superadmin de desarrollo con credenciales admin/admin.
    Solo para uso en desarrollo local.
    """
    print("🔐 Creando superadmin de desarrollo (admin/admin)...")

    sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "")
    sync_engine = create_engine(sync_database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

    with SessionLocal() as db:
        # Verificar si ya existe
        result = db.execute(select(User).where(col(User.email) == "admin@admin.com"))
        if result.first():
            print("⚠️  El superadmin de desarrollo ya existe (admin@admin.com)")
            return

        try:
            hashed_password = PasswordSecurity.obtener_hash_contrasena("admin")
            verification_token = SecurityTokens.generar_token_verificacion()

            user = User(
                email="admin@admin.com",
                nombre="Admin",
                apellido="Dev",
                contrasena_hasheada=hashed_password,
                rol=UserRole.SUPERADMIN,
                estado=UserStatus.ACTIVE,
                token_verificacion_email=verification_token,
                es_email_verificado=True,
            )

            db.add(user)
            db.commit()

            print("✅ Superadmin de desarrollo creado:")
            print("   Email: admin@admin.com")
            print("   Password: admin")

        except Exception as e:
            print(f"❌ Error creando superadmin: {e!s}")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        create_superadmin()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
