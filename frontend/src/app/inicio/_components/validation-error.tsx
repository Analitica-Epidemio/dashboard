"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { REQUIRED_COLUMNS } from "../constants";

interface ValidationErrorProps {
  message: string;
  onRetry: () => void;
}

export function ValidationError({ message, onRetry }: ValidationErrorProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 max-w-4xl mx-auto">
      {/* Error principal */}
      <div className="mb-6 p-6 bg-orange-50 border border-orange-200 rounded-lg">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-orange-800">
              Archivo no reconocido
            </h3>
            <p className="mt-2 text-sm text-orange-700 leading-relaxed">
              {message}
            </p>
            <p className="mt-3 text-sm text-orange-700">
              <strong>No te preocupes:</strong> Esto significa que tu archivo no coincide con el formato específico del sistema SNVS de epidemiología.
            </p>
          </div>
        </div>
      </div>

      {/* Información simplificada sobre el formato */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg w-full">
        <h4 className="text-sm font-medium text-blue-800 mb-3 flex items-center">
          ¿Qué archivo necesito?
        </h4>
        <div className="text-sm text-blue-700 space-y-2">
          <p>• <strong>Archivos del Sistema SNVS</strong> (Sistema Nacional de Vigilancia de la Salud)</p>
          <p>• Deben contener las <strong>{REQUIRED_COLUMNS.length} columnas epidemiológicas estándar</strong></p>
          <p>• Formato Excel (.xlsx) con datos de casos epidemiológicos</p>
          
          <details className="mt-3">
            <summary className="cursor-pointer text-primary hover:text-primary/80">
              Ver algunas columnas esperadas (click para expandir)
            </summary>
            <div className="mt-2 p-2 bg-card rounded border text-xs space-y-1 max-h-32 overflow-y-auto">
              {REQUIRED_COLUMNS.slice(0, 12).map((column, index) => (
                <div key={index} className="text-muted-foreground">• {column}</div>
              ))}
              <div className="text-muted-foreground/70 italic">... y {REQUIRED_COLUMNS.length - 12} columnas más</div>
            </div>
          </details>
        </div>
      </div>

      {/* Instrucciones */}
      <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg w-full">
        <h4 className="text-sm font-medium text-green-800 mb-3 flex items-center">
          ¿Qué puedo hacer?
        </h4>
        <div className="text-sm text-green-700 space-y-3">
          <div className="flex items-start space-x-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-200 text-green-800 rounded-full flex items-center justify-center text-xs font-bold">1</span>
            <div>
              <p className="font-medium">Verificar que sea un archivo SNVS</p>
              <p className="text-xs text-green-600">El archivo debe provenir del sistema oficial de vigilancia epidemiológica</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-200 text-green-800 rounded-full flex items-center justify-center text-xs font-bold">2</span>
            <div>
              <p className="font-medium">Intentar con otro archivo</p>
              <p className="text-xs text-green-600">Si tienes varios archivos Excel, prueba con uno diferente</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-2">
            <span className="flex-shrink-0 w-6 h-6 bg-green-200 text-green-800 rounded-full flex items-center justify-center text-xs font-bold">3</span>
            <div>
              <p className="font-medium">Contactar al equipo técnico</p>
              <p className="text-xs text-green-600">Si necesitas ayuda con el formato o conversión de datos</p>
            </div>
          </div>
        </div>
      </div>

      {/* Botón para reintentar */}
      <Button 
        onClick={onRetry}
        className="px-8 py-3 text-base font-medium"
        size="lg"
      >
        Intentar con otro archivo
      </Button>
    </div>
  );
}