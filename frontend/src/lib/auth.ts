import type { NextAuthOptions } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';
import { env } from '@/env';

// URL para llamadas server-side (NextAuth corre en el servidor)
// En Docker: usa API_HOST_INTERNAL (http://api:8000) para red interna
// En local: usa NEXT_PUBLIC_API_HOST como fallback
const serverApiHost = env.API_HOST_INTERNAL ?? env.NEXT_PUBLIC_API_HOST;

/**
 * Refresca el access token usando el refresh token
 * Se llama automáticamente cuando el access token expira
 */
async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await fetch(`${serverApiHost}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token_refresco: token.refreshToken,
      }),
    });

    const refreshedTokens = await response.json();

    if (!response.ok) {
      throw refreshedTokens;
    }

    return {
      ...token,
      accessToken: refreshedTokens.token_acceso,
      refreshToken: refreshedTokens.token_refresco ?? token.refreshToken,
      accessTokenExpires: Date.now() + 24 * 60 * 60 * 1000, // 24 horas
    };
  } catch (error) {
    console.error('Error refreshing access token:', error);

    return {
      ...token,
      error: 'RefreshAccessTokenError',
    };
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const response = await fetch(`${serverApiHost}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials.email,
              contrasena: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data = await response.json();

          // Parse JWT to extract user info
          const tokenPayload = JSON.parse(
            Buffer.from(data.token_acceso.split('.')[1], 'base64').toString()
          );

          return {
            id: tokenPayload.sub.toString(),
            email: tokenPayload.email,
            name: tokenPayload.email, // We don't have name in token, use email temporarily
            role: tokenPayload.role,
            accessToken: data.token_acceso,
            refreshToken: data.token_refresco,
            accessTokenExpires: Date.now() + 24 * 60 * 60 * 1000, // 24 horas
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, trigger }) {
      // Initial sign in
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.role = user.role;
        token.accessTokenExpires = user.accessTokenExpires;
        token.lastValidated = Date.now();
      }

      // Validate token against backend every 2 minutes (even if not expired)
      // This ensures deleted/disabled users are logged out promptly
      // SEGURIDAD: Intervalo reducido para datos médicos sensibles
      const VALIDATION_INTERVAL_MS = 2 * 60 * 1000; // 2 minutos
      const shouldValidate = trigger === 'update' ||
        !token.lastValidated ||
        Date.now() - (token.lastValidated as number) > VALIDATION_INTERVAL_MS;

      if (shouldValidate && token.accessToken) {
        try {
          // Call /auth/me to validate the token is still valid
          // NOTE: Can't use apiClient here as it would create circular dependency
          const response = await fetch(`${serverApiHost}/api/v1/auth/me`, {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token.accessToken}`,
              'Content-Type': 'application/json',
            },
            cache: 'no-store',
          });

          if (!response.ok) {
            // Token is invalid (user deleted, disabled, or token revoked)
            console.log('🔒 Token validation failed, forcing re-login');
            return { ...token, error: 'TokenValidationFailed' };
          }

          // Update last validation timestamp
          token.lastValidated = Date.now();
          console.log('✅ Token validated successfully');
        } catch (error) {
          console.error('❌ Error validating token:', error);
          return { ...token, error: 'TokenValidationError' };
        }
      }

      // Return previous token if the access token has not expired yet
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // 🔄 Access token has expired, try to refresh it
      console.log('Access token expired, refreshing...');
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.refreshToken = token.refreshToken as string;
      session.user.role = token.role as string;

      // Pass error to client side to handle forced re-login
      if (token.error) {
        session.error = token.error as string;
      }

      return session;
    },
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 7 * 24 * 60 * 60, // 7 days (matches refresh token expiry)
  },
  cookies: {
    sessionToken: {
      name: 'next-auth.session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      },
    },
  },
};