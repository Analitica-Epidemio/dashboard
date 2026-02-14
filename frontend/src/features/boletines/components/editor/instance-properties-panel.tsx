"use client";

/**
 * Panel de propiedades para el editor de instancias de boletines
 * Muestra propiedades del elemento seleccionado y permite editarlas
 */

import { useState, useEffect } from "react";
import type { Editor } from "@tiptap/react";
import {
  Settings2,
  Type,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Image,
  BarChart3,
  Table,
  ChevronRight,
  Palette,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface InstancePropertiesPanelProps {
  editor: Editor | null;
  className?: string;
}

type SelectionType = "none" | "text" | "heading" | "image" | "chart" | "table" | "dynamicBlock";

interface SelectionInfo {
  type: SelectionType;
  attrs?: Record<string, unknown>;
  node?: unknown;
}

export function InstancePropertiesPanel({ editor, className }: InstancePropertiesPanelProps) {
  const [selectionInfo, setSelectionInfo] = useState<SelectionInfo>({ type: "none" });

  // Listen to selection changes
  useEffect(() => {
    if (!editor) return;

    const updateSelection = () => {
      const { selection, doc } = editor.state;
      const { from, to } = selection;

      // Check what's selected
      let newInfo: SelectionInfo = { type: "none" };

      // Try to find a node at the selection
      const node = doc.nodeAt(from);

      if (node) {
        switch (node.type.name) {
          case "image":
            newInfo = { type: "image", attrs: node.attrs, node };
            break;
          case "dynamicChart":
            newInfo = { type: "chart", attrs: node.attrs, node };
            break;
          case "dynamicTable":
            newInfo = { type: "table", attrs: node.attrs, node };
            break;
          case "dynamicBlock":
            newInfo = { type: "dynamicBlock", attrs: node.attrs, node };
            break;
          case "heading":
            newInfo = { type: "heading", attrs: node.attrs, node };
            break;
          default:
            // Check if there's text selected
            if (from !== to) {
              newInfo = { type: "text" };
            }
        }
      } else if (from !== to) {
        newInfo = { type: "text" };
      }

      setSelectionInfo(newInfo);
    };

    // Update on selection change
    editor.on("selectionUpdate", updateSelection);
    editor.on("transaction", updateSelection);

    // Initial update
    updateSelection();

    return () => {
      editor.off("selectionUpdate", updateSelection);
      editor.off("transaction", updateSelection);
    };
  }, [editor]);

  if (!editor) {
    return (
      <div className={cn("h-full flex items-center justify-center p-4", className)}>
        <p className="text-sm text-muted-foreground">Cargando editor...</p>
      </div>
    );
  }

  return (
    <div className={cn("h-full flex flex-col bg-background border-l", className)}>
      {selectionInfo.type === "none" ? (
        <EmptyState />
      ) : selectionInfo.type === "text" ? (
        <TextProperties editor={editor} />
      ) : selectionInfo.type === "heading" ? (
        <HeadingProperties editor={editor} attrs={selectionInfo.attrs} />
      ) : selectionInfo.type === "image" ? (
        <ImageProperties editor={editor} attrs={selectionInfo.attrs} />
      ) : selectionInfo.type === "chart" ? (
        <ChartProperties editor={editor} attrs={selectionInfo.attrs} />
      ) : selectionInfo.type === "dynamicBlock" ? (
        <DynamicBlockProperties editor={editor} attrs={selectionInfo.attrs} />
      ) : selectionInfo.type === "table" ? (
        <TableProperties editor={editor} attrs={selectionInfo.attrs} />
      ) : null}
    </div>
  );
}

// ============================================================================
// Empty State
// ============================================================================

function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-gradient-to-b from-muted/30 to-background">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center mb-6 shadow-inner">
        <Settings2 className="h-8 w-8 text-muted-foreground/50" />
      </div>
      <h3 className="text-base font-semibold text-foreground mb-2">
        Panel de Propiedades
      </h3>
      <p className="text-sm text-muted-foreground max-w-[220px] leading-relaxed">
        Selecciona un elemento en el editor para ver y editar sus propiedades
      </p>
      <div className="flex items-center gap-2 mt-6 text-xs text-muted-foreground">
        <ChevronRight className="h-4 w-4" />
        <span>Click en cualquier elemento</span>
      </div>
    </div>
  );
}

