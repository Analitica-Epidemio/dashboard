"use client";

import React, { useCallback, useState } from "react";
import { Upload, FileSpreadsheet, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ModernFileUploadProps {
  onFileSelected: (file: File) => void;
  isUploading: boolean;
  error?: string | null;
}

export function ModernFileUpload({ onFileSelected, isUploading, error }: ModernFileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        const file = files[0];
        setSelectedFileName(file.name);
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        setSelectedFileName(file.name);
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "w-full max-w-2xl mx-auto",
        "border-2 border-dashed rounded-lg bg-background",
        "transition-colors",
        isDragging && "border-primary",
        error && "border-destructive bg-destructive/5",
        isUploading && "border-primary/50",
        !isDragging && !error && !isUploading && "border-muted-foreground/25 hover:border-muted-foreground/50"
      )}
    >
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept=".xlsx,.xls,.csv"
        onChange={handleFileInput}
        disabled={isUploading}
      />

      <label
        htmlFor="file-upload"
        className={cn(
          "flex flex-col items-center justify-center px-6 py-12 cursor-pointer",
          isUploading && "cursor-wait"
        )}
      >
          {/* Icon */}
          <div className="mb-4">
            {isUploading ? (
              <Loader2 className="w-8 h-8 text-muted-foreground animate-spin" />
            ) : error ? (
              <AlertCircle className="w-8 h-8 text-destructive" />
            ) : (
              <FileSpreadsheet className={cn(
                "w-8 h-8",
                isDragging ? "text-primary" : "text-muted-foreground"
              )} />
            )}
          </div>

          {/* Text */}
          <div className="text-center space-y-1">
            {error ? (
              <>
                <p className="text-sm font-medium text-destructive">Error al procesar archivo</p>
                <p className="text-xs text-muted-foreground max-w-md">{error}</p>
              </>
            ) : isUploading ? (
              <>
                <p className="text-sm font-medium">Analizando archivo...</p>
                {selectedFileName && (
                  <p className="text-xs text-muted-foreground font-mono">{selectedFileName}</p>
                )}
              </>
            ) : (
              <>
                <p className="text-sm font-medium">
                  {isDragging ? "Suelta el archivo aquí" : "Arrastra tu archivo o haz clic para seleccionar"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Excel (.xlsx, .xls) o CSV (.csv)
                </p>
              </>
            )}
          </div>
        </label>
    </div>
  );
}
