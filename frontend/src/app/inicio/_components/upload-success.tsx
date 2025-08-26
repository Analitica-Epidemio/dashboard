"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { CheckCircle, FileText, RotateCcw } from "lucide-react";

interface UploadSuccessProps {
  sheetName: string;
  totalRows: number;
  onUploadAnother: () => void;
  onViewDashboard?: () => void;
}

export function UploadSuccess({ 
  sheetName, 
  totalRows, 
  onUploadAnother,
  onViewDashboard 
}: UploadSuccessProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 max-w-2xl mx-auto">
      {/* Ícono de éxito */}
      <div className="mb-6 flex flex-col items-center">
        <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 text-center">
          ¡Datos subidos correctamente!
        </h2>
      </div>

      {/* Información del upload */}
      <div className="mb-8 p-6 bg-muted/50 border border-border rounded-lg w-full">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-foreground">Hoja procesada:</span>
            <span className="text-sm text-muted-foreground font-mono">{sheetName}</span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-foreground">Casos epidemiológicos:</span>
            <span className="text-sm text-foreground font-bold">
              {totalRows.toLocaleString()} filas
            </span>
          </div>
          
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground">
              Los datos han sido validados y están listos para su análisis en el dashboard.
            </p>
          </div>
        </div>
      </div>

      {/* Acciones disponibles */}
      <div className="w-full space-y-4">
        <div className="text-center mb-4">
          <p className="text-muted-foreground text-sm">
            ¿Qué te gustaría hacer ahora?
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Botón para ver dashboard */}
          {onViewDashboard && (
            <Button
              onClick={onViewDashboard}
              className="flex items-center justify-center space-x-2 py-3"
              size="lg"
            >
              <FileText className="w-5 h-5" />
              <span>Ver Dashboard</span>
            </Button>
          )}
          
          {/* Botón para subir otro archivo */}
          <Button
            onClick={onUploadAnother}
            variant="outline"
            className="flex items-center justify-center space-x-2 py-3"
            size="lg"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Subir otro archivo</span>
          </Button>
        </div>
      </div>

      {/* Información adicional */}
      <div className="mt-8 p-4 bg-muted/30 rounded-lg w-full">
        <p className="text-xs text-muted-foreground text-center">
          Los datos subidos se han integrado al sistema de análisis epidemiológico.
          Puedes encontrarlos en el dashboard principal o continuar subiendo más archivos.
        </p>
      </div>
    </div>
  );
}