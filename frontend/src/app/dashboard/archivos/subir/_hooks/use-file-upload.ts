"use client";

import { useMutation } from "@tanstack/react-query";
import * as XLSX from "xlsx";
import { getUploadCsvAsyncUrl } from "@/lib/api/config";
import type { components } from "@/lib/api/types";

// Usar tipos generados automáticamente desde OpenAPI
type AsyncJobResponse = components["schemas"]["AsyncJobResponse"];

// Usar tipos de respuesta generados automáticamente
type SuccessResponse<T> = components["schemas"]["SuccessResponse_AsyncJobResponse_"] & {
  data: T;
};
type ApiError = components["schemas"]["ErrorResponse"];

interface SheetUploadParams {
  originalFile: File;
  selectedSheetName: string;
  originalFilename: string;
}

/**
 * Upload asíncrono moderno con Celery backend.
 * 
 * Returns job ID para tracking con useJobProgress.
 */
async function uploadSelectedSheetAsync(params: SheetUploadParams): Promise<AsyncJobResponse> {
  const { originalFile, selectedSheetName, originalFilename } = params;
  
  // Leer el archivo completo
  const arrayBuffer = await originalFile.arrayBuffer();
  const workbook = XLSX.read(arrayBuffer, { type: "array" });
  
  // Extraer solo la hoja seleccionada
  const worksheet = workbook.Sheets[selectedSheetName];
  if (!worksheet) {
    throw new Error(`Hoja "${selectedSheetName}" no encontrada`);
  }
  
  // Convertir la hoja a CSV - mucho más eficiente
  const csv = XLSX.utils.sheet_to_csv(worksheet, {
    FS: ',',           // Separador de campos
    RS: '\n',          // Separador de filas
    strip: true,       // Quitar espacios innecesarios
    blankrows: false,  // Omitir filas vacías
    skipHidden: true   // Omitir columnas ocultas
  });
  
  // Crear blob CSV - significativamente más pequeño
  const blob = new Blob([csv], { type: 'text/csv; charset=utf-8' });
  
  // Log de conversión para debugging (remover en producción)
  if (process.env.NODE_ENV === 'development') {
    console.log("📊 Conversión a CSV:", {
      original: (originalFile.size / (1024 * 1024)).toFixed(2) + "MB",
      csv: (blob.size / (1024 * 1024)).toFixed(2) + "MB",
      reducción: Math.round((1 - blob.size / originalFile.size) * 100) + "%"
    });
  }
  
  const formData = new FormData();
  formData.append("file", blob, `${selectedSheetName}.csv`);
  formData.append("original_filename", originalFilename);
  formData.append("sheet_name", selectedSheetName);

  // Usar endpoint asíncrono moderno
  const response = await fetch(getUploadCsvAsyncUrl(), {
    method: "POST",
    body: formData,
  });

  const result = await response.json();

  if (!response.ok) {
    const error = result as ApiError;
    throw new Error(error.error.message || "Error al iniciar procesamiento");
  }

  const apiResponse = result as SuccessResponse<AsyncJobResponse>;
  return apiResponse.data;
}

/**
 * Hook moderno para upload asíncrono.
 * 
 * Usage:
 * const upload = useAsyncSheetUpload();
 * const jobProgress = useJobProgress();
 * 
 * const handleUpload = async () => {
 *   const job = await upload.mutateAsync(params);
 *   jobProgress.startPolling(job.job_id);
 * };
 */
export function useAsyncSheetUpload() {
  return useMutation({
    mutationFn: uploadSelectedSheetAsync,
    onError: (error) => {
      console.error("Error uploading sheet:", error);
    },
  });
}