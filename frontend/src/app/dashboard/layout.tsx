/**
 * Layout principal para la sección de epidemiología
 * Estilo Analytics Dashboard con sidebar persistente
 *
 * SEGURIDAD: Verificación server-side de autenticación
 * Este layout protege TODAS las rutas del dashboard
 */

import React from "react";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { SessionValidator } from "@/components/auth/session-validator";

interface EpidemiologyLayoutProps {
  children: React.ReactNode;
}

export default async function EpidemiologyLayout({
  children,
}: EpidemiologyLayoutProps) {
  // 🔒 VERIFICACIÓN SERVER-SIDE - Protección crítica para datos médicos
  console.log('📋 [Dashboard Layout] Checking session...');
  const session = await getServerSession(authOptions);

  console.log('📋 [Dashboard Layout] Session result:', {
    hasSession: !!session,
    hasUser: !!session?.user,
    userEmail: session?.user?.email,
    hasAccessToken: !!session?.accessToken,
    sessionError: session?.error,
  });

  // Si no hay sesión, redirigir a login ANTES de renderizar contenido
  if (!session) {
    console.log('📋 [Dashboard Layout] No session, redirecting to login');
    redirect('/login');
  }

  // Verificar que la sesión tenga los datos necesarios
  if (!session.user || !session.accessToken) {
    console.log('📋 [Dashboard Layout] Missing user or accessToken, redirecting to login');
    redirect('/login');
  }

  // Si la sesión tiene error (usuario eliminado, token inválido), redirigir
  if (session.error) {
    console.log('📋 [Dashboard Layout] Session has error, redirecting to login:', session.error);
    redirect('/login');
  }

  console.log('📋 [Dashboard Layout] Session valid, rendering dashboard');

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Validador de sesión en tiempo real (client-side) */}
      <SessionValidator />

      {/* Contenido principal con altura completa */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
