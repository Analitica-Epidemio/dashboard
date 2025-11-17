"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, Plus, X, Database, Edit3 } from "lucide-react";
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
import { AVAILABLE_QUERIES, type TableBlock } from "./types";

interface TableBlockEditorProps {
  block: TableBlock;
  onChange: (block: TableBlock) => void;
  onDelete: (id: string) => void;
}

export function TableBlockEditor({ block, onChange, onDelete }: TableBlockEditorProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: block.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const updateField = <K extends keyof TableBlock>(field: K, value: TableBlock[K]) => {
    onChange({ ...block, [field]: value });
  };

  const addColumn = () => {
    const headers = block.headers || [];
    updateField("headers", [...headers, `Columna ${headers.length + 1}`]);
  };

  const updateHeader = (index: number, value: string) => {
    const headers = [...(block.headers || [])];
    headers[index] = value;
    updateField("headers", headers);
  };

  const removeColumn = (index: number) => {
    const headers = [...(block.headers || [])];
    headers.splice(index, 1);
    const rows = (block.rows || []).map((row) => {
      const newRow = [...row];
      newRow.splice(index, 1);
      return newRow;
    });
    updateField("headers", headers);
    updateField("rows", rows);
  };

  const addRow = () => {
    const rows = block.rows || [];
    const newRow = Array((block.headers || []).length).fill("");
    updateField("rows", [...rows, newRow]);
  };

  const updateCell = (rowIndex: number, colIndex: number, value: string) => {
    const rows = [...(block.rows || [])];
    rows[rowIndex][colIndex] = value;
    updateField("rows", rows);
  };

  const removeRow = (index: number) => {
    const rows = [...(block.rows || [])];
    rows.splice(index, 1);
    updateField("rows", rows);
  };

  const selectedQueryInfo = AVAILABLE_QUERIES.tables.find((q) => q.id === block.query?.type);

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
              <span className="text-xs font-semibold text-purple-600">TABLE</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? "Colapsar" : "Expandir"}
            </Button>
          </div>

          {isExpanded && (
            <>
              {/* Title */}
              <div>
                <Label className="text-xs">Titulo de la tabla (opcional)</Label>
                <Input
                  value={block.title || ""}
                  onChange={(e) => updateField("title", e.target.value)}
                  placeholder="Ej: Tabla N 1. Casos confirmados..."
                  className="mt-1"
                />
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
                <div className="space-y-2 border rounded-lg p-3 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Columnas</Label>
                    <Button variant="outline" size="sm" onClick={addColumn}>
                      <Plus className="h-3 w-3 mr-1" />
                      Columna
                    </Button>
                  </div>

                  {/* Headers */}
                  <div className="flex gap-2">
                    {(block.headers || []).map((header, idx) => (
                      <div key={idx} className="flex-1 flex gap-1">
                        <Input
                          value={header}
                          onChange={(e) => updateHeader(idx, e.target.value)}
                          placeholder="Nombre"
                          className="text-xs"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeColumn(idx)}
                          className="px-2"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  {/* Rows */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs">Filas</Label>
                      <Button variant="outline" size="sm" onClick={addRow}>
                        <Plus className="h-3 w-3 mr-1" />
                        Fila
                      </Button>
                    </div>

                    {(block.rows || []).map((row, rowIdx) => (
                      <div key={rowIdx} className="flex gap-2">
                        {row.map((cell, colIdx) => (
                          <Input
                            key={colIdx}
                            value={cell}
                            onChange={(e) => updateCell(rowIdx, colIdx, e.target.value)}
                            placeholder="-"
                            className="flex-1 text-xs"
                          />
                        ))}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeRow(rowIdx)}
                          className="px-2"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}

                    {(!block.rows || block.rows.length === 0) && (
                      <p className="text-xs text-muted-foreground text-center py-4">
                        Agrega filas para comenzar
                      </p>
                    )}
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
                          type: value as NonNullable<TableBlock["query"]>["type"],
                          params: {},
                        })
                      }
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Selecciona una query..." />
                      </SelectTrigger>
                      <SelectContent>
                        {AVAILABLE_QUERIES.tables.map((q) => (
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

              {/* Footnote */}
              <div>
                <Label className="text-xs">Nota al pie (opcional)</Label>
                <Textarea
                  value={block.footnote || ""}
                  onChange={(e) => updateField("footnote", e.target.value)}
                  placeholder="Ej: Fuente: SNVS 2.0"
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
