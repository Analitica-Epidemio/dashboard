/**
 * Auth Hook using NextAuth
 */

import { useSession, signIn, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

/**
 * Main authentication hook
 */
export function useAuth() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Helper functions
  const login = async (credentials: { email: string; password: string; remember_me?: boolean }) => {
    setIsLoggingIn(true);
    setLoginError(null);

    try {
      const result = await signIn('credentials', {
        email: credentials.email,
        password: credentials.password,
        remember_me: credentials.remember_me ? 'true' : 'false',
        redirect: false,
      });

      if (result?.error) {
        setLoginError('Invalid credentials');
      } else if (result?.ok) {
        router.push('/dashboard');
      }
    } catch (error) {
      setLoginError('Login failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const logout = async () => {
    await signOut({ redirect: false });
    router.push('/');
  };

  const user = session?.user;
  const isAuthenticated = !!session;
  const isSuperadmin = session?.user.role === 'superadmin';
  const isEpidemiologist = session?.user.role === 'epidemiologo';

  return {
    // State
    user,
    isLoading: status === 'loading',
    error: loginError,
    isAuthenticated,
    isSuperadmin,
    isEpidemiologist,

    // Actions
    login,
    logout,
    refetchUser: () => {}, // NextAuth handles session automatically

    // Mutation states
    isLoggingIn,
    isLoggingOut: false, // NextAuth handles this
    loginError,
  };
}