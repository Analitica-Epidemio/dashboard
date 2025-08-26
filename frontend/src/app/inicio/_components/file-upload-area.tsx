"use client";

import React from "react";
import { useDropzone, FileRejection } from "react-dropzone";

interface ProgressState {
  step: string;
  current: number;
  total: number;
  percentage: number;
  message: string;
}

interface FileUploadAreaProps {
  onFileAccepted: (file: File) => void;
  isProcessing: boolean;
  progress: ProgressState | null;
  error: string | null;
}

const MAX_SIZE_MB = 50;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export function FileUploadArea({ 
  onFileAccepted, 
  isProcessing, 
  progress,
  error 
}: FileUploadAreaProps) {
  const onDrop = React.useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      if (fileRejections.length > 0) {
        // Los errores ahora se manejan en el componente padre
        return;
      }

      if (acceptedFiles.length > 0) {
        onFileAccepted(acceptedFiles[0]);
      }
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    multiple: false,
    maxSize: MAX_SIZE_BYTES,
    disabled: isProcessing,
  });

  return (
    <div className="flex flex-col items-center justify-center flex-1">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-10 w-96 text-center cursor-pointer transition-colors
          ${isDragActive ? "border-primary bg-muted/50" : "border-border"}
          ${isProcessing ? "opacity-50 cursor-not-allowed" : "hover:border-primary/50 hover:bg-muted/30"}
        `}
      >
        <input {...getInputProps()} />
        
        {isProcessing ? (
          <div className="flex flex-col items-center space-y-4 w-full max-w-md">
            {/* Barra de progreso visual */}
            <div className="w-full bg-muted rounded-full h-2.5">
              <div 
                className="bg-primary h-2.5 rounded-full transition-all duration-300" 
                style={{ width: `${progress?.percentage || 0}%` }}
              ></div>
            </div>
            
            {/* Información del progreso */}
            <div className="text-center space-y-2">
              {progress && (
                <>
                  <p className="text-foreground font-medium">
                    {progress.message}
                  </p>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>{progress.percentage}% completado</span>
                    {progress.total > 0 && progress.step === 'processing' && (
                      <span>{progress.current + 1} de {progress.total} hojas</span>
                    )}
                  </div>
                </>
              )}
            </div>
            
            {/* Spinner */}
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        ) : isDragActive ? (
          <p className="text-primary font-medium">
            Suelta el archivo aquí...
          </p>
        ) : (
          <p className="text-muted-foreground">
            Arrastra y suelta un archivo <b>.xlsx</b> aquí (máx {MAX_SIZE_MB} MB), 
            o haz click para seleccionarlo
          </p>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-destructive text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}