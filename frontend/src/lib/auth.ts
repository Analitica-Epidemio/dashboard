import type { NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { env } from '@/env';

/**
 * Refresca el access token usando el refresh token
 * Se llama automáticamente cuando el access token expira
 */
async function refreshAccessToken(token: any) {
  try {
    const response = await fetch(`${env.NEXT_PUBLIC_API_HOST}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: token.refreshToken,
      }),
    });

    const refreshedTokens = await response.json();

    if (!response.ok) {
      throw refreshedTokens;
    }

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
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
          const response = await fetch(`${env.NEXT_PUBLIC_API_HOST}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data = await response.json();

          // Parse JWT to extract user info
          const tokenPayload = JSON.parse(
            Buffer.from(data.access_token.split('.')[1], 'base64').toString()
          );

          return {
            id: tokenPayload.sub.toString(),
            email: tokenPayload.email,
            name: tokenPayload.email, // We don't have name in token, use email temporarily
            role: tokenPayload.role,
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            accessTokenExpires: Date.now() + 24 * 60 * 60 * 1000, // 24 horas
          };
        } catch {
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      // Initial sign in
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.role = user.role;
        token.accessTokenExpires = user.accessTokenExpires;
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