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

interface EpidemiologyLayoutProps {
  children: React.ReactNode;
}

export default async function EpidemiologyLayout({
  children,
}: EpidemiologyLayoutProps) {
  // 🔒 VERIFICACIÓN SERVER-SIDE - Protección crítica para datos médicos
  const session = await getServerSession(authOptions);

  // Si no hay sesión, redirigir a login ANTES de renderizar contenido
  if (!session) {
    redirect('/login');
  }

  // Verificar que la sesión tenga los datos necesarios
  if (!session.user || !session.accessToken) {
    redirect('/login');
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Contenido principal con altura completa */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
