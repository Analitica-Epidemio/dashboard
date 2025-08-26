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
        >
          {isUploading ? "Subiendo..." : "Subir hoja seleccionada"}
        </Button>
      </div>
    </div>
  );
}