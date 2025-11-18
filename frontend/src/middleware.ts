/**
 * Middleware de Next.js para protección de rutas
 *
 * IMPORTANTE: Este middleware solo proporciona protección a nivel de CLIENTE.
 * Todas las páginas protegidas DEBEN tener también verificación server-side.
 *
 * Capas de seguridad:
 * 1. Este middleware (frontend) - Primera barrera
 * 2. Layout verification (server-side) - Segunda barrera
 * 3. API authentication (backend) - Tercera barrera
 *
 * ¡NUNCA confiar solo en protección del cliente para datos médicos!
 */

import { withAuth } from 'next-auth/middleware';
import { NextResponse } from 'next/server';

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;

    // Si el token tiene error (ej: usuario eliminado, token inválido), redirigir a login
    if (token?.error) {
      const loginUrl = new URL('/login', req.url);
      return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        // Permitir acceso solo si hay token Y no tiene errores
        return !!token && !token.error;
      },
    },
    pages: {
      signIn: '/login',
    },
  }
);

export const config = {
  matcher: [
    // Proteger TODAS las rutas excepto login, api/auth, y archivos estáticos
    '/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)',
  ],
};