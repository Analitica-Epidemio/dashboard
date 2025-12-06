"""
Authentication service layer
Handles user management, authentication, and session management
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, Request, status
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, UserLogin, UserSession, UserStatus
from .schemas import SessionInfo, Token, UserCreate, UserUpdate
from .schemas import UserLogin as UserLoginSchema
from .security import (
    PasswordSecurity,
    SecurityConfig,
    SecurityTokens,
    SessionSecurity,
    TokenSecurity,
    crear_excepcion_credenciales,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_usuario(self, datos_usuario: UserCreate) -> User:
        """Create a new user with validation"""
        # Check if user already exists
        usuario_existente = await self._obtener_usuario_por_email(datos_usuario.email)
        if usuario_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        es_valida, mensaje_error = PasswordSecurity.validar_fortaleza_contrasena(datos_usuario.contrasena)
        if not es_valida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje_error
            )

        # Create user
        password_hasheada = PasswordSecurity.obtener_hash_contrasena(datos_usuario.contrasena)
        token_verificacion = SecurityTokens.generar_token_verificacion()

        usuario = User(
            email=datos_usuario.email,
            nombre=datos_usuario.nombre,
            apellido=datos_usuario.apellido,
            contrasena_hasheada=password_hasheada,
            rol=datos_usuario.rol,
            token_verificacion_email=token_verificacion,
            estado=UserStatus.ACTIVE,  # Auto-activate for now
            es_email_verificado=False
        )

        self.db.add(usuario)
        await self.db.commit()
        await self.db.refresh(usuario)

        logger.info(f"Created new user: {usuario.email}")
        return usuario

    async def autenticar_usuario(
        self,
        credenciales: UserLoginSchema,
        request: Request
    ) -> Tuple[User, Token]:
        """Authenticate user and create session - simplified and fixed"""
        # Get user with all needed data in single query
        usuario = await self._obtener_usuario_por_email(credenciales.email)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Extract ALL needed values BEFORE any database operations
        user_id = usuario.id
        user_email = usuario.email
        user_nombre = usuario.nombre
        user_apellido = usuario.apellido
        user_role = usuario.rol
        user_status = usuario.estado
        user_locked_until = usuario.bloqueado_hasta
        user_hashed_password = usuario.contrasena_hasheada

        # Check if user is locked
        if user_locked_until and user_locked_until > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked"
            )

        # Check user status
        if user_status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user_status.value}"
            )

        # Verify password
        if not PasswordSecurity.verificar_contrasena(credenciales.contrasena, user_hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Update user for successful login
        usuario.intentos_login = 0
        usuario.bloqueado_hasta = None
        usuario.ultimo_login = datetime.now(timezone.utc)

        # Commit and refresh in single transaction
        await self.db.commit()
        await self.db.refresh(usuario)

        # Create session
        ip_cliente = self._obtener_ip_cliente(request)
        user_agent = request.headers.get("user-agent", "")
        sesion = await self._crear_sesion_usuario(
            user_id, ip_cliente, user_agent, credenciales.recordarme
        )

        # Create tokens using extracted values
        token = self._crear_tokens_con_datos(
            user_id, user_email, user_nombre, user_apellido, user_role, sesion
        )

        logger.info(f"User {user_email} authenticated successfully")
        return usuario, token

    async def refrescar_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        datos_token = TokenSecurity.verificar_token(refresh_token, "refresh")
        if not datos_token or not datos_token.id_sesion:
            raise crear_excepcion_credenciales("Invalid refresh token")

        # Get session
        sesion = await self._obtener_sesion(datos_token.id_sesion)
        if not sesion or not sesion.es_activa:
            raise crear_excepcion_credenciales("Session expired or invalid")

        # Get user
        usuario = await self._obtener_usuario_por_id(sesion.user_id)
        if not usuario or usuario.estado != UserStatus.ACTIVE:
            raise crear_excepcion_credenciales("User not found or inactive")

        # Update session activity
        sesion.ultima_actividad = datetime.now(timezone.utc)
        await self.db.commit()

        # Create new tokens
        return self._crear_tokens(usuario, sesion)

    async def cerrar_sesion_usuario(self, session_id: int) -> None:
        """Logout user by deactivating session"""
        sesion = await self._obtener_sesion(session_id)
        if sesion:
            sesion.es_activa = False
            await self.db.commit()
            logger.info(f"User session {session_id} logged out")

    async def cerrar_sesion_especifica(self, user_id: int, session_id: int) -> bool:
        """
        Logout a specific session owned by the user
        Returns True if session was found and logged out, False otherwise
        """
        sesion = await self._obtener_sesion(session_id)

        # Verificar que la sesión existe y pertenece al usuario
        if not sesion or sesion.user_id != user_id:
            return False

        # Cerrar la sesión
        sesion.es_activa = False
        await self.db.commit()
        logger.info(f"User {user_id} logged out session {session_id}")
        return True

    async def cerrar_todas_sesiones(self, user_id: int) -> None:
        """Logout user from all sessions"""
        await self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(es_activa=False)
        )
        await self.db.commit()
        logger.info(f"All sessions for user {user_id} logged out")

    async def obtener_sesiones_usuario(self, user_id: int, current_session_id: int = None) -> List[SessionInfo]:
        """Get active sessions for user"""
        resultado = await self.db.execute(
            select(UserSession)
            .where(and_(
                UserSession.user_id == user_id,
                UserSession.es_activa.is_(True),
                UserSession.expira_en > datetime.now(timezone.utc)
            ))
            .order_by(UserSession.ultima_actividad.desc())
        )
        sesiones = resultado.scalars().all()

        return [
            SessionInfo(
                id=sesion.id,
                direccion_ip=sesion.direccion_ip,
                agente_usuario=sesion.agente_usuario,
                created_at=sesion.created_at,
                ultima_actividad=sesion.ultima_actividad,
                es_actual=(sesion.id == current_session_id)
            )
            for sesion in sesiones
        ]

    async def actualizar_usuario(self, user_id: int, datos_usuario: UserUpdate) -> User:
        """Update user information"""
        usuario = await self._obtener_usuario_por_id(user_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check for email conflicts
        if datos_usuario.email and datos_usuario.email != usuario.email:
            existente = await self._obtener_usuario_por_email(datos_usuario.email)
            if existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Update fields
        datos_actualizacion = datos_usuario.model_dump(exclude_unset=True)
        for campo, valor in datos_actualizacion.items():
            setattr(usuario, campo, valor)

        usuario.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(usuario)

        logger.info(f"Updated user {usuario.email}")
        return usuario

    async def cambiar_contrasena(self, user_id: int, password_actual: str, nueva_password: str) -> None:
        """Change user password"""
        usuario = await self._obtener_usuario_por_id(user_id)
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not PasswordSecurity.verificar_contrasena(password_actual, usuario.contrasena_hasheada):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password
        es_valida, mensaje_error = PasswordSecurity.validar_fortaleza_contrasena(nueva_password)
        if not es_valida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=mensaje_error
            )

        # Update password
        usuario.contrasena_hasheada = PasswordSecurity.obtener_hash_contrasena(nueva_password)
        usuario.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Logout all other sessions for security
        await self.cerrar_todas_sesiones(user_id)

        logger.info(f"Password changed for user {usuario.email}")

    # Private helper methods

    async def _obtener_usuario_por_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        resultado = await self.db.execute(
            select(User).where(User.email == email)
        )
        return resultado.scalar_one_or_none()

    async def _obtener_usuario_por_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        resultado = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return resultado.scalar_one_or_none()

    async def _obtener_sesion(self, session_id: int) -> Optional[UserSession]:
        """Get session by ID"""
        resultado = await self.db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        return resultado.scalar_one_or_none()

    async def _crear_sesion_usuario(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> UserSession:
        """Create new user session - fixed version without problematic cleanup"""
        # Session duration
        horas = 24 * 7 if remember_me else SecurityConfig.SESSION_EXPIRE_HOURS

        sesion = UserSession(
            user_id=user_id,
            token_sesion=SessionSecurity.generar_token_sesion(),
            direccion_ip=ip_address,
            agente_usuario=user_agent,
            expira_en=SessionSecurity.obtener_expiracion_sesion(horas)
        )

        self.db.add(sesion)
        await self.db.commit()
        await self.db.refresh(sesion)

        return sesion

    async def _limpiar_sesiones_usuario(self, user_id: int) -> None:
        """Clean up old sessions for user"""
        # Deactivate expired sessions
        await self.db.execute(
            update(UserSession)
            .where(and_(
                UserSession.user_id == user_id,
                UserSession.expira_en < datetime.now(timezone.utc)
            ))
            .values(es_activa=False)
        )

        # Keep only the most recent active sessions - use subquery to avoid loading objects
        subquery = select(UserSession.id).where(and_(
            UserSession.user_id == user_id,
            UserSession.es_activa.is_(True)
        )).order_by(UserSession.ultima_actividad.desc()).offset(SecurityConfig.MAX_SESSIONS_PER_USER - 1)

        # Deactivate old sessions using direct UPDATE
        await self.db.execute(
            update(UserSession)
            .where(UserSession.id.in_(subquery))
            .values(es_activa=False)
        )

        await self.db.commit()

    def _crear_tokens(self, usuario: User, sesion: UserSession) -> Token:
        """Create JWT tokens for user session"""
        return self._crear_tokens_con_datos(
            usuario.id, usuario.email, usuario.nombre, usuario.apellido, usuario.rol, sesion
        )

    def _crear_tokens_con_datos(
        self, user_id: int, user_email: str, user_nombre: str, user_apellido: str,
        user_role, sesion: UserSession
    ) -> Token:
        """Create JWT tokens using extracted data (avoids accessing expired user object)"""
        from .schemas import TokenUser

        datos_token = {
            "sub": str(user_id),  # JWT standard requires sub to be a string
            "email": user_email,
            "role": user_role.value,
            "session_id": sesion.id
        }

        access_token = TokenSecurity.crear_token_acceso(datos_token)
        refresh_token = TokenSecurity.crear_token_refresco(datos_token)

        # Include user info in response
        info_usuario = TokenUser(
            id=user_id,
            email=user_email,
            nombre=user_nombre,
            apellido=user_apellido,
            rol=user_role
        )

        return Token(
            token_acceso=access_token,
            token_refresco=refresh_token,
            expira_en=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            usuario=info_usuario
        )

    async def _registrar_intento_login(
        self,
        email: str,
        exito: bool,
        razon_fallo: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> None:
        """Log login attempt for audit purposes"""
        log_login = UserLogin(
            user_id=user_id,
            email_intentado=email,
            exito=exito,
            motivo_fallo=razon_fallo,
            direccion_ip=ip_address,
            agente_usuario=user_agent
        )

        self.db.add(log_login)
        await self.db.commit()

    def _obtener_ip_cliente(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"
