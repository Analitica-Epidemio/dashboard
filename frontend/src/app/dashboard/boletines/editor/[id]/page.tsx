"use client";

import { use, useState, useEffect } from "react";
import { Save, FileDown, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { $api } from "@/lib/api/client";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { BoletinTiptapEditor } from "@/features/boletines/components/editor/boletin-tiptap-editor";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function EditorPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const templateId = parseInt(resolvedParams.id);
  const router = useRouter();

  const { data: templateResponse, isLoading } = $api.useQuery(
    'get',
    '/api/v1/boletines/templates/{template_id}',
    { params: { path: { template_id: templateId } } }
  );
  const updateTemplate = $api.useMutation('put', '/api/v1/boletines/templates/{template_id}');
  const createInstance = $api.useMutation('post', '/api/v1/boletines/instances');

  const template = templateResponse?.data;

  const [boletinName, setBoletinName] = useState("");
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Initialize content from template
  useEffect(() => {
    if (template?.widgets) {
      // Convert widgets to HTML for Tiptap
      // For now, we'll start with empty content - the seed will have the full content
      setContent(template.content || "");
    }
  }, [template]);

  const handleContentChange = (html: string) => {
    setContent(html);
  };

  const handleSave = async () => {
    if (!template) return;

    setIsSaving(true);
    try {
      await updateTemplate.mutateAsync({
        params: {
          path: { template_id: templateId }
        },
        body: {
          content: content,
        },
      });
      toast.success("Cambios guardados");
    } catch (error) {
      toast.error("Error al guardar");
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerate = async () => {
    if (!template || !boletinName) {
      toast.error("Ingresa un nombre para el boletín");
      return;
    }

    try {
      await createInstance.mutateAsync({
        body: {
          template_id: templateId,
          name: boletinName,
          parameters: {
            fecha: new Date().toISOString(),
          },
        },
      });

      toast.success("Boletín creado exitosamente");
      router.push("/dashboard/boletines");
    } catch (error) {
      toast.error("Error al crear boletín");
      console.error(error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col min-h-screen">
        <div className="border-b bg-background px-6 py-4">
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <Skeleton className="h-96 w-full max-w-4xl" />
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <h2 className="text-xl font-semibold mb-4">Plantilla no encontrada</h2>
        <Link href="/dashboard/boletines">
          <Button>Volver a Boletines</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header - Simple con back button */}
      <div className="flex-none border-b bg-background px-6 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard/boletines">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-lg font-semibold">{template.name}</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Input
              className="w-80"
              placeholder="Nombre del boletín (ej: Boletín Epidemiológico - Semana 40)"
              value={boletinName}
              onChange={(e) => setBoletinName(e.target.value)}
            />
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={isSaving || template.is_system}
            >
              <Save className="w-4 h-4 mr-2" />
              {isSaving ? "Guardando..." : "Guardar"}
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={!boletinName || createInstance.isPending}
            >
              <FileDown className="w-4 h-4 mr-2" />
              {createInstance.isPending ? "Generando..." : "Generar"}
            </Button>
          </div>
        </div>
      </div>

      {/* Editor - Full screen */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <BoletinTiptapEditor
          initialHtml={content}
          onChange={handleContentChange}
        />
      </div>
    </div>
  );
}
