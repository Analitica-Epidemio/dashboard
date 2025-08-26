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
      <div className="mb-6 p-6 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Formato de archivo incorrecto
            </h3>
            <p className="mt-2 text-sm text-red-700">
              {message}
            </p>
          </div>
        </div>
      </div>

      {/* Información de columnas requeridas */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg w-full">
        <h4 className="text-sm font-medium text-blue-800 mb-3">
          Columnas requeridas para archivos epidemiológicos ({REQUIRED_COLUMNS.length} total):
        </h4>
        <div className="grid grid-cols-3 gap-2 text-xs text-blue-700 max-h-40 overflow-y-auto">
          {REQUIRED_COLUMNS.map((column, index) => (
            <div key={index} className="p-1 bg-white rounded border">
              {column}
            </div>
          ))}
        </div>
      </div>

      {/* Instrucciones */}
      <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg w-full">
        <h4 className="text-sm font-medium text-yellow-800 mb-2">
          ¿Cómo solucionar esto?
        </h4>
        <ul className="text-sm text-yellow-700 space-y-1">
          <li>• Asegúrate de que tu archivo Excel tenga las columnas exactas mostradas arriba</li>
          <li>• Verifica que los nombres de las columnas coincidan exactamente (mayúsculas/minúsculas)</li>
          <li>• Las columnas deben estar en la primera fila de cada hoja</li>
          <li>• Si tienes un archivo con formato diferente, contacta al administrador del sistema</li>
        </ul>
      </div>

      {/* Botón para reintentar */}
      <Button 
        onClick={onRetry}
        className="px-6 py-3"
        size="lg"
      >
        Subir otro archivo
      </Button>
    </div>
  );
}