"use client";
import React, {useCallback, useState} from 'react'
import {useDropzone} from 'react-dropzone'

export default function Page() {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const tamañoMaximoMegaBytes = 50;
  const tamañoMaximoBytes = tamañoMaximoMegaBytes * 1024 * 1024;

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: string | any[]) => {
    if (fileRejections.length > 0) {
      const rejection = fileRejections[0];
      if (rejection.errors.some((e: { code: string; }) => e.code === "file-too-large")) {
        setError("El archivo es demasiado grande (máx {tamañoMaximoMegaBytes} MB)");
      } else if (rejection.errors.some((e: { code: string; }) => e.code === "file-invalid-type")) {
        setError("Solo se permiten archivos .xlsx");
      } else {
        setError("Archivo no válido");
      }
      setFiles([]);
      return;
    }

    setError(null);
    setFiles(acceptedFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    multiple: false,
    maxSize: tamañoMaximoBytes, 
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-6">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-10 w-96 text-center cursor-pointer transition ${
          isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-400"
        }`}
      >
        <input {...getInputProps()} />
        {isDragActive ? (
          <p className="text-blue-600 font-medium">Suelta el archivo aquí...</p>
        ) : (
          <p className="text-gray-600">
            Arrastra y suelta un archivo <b>.xlsx</b> aquí (máx {tamañoMaximoMegaBytes} MB), o haz click para seleccionarlo
          </p>
        )}
      </div>

      {error && <p className="text-red-600 mt-4">{error}</p>}

      {files.length > 0 && (
        <div className="mt-6 w-96">
          <h2 className="text-lg font-semibold mb-2">Archivo seleccionado:</h2>
          <ul className="list-disc list-inside">
            {files.map((file) => (
              <li key={file.name} className="text-gray-700">
                {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
