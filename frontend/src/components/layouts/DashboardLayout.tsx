/**
 * Layout de Dashboard con mejores prácticas
 * 
 * Características:
 * - Sidebar collapsible responsive
 * - Área de contenido scrolleable
 * - Header fijo
 * - Mobile-first responsive
 * - Overflow handling correcto
 */

import React from "react";
import { CollapsibleSidebar } from "@/features/layout/components";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  headerActions?: React.ReactNode;
}

export function DashboardLayout({ 
  children, 
  title, 
  subtitle, 
  headerActions 
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      {/* Container principal con grid layout */}
      <div className="grid min-h-screen w-full lg:grid-cols-[280px_1fr] grid-rows-[auto_1fr]">
        
        {/* Sidebar - ocupa toda la altura en desktop */}
        <div className="hidden lg:block lg:row-span-2">
          <CollapsibleSidebar />
        </div>

        {/* Header - fijo en la parte superior */}
        {(title || headerActions) && (
          <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 items-center px-4 lg:px-6">
              {/* Mobile sidebar trigger podría ir aquí */}
              <div className="lg:hidden">
                {/* TODO: Mobile sidebar trigger */}
              </div>
              
              <div className="flex flex-1 items-center justify-between">
                <div className="flex flex-col">
                  {title && (
                    <h1 className="text-lg font-semibold tracking-tight">
                      {title}
                    </h1>
                  )}
                  {subtitle && (
                    <p className="text-sm text-muted-foreground">
                      {subtitle}
                    </p>
                  )}
                </div>
                {headerActions && (
                  <div className="flex items-center gap-2">
                    {headerActions}
                  </div>
                )}
              </div>
            </div>
          </header>
        )}

        {/* Main content area - scrolleable */}
        <main className="flex-1 overflow-auto lg:col-start-2">
          {/* Sidebar móvil overlay */}
          <div className="lg:hidden">
            <CollapsibleSidebar />
          </div>
          
          {/* Contenido scrolleable con padding apropiado */}
          <div className="container py-4 px-4 lg:px-6 lg:py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

/**
 * Wrapper para páginas que necesitan scroll completo sin padding
 * Útil para dashboards con gráficos que ocupan toda la pantalla
 */
export function DashboardLayoutFullscreen({ 
  children, 
  title, 
  subtitle, 
  headerActions 
}: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="grid min-h-screen w-full lg:grid-cols-[280px_1fr] grid-rows-[auto_1fr]">
        
        <div className="hidden lg:block lg:row-span-2">
          <CollapsibleSidebar />
        </div>

        {(title || headerActions) && (
          <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-14 items-center px-4 lg:px-6">
              <div className="lg:hidden">
                {/* Mobile sidebar trigger */}
              </div>
              
              <div className="flex flex-1 items-center justify-between">
                <div className="flex flex-col">
                  {title && (
                    <h1 className="text-lg font-semibold tracking-tight">
                      {title}
                    </h1>
                  )}
                  {subtitle && (
                    <p className="text-sm text-muted-foreground">
                      {subtitle}
                    </p>
                  )}
                </div>
                {headerActions && (
                  <div className="flex items-center gap-2">
                    {headerActions}
                  </div>
                )}
              </div>
            </div>
          </header>
        )}

        {/* Full screen main content */}
        <main className="flex-1 overflow-hidden lg:col-start-2">
          <div className="lg:hidden">
            <CollapsibleSidebar />
          </div>
          
          <div className="h-full overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}