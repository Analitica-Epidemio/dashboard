"use client";

import { use, useState } from "react";
import { ArrowLeft, Save, FileDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { $api, apiClient } from "@/lib/api/client";
import { Skeleton } from "@/components/ui/skeleton";
import { BoletinTiptapEditor } from "@/features/boletines/components/editor/boletin-tiptap-editor";
import { toast } from "sonner";
import { env } from "@/env";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function InstanceEditorPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const instanceId = parseInt(resolvedParams.id);

  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const { data: instanceResponse, isLoading } = $api.useQuery(
    "get",
    "/api/v1/boletines/instances/{instance_id}",
    { params: { path: { instance_id: instanceId } } }
  );

  const instance = instanceResponse?.data;

  // Guardar contenido
  const handleSave = async () => {
    if (!content) {
      toast.error("No hay contenido para guardar");
      return;
    }

    setIsSaving(true);
    try {
      await apiClient.PUT("/api/v1/boletines/instances/{instance_id}/content", {
        params: { path: { instance_id: instanceId } },
        body: { content },
      });

      toast.success("Boletín guardado exitosamente");
    } catch (error) {
      console.error("Error guardando:", error);
      toast.error("Error al guardar el boletín");
    } finally {
      setIsSaving(false);
    }
  };

  // Exportar a PDF
  const handleExportPDF = async () => {
    setIsExporting(true);
    try {
      // Get auth token
      const { getSession } = await import("next-auth/react");
      const session = await getSession();

      // Llamar al endpoint de exportación
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

      // Descargar el PDF
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
  };

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
          <Link href="/dashboard/analytics">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver a Analytics
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-muted flex flex-col overflow-hidden">
      <div className="border-b bg-background">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/dashboard/analytics">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Volver
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-xl font-semibold">{instance.name}</h1>
            <p className="text-sm text-muted-foreground">
              Estado: {instance.status}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSave}
              disabled={isSaving || !content}
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
                </>
              )}
            </Button>
            <Button
              size="sm"
              onClick={handleExportPDF}
              disabled={isExporting || !content}
            >
              {isExporting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exportando...
                </>
              ) : (
                <>
                  <FileDown className="mr-2 h-4 w-4" />
                  Exportar PDF
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="overflow-y-scroll flex-1">
        <BoletinTiptapEditor
          initialHtml={instance.content || ""}
          onChange={(html) => {
            setContent(html);
          }}
        />
      </div>
    </div>
  );
}
