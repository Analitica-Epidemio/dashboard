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

    // DEBUG: Log middleware execution
    console.log('🛡️ [Middleware]', {
      path: req.nextUrl.pathname,
      hasToken: !!token,
      tokenError: token?.error,
      tokenEmail: token?.email,
    });

    // Si el token tiene error (ej: usuario eliminado, token inválido), redirigir a login
    if (token?.error) {
      console.log('🛡️ [Middleware] Token has error, redirecting to login:', token.error);
      const loginUrl = new URL('/login', req.url);
      return NextResponse.redirect(loginUrl);
    }

    console.log('🛡️ [Middleware] Access granted to:', req.nextUrl.pathname);
    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        const isAuthorized = !!token && !token.error;
        console.log('🛡️ [Middleware:authorized]', {
          path: req.nextUrl.pathname,
          hasToken: !!token,
          tokenError: token?.error,
          isAuthorized,
        });
        return isAuthorized;
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