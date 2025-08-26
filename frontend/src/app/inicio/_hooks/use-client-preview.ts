"use client";

import { useState, useCallback } from "react";
import * as XLSX from "xlsx";
import { validateSheetColumns } from "../constants";

export interface SheetData {
  name: string;
  rows: unknown[][];
  total_rows: number;
  columns: string[];
}

interface ProgressState {
  step: string;
  current: number;
  total: number;
  percentage: number;
  message: string;
}

interface UseClientPreviewReturn {
  originalFile: File | null;
  sheets: Record<string, SheetData>;
  selectedSheet: string;
  hasSheets: boolean;
  hasValidSheets: boolean;
  isProcessing: boolean;
  progress: ProgressState | null;
  error: string | null;
  validationError: string | null;
  processFile: (file: File) => Promise<void>;
  setSelectedSheet: (sheet: string) => void;
  clearData: () => void;
}

export function useClientPreview(): UseClientPreviewReturn {
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [sheets, setSheets] = useState<Record<string, SheetData>>({});
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const processFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    setError(null);
    setValidationError(null);
    setProgress(null);
    
    const updateProgress = (step: string, current: number, total: number, message: string) => {
      const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
      setProgress({ step, current, total, percentage, message });
    };
    
    try {
      // Paso 1: Leer archivo
      updateProgress('reading', 0, 100, `Leyendo archivo... (${(file.size / (1024 * 1024)).toFixed(1)} MB)`);
      
      await new Promise(resolve => setTimeout(resolve, 50)); // Dar tiempo para mostrar UI
      
      const arrayBuffer = await file.arrayBuffer();
      updateProgress('reading', 100, 100, 'Archivo leído completamente');
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Paso 2: Parsear Excel
      updateProgress('parsing', 0, 100, 'Analizando estructura Excel...');
      const workbook = XLSX.read(arrayBuffer, { type: "array" });
      
      updateProgress('parsing', 50, 100, `Encontradas ${workbook.SheetNames.length} hojas`);
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const allSheetsData: Record<string, SheetData> = {};
      const validSheetsData: Record<string, SheetData> = {};
      const totalSheets = workbook.SheetNames.length;
      
      // Paso 3: Procesar cada hoja
      for (let i = 0; i < workbook.SheetNames.length; i++) {
        const sheetName = workbook.SheetNames[i];
        
        updateProgress(
          'processing', 
          i, 
          totalSheets, 
          `Procesando hoja "${sheetName}"... (${i + 1} de ${totalSheets})`
        );
        
        await new Promise(resolve => setTimeout(resolve, 50)); // No bloquear UI
        
        const worksheet = workbook.Sheets[sheetName];
        
        // Convertir a JSON para obtener los datos
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          header: 1,
          defval: "",
        });
        
        // Si la hoja es muy grande, informar progreso durante conversión
        if (jsonData.length > 1000) {
          updateProgress(
            'processing', 
            i, 
            totalSheets, 
            `Procesando ${jsonData.length} filas de "${sheetName}"...`
          );
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // Generar nombres de columnas basados en la primera fila
        let columns: string[] = [];
        if (jsonData.length > 0 && Array.isArray(jsonData[0])) {
          columns = (jsonData[0] as unknown[]).map((cell: unknown, index: number) => {
            const cellStr = String(cell || "").trim();
            return cellStr || `Columna ${index + 1}`;
          });
        }
        
        // Obtener filas de datos (excluyendo la primera que son headers)
        // Tomar desde la fila 1 hasta la 50 (máximo 49 filas de datos)
        const previewRows = jsonData.slice(1, 50) as unknown[][];
        
        const sheetData = {
          name: sheetName,
          rows: previewRows,
          total_rows: jsonData.length,
          columns,
        };
        
        allSheetsData[sheetName] = sheetData;
        
        // Validar si la hoja tiene todas las columnas requeridas
        const validation = validateSheetColumns(columns);
        if (validation.isValid) {
          validSheetsData[sheetName] = sheetData;
        }
      }
      
      // Paso 4: Validación final
      updateProgress('validating', 0, 100, 'Validando hojas procesadas...');
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const validSheetNames = Object.keys(validSheetsData);
      const totalSheetsCount = Object.keys(allSheetsData).length;
      
      if (validSheetNames.length === 0) {
        // No hay hojas válidas - mostrar error de validación más amigable
        setValidationError(
          `Este archivo no tiene el formato epidemiológico esperado. Se revisaron ${totalSheetsCount} hoja${totalSheetsCount !== 1 ? 's' : ''} pero no se encontró el formato del sistema SNVS.`
        );
        setSheets({});
        setSelectedSheet("");
        setOriginalFile(null);
      } else {
        // Hay hojas válidas
        updateProgress('validating', 100, 100, 
          `✓ ${validSheetNames.length} hoja${validSheetNames.length !== 1 ? 's válidas encontradas' : ' válida encontrada'}`
        );
        
        await new Promise(resolve => setTimeout(resolve, 200)); // Mostrar éxito un momento
        
        setOriginalFile(file);
        setSheets(validSheetsData);
        setSelectedSheet(validSheetNames[0]);
        
        // Log si se filtraron hojas
        if (validSheetNames.length < totalSheetsCount) {
          console.log(`Se procesaron ${validSheetNames.length} de ${totalSheetsCount} hojas (las demás no tenían el formato correcto)`);
        }
      }
      
      // El arrayBuffer se limpiará automáticamente por el garbage collector
      
    } catch (err) {
      console.error("Error processing Excel file:", err);
      setError(
        err instanceof Error 
          ? `Error al procesar el archivo: ${err.message}` 
          : "No se pudo procesar el archivo Excel. Verifique que sea un archivo válido."
      );
      setSheets({});
      setSelectedSheet("");
      setOriginalFile(null);
      setValidationError(null);
    } finally {
      setIsProcessing(false);
      setProgress(null);
    }
  }, []);

  const clearData = useCallback(() => {
    setOriginalFile(null);
    setSheets({});
    setSelectedSheet("");
    setError(null);
    setValidationError(null);
    setProgress(null);
    setIsProcessing(false);
  }, []);

  const hasSheets = Object.keys(sheets).length > 0;
  const hasValidSheets = hasSheets; // Si hay sheets, ya fueron filtradas y son válidas

  return {
    originalFile,
    sheets,
    selectedSheet,
    hasSheets,
    hasValidSheets,
    isProcessing,
    progress,
    error,
    validationError,
    processFile,
    setSelectedSheet,
    clearData,
  };
}