"use client";

import { useState } from "react";
import { MapPin, BarChart3, Filter, Download, Maximize2, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

interface MapaLayoutProps {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  detailsPanel?: React.ReactNode;
}

export function MapaLayout({ children, sidebar, detailsPanel }: MapaLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [detailsPanelOpen, setDetailsPanelOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="lg:hidden"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          <div className="flex items-center gap-2">
            <div className="bg-blue-100 p-2 rounded-lg">
              <MapPin className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                Dashboard de Vigilancia Epidemiológica
              </h1>
              <p className="text-xs text-gray-500">
                Análisis geoespacial de eventos de salud pública
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="hidden sm:flex gap-2">
            <Download className="h-4 w-4" />
            Exportar
          </Button>
          <Button variant="outline" size="sm" className="hidden sm:flex gap-2">
            <BarChart3 className="h-4 w-4" />
            Reportes
          </Button>
          <Button variant="ghost" size="icon" className="hidden sm:flex">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Desktop */}
        <aside
          className={cn(
            "hidden lg:block bg-white border-r border-gray-200 transition-all duration-300 overflow-y-auto",
            sidebarOpen ? "w-80" : "w-0"
          )}
        >
          {sidebarOpen && (
            <div className="p-4 space-y-4">
              {sidebar}
            </div>
          )}
        </aside>

        {/* Sidebar - Mobile (Sheet) */}
        <Sheet open={sidebarOpen && isMobile} onOpenChange={setSidebarOpen}>
          <SheetContent side="left" className="w-80 p-4 overflow-y-auto">
            {sidebar}
          </SheetContent>
        </Sheet>

        {/* Map Container */}
        <main className="flex-1 relative overflow-hidden">
          {children}

          {/* Floating Toggle Button (Desktop) */}
          {!sidebarOpen && (
            <Button
              variant="default"
              size="icon"
              className="absolute top-4 left-4 z-[1000] shadow-lg"
              onClick={() => setSidebarOpen(true)}
            >
              <Filter className="h-4 w-4" />
            </Button>
          )}
        </main>
      </div>

      {/* Details Panel (Bottom Drawer) */}
      {detailsPanel && (
        <div
          className={cn(
            "bg-white border-t border-gray-200 transition-all duration-300 overflow-y-auto shadow-2xl",
            detailsPanelOpen ? "h-80" : "h-0"
          )}
        >
          {detailsPanelOpen && (
            <div className="p-4">
              {detailsPanel}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
