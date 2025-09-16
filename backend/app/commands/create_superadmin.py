#!/usr/bin/env python3
"""
Command to create initial superadmin user
Usage: uv run python -m app.commands.create_superadmin
"""
import asyncio
import sys
from getpass import getpass
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine
from app.domains.auth.models import User, UserRole, UserStatus
from app.domains.auth.security import PasswordSecurity, SecurityTokens
from app.domains.auth.service import AuthService
from sqlalchemy import select


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    return PasswordSecurity.validate_password_strength(password)


async def create_superadmin():
    """Create superadmin user interactively"""
    print("🔐 Creación de Super Administrador")
    print("=" * 40)

    async with AsyncSession(engine) as db:
        # Check if any superadmin exists
        result = await db.execute(
            select(User).where(User.role == UserRole.SUPERADMIN)
        )
        existing_superadmin = result.scalar_one_or_none()

        if existing_superadmin:
            print("⚠️  Ya existe un superadmin en el sistema.")
            print(f"   Email: {existing_superadmin.email}")
            print(f"   Nombre: {existing_superadmin.nombre} {existing_superadmin.apellido}")

            confirm = input("¿Desea crear otro superadmin? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes', 'sí', 'si']:
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
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none():
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

            is_valid, error_msg = validate_password(password)
            if not is_valid:
                print(f"❌ {error_msg}")
                continue

            password_confirm = getpass("🔑 Confirmar contraseña: ")
            if password != password_confirm:
                print("❌ Las contraseñas no coinciden.")
                continue
            break

        print("\n📝 Resumen:")
        print(f"   Email: {email}")
        print(f"   Nombre: {nombre}")
        print(f"   Apellido: {apellido}")
        print(f"   Rol: Super Administrador")

        confirm = input("\n¿Crear usuario? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes', 'sí', 'si']:
            print("❌ Operación cancelada.")
            return

        # Create user
        try:
            hashed_password = PasswordSecurity.get_password_hash(password)
            verification_token = SecurityTokens.generate_verification_token()

            user = User(
                email=email,
                nombre=nombre,
                apellido=apellido,
                hashed_password=hashed_password,
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
                email_verification_token=verification_token,
                is_email_verified=True  # Auto-verify for superadmin
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            print(f"\n✅ Super administrador creado exitosamente!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nombre: {user.nombre} {user.apellido}")
            print(f"   Fecha de creación: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\n🎉 Ya puede iniciar sesión en el sistema.")

        except Exception as e:
            print(f"\n❌ Error creando el usuario: {str(e)}")
            sys.exit(1)


async def main():
    """Main entry point"""
    try:
        await create_superadmin()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())