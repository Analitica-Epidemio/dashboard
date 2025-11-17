"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, Database, Edit3, Plus, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AVAILABLE_QUERIES, type ChartBlock } from "./types";

interface ChartBlockEditorProps {
  block: ChartBlock;
  onChange: (block: ChartBlock) => void;
  onDelete: (id: string) => void;
}

export function ChartBlockEditor({ block, onChange, onDelete }: ChartBlockEditorProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const updateField = <K extends keyof ChartBlock>(field: K, value: ChartBlock[K]) => {
    onChange({ ...block, [field]: value });
  };

  const addDataset = () => {
    const datasets = block.data?.datasets || [];
    updateField("data", {
      labels: block.data?.labels || [],
      datasets: [
        ...datasets,
        {
          label: `Serie ${datasets.length + 1}`,
          data: [],
          color: "#3b82f6",
        },
      ],
    });
  };

  const updateDataset = (index: number, field: "label" | "color", value: string) => {
    const datasets = [...(block.data?.datasets || [])];
    datasets[index] = { ...datasets[index], [field]: value };
    updateField("data", {
      labels: block.data?.labels || [],
      datasets,
    });
  };

  const removeDataset = (index: number) => {
    const datasets = [...(block.data?.datasets || [])];
    datasets.splice(index, 1);
    updateField("data", {
      labels: block.data?.labels || [],
      datasets,
    });
  };

  const selectedQueryInfo = AVAILABLE_QUERIES.charts.find((q) => q.id === block.query?.type);

  return (
    <Card ref={setNodeRef} style={style} className="p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        {/* Drag Handle */}
        <button
          {...attributes}
          {...listeners}
          className="mt-2 cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
        >
          <GripVertical className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="flex-1 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">#{block.orden}</span>
              <span className="text-xs font-semibold text-orange-600">CHART</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setIsExpanded(!isExpanded)}>
              {isExpanded ? "Colapsar" : "Expandir"}
            </Button>
          </div>

          {isExpanded && (
            <>
              {/* Title */}
              <div>
                <Label className="text-xs">Titulo del grafico (opcional)</Label>
                <Input
                  value={block.title || ""}
                  onChange={(e) => updateField("title", e.target.value)}
                  placeholder="Ej: Grafico N 1. Corredor endemico..."
                  className="mt-1"
                />
              </div>

              {/* Chart type */}
              <div>
                <Label className="text-xs">Tipo de grafico</Label>
                <Select
                  value={block.chartType}
                  onValueChange={(value) => updateField("chartType", value as ChartBlock["chartType"])}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="line">Lineas</SelectItem>
                    <SelectItem value="bar">Barras</SelectItem>
                    <SelectItem value="table_data">Tabla de datos</SelectItem>
                    <SelectItem value="corridor">Corredor endemico</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Data source selector */}
              <div>
                <Label className="text-xs">Fuente de datos</Label>
                <div className="flex gap-2 mt-1">
                  <Button
                    variant={block.dataSource === "manual" ? "default" : "outline"}
                    size="sm"
                    onClick={() => updateField("dataSource", "manual")}
                    className="flex-1"
                  >
                    <Edit3 className="h-4 w-4 mr-2" />
                    Manual
                  </Button>
                  <Button
                    variant={block.dataSource === "query" ? "default" : "outline"}
                    size="sm"
                    onClick={() => updateField("dataSource", "query")}
                    className="flex-1"
                  >
                    <Database className="h-4 w-4 mr-2" />
                    Query
                  </Button>
                </div>
              </div>

              {/* Manual data editor */}
              {block.dataSource === "manual" && (
                <div className="space-y-3 border rounded-lg p-3 bg-gray-50">
                  <div>
                    <Label className="text-xs">Etiquetas (eje X)</Label>
                    <Input
                      value={(block.data?.labels || []).join(", ")}
                      onChange={(e) =>
                        updateField("data", {
                          labels: e.target.value.split(",").map((s) => s.trim()),
                          datasets: block.data?.datasets || [],
                        })
                      }
                      placeholder="Ej: Semana 1, Semana 2, Semana 3"
                      className="mt-1 text-xs"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Separadas por comas
                    </p>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <Label className="text-xs">Series de datos</Label>
                      <Button variant="outline" size="sm" onClick={addDataset}>
                        <Plus className="h-3 w-3 mr-1" />
                        Serie
                      </Button>
                    </div>

                    {(block.data?.datasets || []).map((dataset, idx) => (
                      <div key={idx} className="flex gap-2 mb-2">
                        <Input
                          value={dataset.label}
                          onChange={(e) => updateDataset(idx, "label", e.target.value)}
                          placeholder="Nombre de la serie"
                          className="flex-1 text-xs"
                        />
                        <Input
                          type="color"
                          value={dataset.color || "#3b82f6"}
                          onChange={(e) => updateDataset(idx, "color", e.target.value)}
                          className="w-16"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeDataset(idx)}
                          className="px-2"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}

                    <p className="text-xs text-amber-600 mt-2">
                      Los valores de datos se ingresaran al generar el reporte
                    </p>
                  </div>
                </div>
              )}

              {/* Query data selector */}
              {block.dataSource === "query" && (
                <div className="space-y-3 border rounded-lg p-3 bg-blue-50">
                  <div>
                    <Label className="text-xs">Tipo de query</Label>
                    <Select
                      value={block.query?.type || ""}
                      onValueChange={(value) =>
                        updateField("query", {
                          type: value as NonNullable<ChartBlock["query"]>["type"],
                          params: {},
                        })
                      }
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Selecciona una query..." />
                      </SelectTrigger>
                      <SelectContent>
                        {AVAILABLE_QUERIES.charts.map((q) => (
                          <SelectItem key={q.id} value={q.id}>
                            {q.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedQueryInfo && (
                    <div className="text-xs text-muted-foreground">
                      <p className="font-medium">Descripcion:</p>
                      <p>{selectedQueryInfo.descripcion}</p>
                      <p className="font-medium mt-2">Parametros:</p>
                      <ul className="list-disc list-inside">
                        {selectedQueryInfo.params.map((param) => (
                          <li key={param}>{param}</li>
                        ))}
                      </ul>
                      <p className="mt-2 text-amber-600">
                        Los parametros se configuraran al generar el reporte
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Height */}
              <div>
                <Label className="text-xs">Altura (px)</Label>
                <Input
                  type="number"
                  value={block.height || 300}
                  onChange={(e) => updateField("height", parseInt(e.target.value))}
                  className="mt-1"
                />
              </div>

              {/* Footnote */}
              <div>
                <Label className="text-xs">Nota al pie (opcional)</Label>
                <Textarea
                  value={block.footnote || ""}
                  onChange={(e) => updateField("footnote", e.target.value)}
                  placeholder="Ej: Fuente: Laboratorio Provincial"
                  rows={2}
                  className="mt-1 text-xs"
                />
              </div>
            </>
          )}
        </div>

        {/* Delete button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(block.id)}
          className="text-red-500 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
