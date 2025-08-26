"use client";

import React from "react";
import { Button } from "@/components/ui/button";

interface UploadActionsProps {
  selectedSheet: string;
  onContinue: () => void;
  onReset: () => void;
  isUploading?: boolean;
}

export function UploadActions({
  selectedSheet,
  onContinue,
  onReset,
  isUploading = false,
}: UploadActionsProps) {
  return (
    <div className="mt-6 flex justify-between items-center">
      <div>
        <p className="text-sm text-gray-600">
          Hoja seleccionada: <strong>{selectedSheet}</strong>
        </p>
      </div>
      
      <div className="space-x-3">
        <Button
          variant="outline"
          onClick={onReset}
          disabled={isUploading}
        >
          Subir otro archivo
        </Button>
        
        <Button
          onClick={onContinue}
          disabled={!selectedSheet || isUploading}
          className="min-w-[200px]"
        >
          {isUploading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Enviando al servidor...</span>
            </div>
          ) : (
            "Subir hoja seleccionada"
          )}
        </Button>
      </div>
    </div>
  );
}