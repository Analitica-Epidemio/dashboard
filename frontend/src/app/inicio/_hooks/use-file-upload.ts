"use client";

import { useMutation } from "@tanstack/react-query";
import * as XLSX from "xlsx";
import { getUploadSheetUrl } from "@/lib/api/config";

interface SheetUploadResponse {
  upload_id: number;
  filename: string;
  sheet_name: string;
  file_path: string;
  file_size: number;
  total_rows: number;
  columns: string[];
  upload_timestamp: string;
  success: boolean;
  message: string;
}

interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

interface ApiError {
  error: {
    code: string;
    message: string;
    field?: string;
  };
  request_id?: string;
}

interface SheetUploadParams {
  originalFile: File;
  selectedSheetName: string;
  originalFilename: string;
}

async function uploadSelectedSheet(params: SheetUploadParams): Promise<SheetUploadResponse> {
  const { originalFile, selectedSheetName, originalFilename } = params;
  
  // Leer el archivo completo
  const arrayBuffer = await originalFile.arrayBuffer();
  const workbook = XLSX.read(arrayBuffer, { type: "array" });
  
  // Extraer solo la hoja seleccionada
  const worksheet = workbook.Sheets[selectedSheetName];
  if (!worksheet) {
    throw new Error(`Hoja "${selectedSheetName}" no encontrada`);
  }
  
  // Crear un nuevo workbook con solo la hoja seleccionada
  const newWorkbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(newWorkbook, worksheet, selectedSheetName);
  
  // Convertir a buffer
  const buffer = XLSX.write(newWorkbook, { 
    type: 'array', 
    bookType: 'xlsx' 
  });
  
  // Crear blob y formdata
  const blob = new Blob([buffer], { 
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
  });
  
  const formData = new FormData();
  formData.append("file", blob, `${selectedSheetName}.xlsx`);
  formData.append("original_filename", originalFilename);
  formData.append("sheet_name", selectedSheetName);

  // Subir al servidor
  const response = await fetch(getUploadSheetUrl(), {
    method: "POST",
    body: formData,
  });

  const result = await response.json();

  if (!response.ok) {
    const error = result as ApiError;
    throw new Error(error.error.message || "Error al subir hoja");
  }

  const apiResponse = result as ApiResponse<SheetUploadResponse>;
  return apiResponse.data;
}

export function useSheetUpload() {
  return useMutation({
    mutationFn: uploadSelectedSheet,
    onError: (error) => {
      console.error("Error uploading sheet:", error);
    },
  });
}