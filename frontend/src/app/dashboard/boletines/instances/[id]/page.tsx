"use client";

/**
 * Editor de instancia de boletín con 3 paneles:
 * - Estructura del documento
 * - Editor visual
 * - Panel de propiedades
 */

import { use, useState, useEffect, useCallback } from "react";
import { ArrowLeft, Save, FileDown, Loader2, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { $api, apiClient } from "@/lib/api/client";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { BoletinThreePanelEditor } from "@/features/boletines/components/editor/boletin-three-panel-editor";
import { useKeyboardShortcuts, formatShortcut } from "@/features/boletines/hooks/use-keyboard-shortcuts";
import { toast } from "sonner";
import { env } from "@/env";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function InstanceEditorPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const instanceId = parseInt(resolvedParams.id);

  const [content, setContent] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const { data: instanceResponse, isLoading } = $api.useQuery(
    "get",
    "/api/v1/boletines/instances/{instance_id}",
    { params: { path: { instance_id: instanceId } } }
  );

  const instance = instanceResponse?.data;

  // Initialize content when instance loads
  useEffect(() => {
    if (instance?.content && content === null) {
      setContent(instance.content);
    }
  }, [instance, content]);

  // Handle content change
  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setHasChanges(true);
  };

  // Save content
  const handleSave = useCallback(async () => {
    if (!content) {
      toast.error("No hay contenido para guardar");
      return;
    }

    if (!hasChanges || isSaving) return;

    setIsSaving(true);
    try {
      await apiClient.PUT("/api/v1/boletines/instances/{instance_id}/content", {
        params: { path: { instance_id: instanceId } },
        body: { content },
      });

      toast.success("Boletín guardado exitosamente");
      setHasChanges(false);
    } catch (error) {
      console.error("Error guardando:", error);
      toast.error("Error al guardar el boletín");
    } finally {
      setIsSaving(false);
    }
  }, [content, hasChanges, isSaving, instanceId]);

  // Export to PDF
  const handleExportPDF = useCallback(async () => {
    if (isExporting || !content) return;

    setIsExporting(true);
    try {
      const { getSession } = await import("next-auth/react");
      const session = await getSession();

      const response = await fetch(
        `${env.NEXT_PUBLIC_API_HOST}/api/v1/boletines/instances/${instanceId}/export-pdf`,
        {
          method: "POST",
          headers: {
            ...(session?.accessToken && {
              Authorization: `Bearer ${session.accessToken}`,
            }),
          },
        }
      );

      if (!response.ok) {
        throw new Error("Error al generar PDF");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${instance?.name || "boletin"}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success("PDF generado y descargado exitosamente");
    } catch (error) {
      console.error("Error exportando:", error);
      toast.error("Error al exportar a PDF");
    } finally {
      setIsExporting(false);
    }
  }, [content, instanceId, isExporting, instance?.name]);

  // Keyboard shortcuts (Cmd+S save, Cmd+E export)
  useKeyboardShortcuts({
    onSave: handleSave,
    onExport: handleExportPDF,
    enabled: true,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-muted p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (!instance) {
    return (
      <div className="min-h-screen bg-muted p-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold mb-4">Boletín no encontrado</h1>
          <Link href="/dashboard/boletines">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver a Boletines
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-muted flex flex-col overflow-hidden">
      {/* Header */}
      <div className="border-b bg-background shrink-0">
        <div className="px-4 py-3 flex items-center gap-4">
          <Link href="/dashboard/boletines">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver
            </Button>
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold truncate">{instance.name}</h1>
              {instance.semana_epidemiologica && instance.anio_epidemiologico && (
                <Badge variant="outline" className="shrink-0 text-xs">
                  <Calendar className="h-3 w-3 mr-1" />
                  SE {instance.semana_epidemiologica}/{instance.anio_epidemiologico}
                  {instance.num_semanas && ` (${instance.num_semanas} sem)`}
                </Badge>
              )}
            </div>
            {hasChanges && (
              <span className="text-xs text-amber-600">Cambios sin guardar</span>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={isSaving || !content || !hasChanges}
              title={`Guardar (${formatShortcut("S")})`}
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Guardar
                  <kbd className="ml-2 hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                    {formatShortcut("S")}
                  </kbd>
                </>
              )}
            </Button>
            <Button
              size="sm"
              onClick={handleExportPDF}
              disabled={isExporting || !content}
              title={`Exportar PDF (${formatShortcut("E")})`}
            >
              {isExporting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exportando...
                </>
              ) : (
                <>
                  <FileDown className="mr-2 h-4 w-4" />
                  Exportar
                  <kbd className="ml-2 hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted/50 px-1.5 font-mono text-[10px] font-medium text-primary-foreground/70">
                    {formatShortcut("E")}
                  </kbd>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Editor with 3 panels */}
      <BoletinThreePanelEditor
        initialHtml={instance.content || ""}
        onChange={handleContentChange}
        className="flex-1"
        defaultFechaDesde={instance.fecha_inicio}
        defaultFechaHasta={instance.fecha_fin}
      />
    </div>
  );
}
