"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, FileText, Table } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { SheetPreview } from "../_hooks/use-server-preview";

interface ModernSheetPreviewProps {
  sheets: SheetPreview[];
  selectedSheet: string | null;
  onSheetSelect: (sheetName: string) => void;
  onProcess: () => void;
  onCancel: () => void;
  isProcessing: boolean;
  filename: string;
  fileSize: number;
}

export function ModernSheetPreview({
  sheets,
  selectedSheet,
  onSheetSelect,
  onProcess,
  onCancel,
  isProcessing,
  filename,
  fileSize,
}: ModernSheetPreviewProps) {
  const validSheets = sheets.filter((s) => s.is_valid);
  const invalidSheets = sheets.filter((s) => !s.is_valid);
  const selectedSheetData = sheets.find((s) => s.name === selectedSheet);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header con info del archivo */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-muted-foreground">
          <FileText className="w-4 h-4" />
          <span className="text-sm">{filename}</span>
          <span className="text-xs">•</span>
          <span className="text-xs">{formatFileSize(fileSize)}</span>
        </div>
        <div>
          <h2 className="text-2xl font-semibold">Selecciona una hoja</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {validSheets.length > 0 ? (
              <>
                {validSheets.length} hoja{validSheets.length !== 1 && "s"} con formato válido
              </>
            ) : (
              "No se encontraron hojas con formato válido"
            )}
          </p>
        </div>
      </div>

      {/* Hojas válidas */}
      {validSheets.length > 0 && (
        <div className="space-y-3">
          {validSheets.map((sheet) => {
            const isSelected = selectedSheet === sheet.name;

            return (
              <Card
                key={sheet.name}
                className={cn(
                  "cursor-pointer transition-colors",
                  isSelected ? "bg-background border-primary" : "hover:bg-background/50"
                )}
                onClick={() => onSheetSelect(sheet.name)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Table className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <CardTitle className="text-base">{sheet.name}</CardTitle>
                        <CardDescription className="text-xs">
                          {sheet.row_count.toLocaleString()} filas • {sheet.columns.length} columnas
                        </CardDescription>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs border-green-200 text-green-700">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Válida
                    </Badge>
                  </div>
                </CardHeader>

                {/* Vista previa de datos cuando está seleccionada */}
                {isSelected && sheet.preview_rows.length > 0 && (
                  <CardContent className="pt-0">
                    <div className="border rounded-md overflow-hidden bg-background">
                      <div className="overflow-x-auto overflow-y-auto max-h-[500px]">
                        <table className="w-full text-xs">
                          <thead className="bg-muted sticky top-0">
                            <tr>
                              {sheet.columns.map((col, idx) => (
                                <th
                                  key={idx}
                                  className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap"
                                >
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {sheet.preview_rows.map((row, rowIdx) => (
                              <tr key={rowIdx} className="hover:bg-muted/50">
                                {(row as unknown[]).map((cell, cellIdx) => (
                                  <td key={cellIdx} className="px-3 py-2 text-muted-foreground">
                                    <div className="max-w-[200px] truncate">
                                      {String(cell || "")}
                                    </div>
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {sheet.preview_rows.length < sheet.row_count && (
                        <div className="bg-muted px-3 py-2 text-xs text-muted-foreground text-center border-t">
                          Mostrando {sheet.preview_rows.length} de {sheet.row_count.toLocaleString()} filas
                        </div>
                      )}
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Hojas inválidas */}
      {invalidSheets.length > 0 && (
        <details className="group">
          <summary className="flex items-center gap-2 cursor-pointer text-sm text-muted-foreground hover:text-foreground">
            <AlertTriangle className="w-4 h-4" />
            <span>
              {invalidSheets.length} hoja{invalidSheets.length !== 1 && "s"} sin formato válido
            </span>
          </summary>
          <div className="mt-3 space-y-2">
            {invalidSheets.map((sheet) => (
              <Card key={sheet.name} className="bg-background/50">
                <CardHeader className="pb-3">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-sm">{sheet.name}</CardTitle>
                      <CardDescription className="text-xs mt-1">
                        Faltan columnas: {sheet.missing_columns.join(", ")}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        </details>
      )}

      {/* Acciones */}
      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="ghost" onClick={onCancel} disabled={isProcessing}>
          Cancelar
        </Button>
        <Button
          onClick={onProcess}
          disabled={!selectedSheet || isProcessing}
          className="min-w-[180px]"
        >
          {isProcessing ? (
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              <span>Procesando...</span>
            </div>
          ) : (
            <>Procesar archivo</>
          )}
        </Button>
      </div>
    </div>
  );
}
