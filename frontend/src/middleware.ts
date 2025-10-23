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

export { default } from 'next-auth/middleware';

export const config = {
  matcher: [
    // Proteger todas las rutas del dashboard
    '/dashboard/:path*',

    // Agregar aquí otras rutas protegidas en el futuro
    // '/admin/:path*',
    // '/reportes/:path*',
  ],
};