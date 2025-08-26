"use client";

import React from "react";
import { useDropzone, FileRejection } from "react-dropzone";

interface FileUploadAreaProps {
  onFileAccepted: (file: File) => void;
  isProcessing: boolean;
  error: string | null;
}

const MAX_SIZE_MB = 50;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export function FileUploadArea({ 
  onFileAccepted, 
  isProcessing, 
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
          border-2 border-dashed rounded-xl p-10 w-96 text-center cursor-pointer transition
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-400"}
          ${isProcessing ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input {...getInputProps()} />
        
        {isProcessing ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-blue-600 font-medium">
              Procesando archivo...
            </p>
          </div>
        ) : isDragActive ? (
          <p className="text-blue-600 font-medium">
            Suelta el archivo aquí...
          </p>
        ) : (
          <p className="text-gray-600">
            Arrastra y suelta un archivo <b>.xlsx</b> aquí (máx {MAX_SIZE_MB} MB), 
            o haz click para seleccionarlo
          </p>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}