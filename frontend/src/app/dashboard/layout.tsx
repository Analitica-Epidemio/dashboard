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
      {/* Contenido principal con altura completa */}
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  );
}
