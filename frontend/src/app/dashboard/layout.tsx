/**
 * Layout principal para la sección de epidemiología
 * Estilo Analytics Dashboard con sidebar persistente
 */

import React from "react";

interface EpidemiologyLayoutProps {
  children: React.ReactNode;
}

export default function EpidemiologyLayout({
  children,
}: EpidemiologyLayoutProps) {
  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Header fijo */}
      <header className="bg-white border-b border-gray-200 flex-shrink-0 z-40">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold text-gray-900">
              Sistema de Vigilancia Epidemiológica
            </h1>
          </div>
        </div>
      </header>

      {/* Contenido principal con altura completa */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
