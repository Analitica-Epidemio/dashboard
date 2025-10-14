"use client";

import { use, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Share2,
  Printer,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

import { useEvento } from "@/lib/api/eventos";
import { EventoDetail } from "../_components/evento-detail";

export default function EventoDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = use(params);
  const eventoId = parseInt(id);
  const [copied, setCopied] = useState(false);

  const eventoQuery = useEvento(eventoId);
  const evento = eventoQuery.data?.data;

  // Keyboard shortcuts (ESC to go back, Cmd+P to print)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC to go back (like GitHub)
      if (e.key === "Escape") {
        router.back();
      }
      // Cmd/Ctrl + P to print
      if ((e.metaKey || e.ctrlKey) && e.key === "p") {
        e.preventDefault();
        handlePrint();
      }
      // Cmd/Ctrl + K to copy URL
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        handleCopyURL();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Evento ${evento?.id_evento_caso}`,
          text: `Ver evento epidemiológico #${evento?.id_evento_caso}`,
          url: window.location.href,
        });
      } catch (err) {
        console.log("Error sharing:", err);
      }
    } else {
      handleCopyURL();
    }
  };

  const handleCopyURL = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success("URL copiada al portapapeles");
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExport = () => {
    toast.success("Exportando evento...");
    // TODO: Implement export functionality
  };

  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset>
        {/* Header with breadcrumbs and actions (GitHub/Linear style) */}
        <header className="sticky top-0 z-10 flex h-14 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-6" />

          {/* Breadcrumbs (GitHub/Vercel style) */}
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href="/dashboard">Dashboard</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href="/dashboard/eventos">Eventos</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>
                  #{evento?.id_evento_caso || eventoId}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <div className="ml-auto flex items-center gap-2">
            {/* Navigation prev/next (Linear style) */}
            <div className="hidden md:flex items-center gap-1 mr-2">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => router.push(`/dashboard/eventos/${eventoId - 1}`)}
                title="Evento anterior (←)"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => router.push(`/dashboard/eventos/${eventoId + 1}`)}
                title="Evento siguiente (→)"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Action buttons (Vercel style) */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopyURL}
              className="hidden sm:flex"
            >
              {copied ? (
                <>
                  <Check className="mr-2 h-4 w-4 text-green-600" />
                  Copiado
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copiar URL
                </>
              )}
            </Button>

            {/* More actions dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Share2 className="mr-2 h-4 w-4" />
                  <span className="hidden sm:inline">Compartir</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleShare}>
                  <Share2 className="mr-2 h-4 w-4" />
                  Compartir
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCopyURL}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copiar URL
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handlePrint}>
                  <Printer className="mr-2 h-4 w-4" />
                  Imprimir
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleExport}>
                  <Download className="mr-2 h-4 w-4" />
                  Exportar PDF
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() =>
                    window.open(`/dashboard/eventos/${eventoId}`, "_blank")
                  }
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Abrir en nueva pestaña
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.back()}
              className="hidden sm:flex"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver
            </Button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 p-6 overflow-y-auto print:p-0">
          {/* Print-only header */}
          <div className="hidden print:block mb-6">
            <h1 className="text-2xl font-bold">
              Evento Epidemiológico #{evento?.id_evento_caso}
            </h1>
            <p className="text-sm text-muted-foreground">
              Generado el {new Date().toLocaleDateString("es-ES")}
            </p>
          </div>

          {/* Keyboard shortcuts hint (Linear style) */}
          <div className="hidden md:block mb-4 text-xs text-muted-foreground print:hidden">
            <kbd className="px-2 py-1 bg-muted rounded text-xs">ESC</kbd> para volver •{" "}
            <kbd className="px-2 py-1 bg-muted rounded text-xs">←</kbd>
            <kbd className="px-2 py-1 bg-muted rounded text-xs">→</kbd> para navegar •{" "}
            <kbd className="px-2 py-1 bg-muted rounded text-xs">⌘K</kbd> copiar URL
          </div>

          {/* Evento detail component (reused) */}
          <EventoDetail eventoId={eventoId} onClose={() => router.back()} />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
