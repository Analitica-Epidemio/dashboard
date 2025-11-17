"use client";

import React, { useState } from "react";
import { DndContext, closestCenter, DragEndEvent } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy, arrayMove } from "@dnd-kit/sortable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Save, FileText, Eye, EyeOff } from "lucide-react";
import { BlockRenderer, BlockPalette } from "./blocks";
import type { BoletinTemplate, Block, BlockType } from "./blocks/types";

interface BoletinEditorProps {
  initialTemplate: BoletinTemplate;
  onSave: (template: BoletinTemplate) => void;
}

export function BoletinEditor({ initialTemplate, onSave }: BoletinEditorProps) {
  const [template, setTemplate] = useState<BoletinTemplate>(initialTemplate);
  const [hasChanges, setHasChanges] = useState(false);
  const [showPreview, setShowPreview] = useState(true);

  const updatePortada = <K extends keyof typeof template.portada>(
    field: K,
    value: (typeof template.portada)[K]
  ) => {
    setTemplate((prev) => ({
      ...prev,
      portada: { ...prev.portada, [field]: value },
    }));
    setHasChanges(true);
  };

  const updateBlock = (updatedBlock: Block) => {
    setTemplate((prev) => ({
      ...prev,
      bloques: prev.bloques.map((b) => (b.id === updatedBlock.id ? updatedBlock : b)),
    }));
    setHasChanges(true);
  };

  const deleteBlock = (id: string) => {
    setTemplate((prev) => ({
      ...prev,
      bloques: prev.bloques.filter((b) => b.id !== id),
    }));
    setHasChanges(true);
  };

  const addBlock = (type: BlockType) => {
    const newBlock: Block = createEmptyBlock(type, template.bloques.length + 1);
    setTemplate((prev) => ({
      ...prev,
      bloques: [...prev.bloques, newBlock],
    }));
    setHasChanges(true);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setTemplate((prev) => {
        const oldIndex = prev.bloques.findIndex((b) => b.id === active.id);
        const newIndex = prev.bloques.findIndex((b) => b.id === over.id);

        const reordered = arrayMove(prev.bloques, oldIndex, newIndex);

        // Actualizar el orden de cada bloque
        const withUpdatedOrder = reordered.map((b, idx) => ({
          ...b,
          orden: idx + 1,
        }));

        return { ...prev, bloques: withUpdatedOrder };
      });
      setHasChanges(true);
    }
  };

  const handleSave = () => {
    onSave(template);
    setHasChanges(false);
  };

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Panel Principal */}
      <div className={showPreview ? "col-span-8" : "col-span-12"}>
        <div className="space-y-6">
          {/* Header con acciones */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    {template.nombre}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Template de Boletin Semanal - {template.bloques.length} bloques
                  </p>
                </div>
                <div className="flex gap-2 items-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowPreview(!showPreview)}
                  >
                    {showPreview ? (
                      <>
                        <EyeOff className="h-4 w-4 mr-2" />
                        Ocultar Preview
                      </>
                    ) : (
                      <>
                        <Eye className="h-4 w-4 mr-2" />
                        Mostrar Preview
                      </>
                    )}
                  </Button>
                  {hasChanges && (
                    <span className="text-xs text-orange-600 flex items-center gap-1">
                      Sin guardar
                    </span>
                  )}
                  <Button onClick={handleSave} disabled={!hasChanges}>
                    <Save className="h-4 w-4 mr-2" />
                    Guardar
                  </Button>
                </div>
              </div>
            </CardHeader>
          </Card>

          {/* Configuracion de Portada */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Portada</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Titulo</Label>
                <Input
                  value={template.portada.titulo}
                  onChange={(e) => updatePortada("titulo", e.target.value)}
                  placeholder="Ej: Boletin Epidemiologico Provincial"
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Subtitulo</Label>
                <Input
                  value={template.portada.subtitulo || ""}
                  onChange={(e) => updatePortada("subtitulo", e.target.value)}
                  placeholder="Ej: Departamento de Epidemiologia"
                  className="mt-2"
                />
              </div>

              <div className="flex items-center justify-between py-2">
                <div>
                  <Label>Incluir logo</Label>
                  <p className="text-xs text-muted-foreground">
                    Logo institucional en la portada
                  </p>
                </div>
                <Switch
                  checked={template.portada.incluir_logo}
                  onCheckedChange={(checked) => updatePortada("incluir_logo", checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Bloques */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Bloques del Boletin</CardTitle>
                <BlockPalette onAddBlock={addBlock} />
              </div>
              <p className="text-sm text-muted-foreground">
                Arrastra para reordenar. Cada bloque es independiente y configurable.
              </p>
            </CardHeader>
            <CardContent>
              <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext
                  items={template.bloques.map((b) => b.id)}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-3">
                    {template.bloques.map((block) => (
                      <BlockRenderer
                        key={block.id}
                        block={block}
                        onChange={updateBlock}
                        onDelete={deleteBlock}
                      />
                    ))}

                    {template.bloques.length === 0 && (
                      <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                        <FileText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                        <p className="font-medium">No hay bloques</p>
                        <p className="text-sm mt-1">
                          Agrega un bloque para comenzar
                        </p>
                      </div>
                    )}
                  </div>
                </SortableContext>
              </DndContext>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Panel de Preview */}
      {showPreview && (
        <div className="col-span-4">
          <div className="sticky top-6">
            <Card className="h-[calc(100vh-3rem)] flex flex-col">
              <CardHeader>
                <CardTitle className="text-lg">Preview</CardTitle>
                <p className="text-xs text-muted-foreground">
                  Vista previa del contenido
                </p>
              </CardHeader>
              <CardContent className="flex-1 overflow-auto">
                <div className="space-y-4 text-sm">
                  {/* Portada preview */}
                  <div className="border-l-4 border-blue-500 pl-3 py-3 bg-blue-50">
                    <h1 className="text-xl font-bold text-blue-900">
                      {template.portada.titulo}
                    </h1>
                    {template.portada.subtitulo && (
                      <p className="text-blue-700 mt-1">{template.portada.subtitulo}</p>
                    )}
                    {template.portada.incluir_logo && (
                      <p className="text-xs text-blue-600 mt-2">Logo institucional</p>
                    )}
                  </div>

                  {/* Bloques preview */}
                  {template.bloques.map((block) => (
                    <div key={block.id} className="border-l-2 border-gray-300 pl-3 py-2">
                      <div className="text-xs text-muted-foreground mb-1">
                        #{block.orden} - {block.type.toUpperCase()}
                      </div>
                      {renderBlockPreview(block)}
                    </div>
                  ))}

                  {template.bloques.length === 0 && (
                    <p className="text-center text-muted-foreground py-8">
                      Sin bloques para mostrar
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper para crear bloques vacios
function createEmptyBlock(type: BlockType, orden: number): Block {
  const baseBlock = {
    id: `block-${Date.now()}-${Math.random()}`,
    orden,
  };

  switch (type) {
    case "heading":
      return { ...baseBlock, type: "heading", level: 2, content: "" };
    case "paragraph":
      return { ...baseBlock, type: "paragraph", content: "<p></p>" };
    case "table":
      return {
        ...baseBlock,
        type: "table",
        dataSource: "manual",
        headers: [],
        rows: [],
      };
    case "chart":
      return {
        ...baseBlock,
        type: "chart",
        chartType: "line",
        dataSource: "manual",
      };
    case "image":
      return { ...baseBlock, type: "image", url: "" };
    case "divider":
      return { ...baseBlock, type: "divider" };
    case "pagebreak":
      return { ...baseBlock, type: "pagebreak" };
  }
}

// Helper para renderizar preview de cada bloque
function renderBlockPreview(block: Block): React.ReactNode {
  switch (block.type) {
    case "heading":
      const headingLevel = block.level as 1 | 2 | 3 | 4 | 5 | 6;
      return React.createElement(
        `h${headingLevel}`,
        {
          className: `font-bold ${
            block.level === 1 ? "text-2xl" : block.level === 2 ? "text-xl" : "text-lg"
          }`,
          style: { textAlign: block.align || "left" },
        },
        block.content || "(Titulo vacio)"
      );

    case "paragraph":
      return (
        <div
          className="prose prose-sm max-w-none"
          style={{ textAlign: block.align || "left" }}
          dangerouslySetInnerHTML={{ __html: block.content }}
        />
      );

    case "table":
      if (block.dataSource === "query") {
        return (
          <div className="bg-blue-50 p-2 rounded text-xs">
            <p className="font-medium">Tabla dinamica: {block.query?.type}</p>
            {block.title && <p className="text-muted-foreground">{block.title}</p>}
          </div>
        );
      }
      return (
        <div className="text-xs">
          {block.title && <p className="font-medium mb-1">{block.title}</p>}
          <div className="border rounded overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-100">
                <tr>
                  {(block.headers || []).map((h, i) => (
                    <th key={i} className="border px-2 py-1 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(block.rows || []).map((row, i) => (
                  <tr key={i}>
                    {row.map((cell, j) => (
                      <td key={j} className="border px-2 py-1">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {block.footnote && (
            <p className="text-muted-foreground mt-1">{block.footnote}</p>
          )}
        </div>
      );

    case "chart":
      if (block.dataSource === "query") {
        return (
          <div className="bg-blue-50 p-2 rounded text-xs">
            <p className="font-medium">
              Grafico dinamico: {block.query?.type} ({block.chartType})
            </p>
            {block.title && <p className="text-muted-foreground">{block.title}</p>}
          </div>
        );
      }
      return (
        <div className="bg-gray-100 p-4 rounded text-xs">
          {block.title && <p className="font-medium mb-2">{block.title}</p>}
          <div
            className="border-2 border-dashed border-gray-300 flex items-center justify-center"
            style={{ height: `${block.height || 300}px` }}
          >
            Grafico: {block.chartType}
          </div>
          {block.footnote && (
            <p className="text-muted-foreground mt-2">{block.footnote}</p>
          )}
        </div>
      );

    case "image":
      return (
        <div className="text-center">
          {block.url ? (
            <img
              src={block.url}
              alt={block.alt || ""}
              className="max-w-full mx-auto"
              style={{
                width: block.width ? `${block.width}px` : "auto",
                textAlign: block.align || "center",
              }}
            />
          ) : (
            <div className="border-2 border-dashed p-8 text-muted-foreground">
              (Imagen sin URL)
            </div>
          )}
          {block.caption && (
            <p className="text-xs text-muted-foreground mt-2">{block.caption}</p>
          )}
        </div>
      );

    case "divider":
      return <hr className="border-t-2 border-gray-300 my-4" />;

    case "pagebreak":
      return (
        <div className="border-2 border-dashed border-amber-400 p-2 text-center text-xs text-amber-600">
          --- SALTO DE PAGINA ---
        </div>
      );

    default:
      return null;
  }
}