// ============================================================================
// Text Properties
// ============================================================================

function TextProperties({ editor }: { editor: Editor }) {
  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={Type} title="Formato de Texto" />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Text formatting */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Estilo</Label>
          <div className="flex gap-1">
            <Button
              variant={editor.isActive("bold") ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().toggleBold().run()}
            >
              <Bold className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive("italic") ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().toggleItalic().run()}
            >
              <Italic className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive("underline") ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().toggleUnderline().run()}
            >
              <UnderlineIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Separator />

        {/* Alignment */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Alineación</Label>
          <div className="flex gap-1">
            <Button
              variant={editor.isActive({ textAlign: "left" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("left").run()}
            >
              <AlignLeft className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive({ textAlign: "center" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("center").run()}
            >
              <AlignCenter className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive({ textAlign: "right" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("right").run()}
            >
              <AlignRight className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive({ textAlign: "justify" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("justify").run()}
            >
              <AlignJustify className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Separator />

        {/* Heading conversion */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Tipo de bloque</Label>
          <Select
            value={
              editor.isActive("heading", { level: 1 })
                ? "h1"
                : editor.isActive("heading", { level: 2 })
                  ? "h2"
                  : editor.isActive("heading", { level: 3 })
                    ? "h3"
                    : "p"
            }
            onValueChange={(value) => {
              if (value === "p") {
                editor.chain().focus().setParagraph().run();
              } else {
                const level = parseInt(value.replace("h", "")) as 1 | 2 | 3;
                editor.chain().focus().toggleHeading({ level }).run();
              }
            }}
          >
            <SelectTrigger className="w-full h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="p">Párrafo</SelectItem>
              <SelectItem value="h1">Título 1</SelectItem>
              <SelectItem value="h2">Título 2</SelectItem>
              <SelectItem value="h3">Título 3</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Heading Properties
// ============================================================================

function HeadingProperties({ editor, attrs }: { editor: Editor; attrs?: Record<string, unknown> }) {
  const level = (attrs?.level as number) || 1;

  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={Type} title={`Título H${level}`} />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Level */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Nivel</Label>
          <Select
            value={`h${level}`}
            onValueChange={(value) => {
              const newLevel = parseInt(value.replace("h", "")) as 1 | 2 | 3;
              editor.chain().focus().toggleHeading({ level: newLevel }).run();
            }}
          >
            <SelectTrigger className="w-full h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="h1">Título 1 (Grande)</SelectItem>
              <SelectItem value="h2">Título 2 (Mediano)</SelectItem>
              <SelectItem value="h3">Título 3 (Pequeño)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* Alignment */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Alineación</Label>
          <div className="flex gap-1">
            <Button
              variant={editor.isActive({ textAlign: "left" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("left").run()}
            >
              <AlignLeft className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive({ textAlign: "center" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("center").run()}
            >
              <AlignCenter className="h-4 w-4" />
            </Button>
            <Button
              variant={editor.isActive({ textAlign: "right" }) ? "secondary" : "outline"}
              size="icon"
              className="h-8 w-8"
              onClick={() => editor.chain().focus().setTextAlign("right").run()}
            >
              <AlignRight className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Separator />

        {/* Convert to paragraph */}
        <div>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => editor.chain().focus().setParagraph().run()}
          >
            Convertir a párrafo
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Image Properties
// ============================================================================

function ImageProperties({ editor, attrs }: { editor: Editor; attrs?: Record<string, unknown> }) {
  const src = (attrs?.src as string) || "";
  const alt = (attrs?.alt as string) || "";

  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={Image} title="Imagen" />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Preview */}
        {src && (
          <div className="rounded-lg border overflow-hidden">
            <img src={src} alt={alt} className="w-full h-auto max-h-32 object-contain bg-muted" />
          </div>
        )}

        {/* Alt text */}
        <div>
          <Label className="text-xs text-muted-foreground mb-2 block">Texto alternativo</Label>
          <Input
            value={alt}
            onChange={() => {
              // Would need to update the node attributes
              // This requires access to the node position
            }}
            placeholder="Descripción de la imagen"
            className="h-8 text-sm"
          />
        </div>

        <Separator />

        {/* Actions */}
        <div className="space-y-2">
          <Button
            variant="destructive"
            size="sm"
            className="w-full"
            onClick={() => editor.chain().focus().deleteSelection().run()}
          >
            Eliminar imagen
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Chart Properties
// ============================================================================

function ChartProperties({ editor, attrs }: { editor: Editor; attrs?: Record<string, unknown> }) {
  const title = (attrs?.title as string) || "Gráfico";
  const chartCode = (attrs?.chartCode as string) || "";

  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={BarChart3} title="Gráfico Dinámico" />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm font-medium text-blue-900">{title}</p>
          {chartCode && (
            <Badge variant="outline" className="mt-2 text-[10px]">
              {chartCode}
            </Badge>
          )}
        </div>

        <Separator />

        {/* Edit button */}
        <div>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => {
              // Dispatch custom event to open chart dialog
              window.dispatchEvent(
                new CustomEvent("edit-chart", {
                  detail: { attrs },
                })
              );
            }}
          >
            <Palette className="h-4 w-4 mr-2" />
            Editar configuración
          </Button>
        </div>

        <div>
          <Button
            variant="destructive"
            size="sm"
            className="w-full"
            onClick={() => editor.chain().focus().deleteSelection().run()}
          >
            Eliminar gráfico
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Dynamic Block Properties
// ============================================================================

function DynamicBlockProperties({
  editor,
  attrs,
}: {
  editor: Editor;
  attrs?: Record<string, unknown>;
}) {
  const blockType = (attrs?.blockType as string) || "block";
  const config = attrs?.config as { titulo?: string } | undefined;
  const title = config?.titulo || blockType;

  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={BarChart3} title="Bloque Dinámico" />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Info */}
        <div className="bg-violet-50 border border-violet-200 rounded-lg p-3">
          <p className="text-sm font-medium text-violet-900">{title}</p>
          <Badge variant="outline" className="mt-2 text-[10px]">
            {blockType}
          </Badge>
        </div>

        <Separator />

        <p className="text-xs text-muted-foreground">
          Este bloque se generó automáticamente desde la plantilla. Sus datos se calculan
          dinámicamente según el período del boletín.
        </p>

        <div>
          <Button
            variant="destructive"
            size="sm"
            className="w-full"
            onClick={() => editor.chain().focus().deleteSelection().run()}
          >
            Eliminar bloque
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Table Properties
// ============================================================================

function TableProperties({ editor, attrs }: { editor: Editor; attrs?: Record<string, unknown> }) {
  const title = (attrs?.title as string) || "Tabla";

  return (
    <div className="h-full flex flex-col">
      <PanelHeader icon={Table} title="Tabla Dinámica" />

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {/* Info */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
          <p className="text-sm font-medium text-emerald-900">{title}</p>
        </div>

        <Separator />

        <div>
          <Button
            variant="destructive"
            size="sm"
            className="w-full"
            onClick={() => editor.chain().focus().deleteSelection().run()}
          >
            Eliminar tabla
          </Button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Panel Header
// ============================================================================

function PanelHeader({ icon: Icon, title }: { icon: typeof Settings2; title: string }) {
  return (
    <div className="p-4 border-b">
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
    </div>
  );
}
