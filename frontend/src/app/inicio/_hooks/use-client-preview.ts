"use client";

import { useState, useCallback } from "react";
import * as XLSX from "xlsx";
import { validateSheetColumns, REQUIRED_COLUMNS } from "../constants";

export interface SheetData {
  name: string;
  rows: unknown[][];
  total_rows: number;
  columns: string[];
}

interface UseClientPreviewReturn {
  originalFile: File | null;
  sheets: Record<string, SheetData>;
  selectedSheet: string;
  hasSheets: boolean;
  hasValidSheets: boolean;
  isProcessing: boolean;
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
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const processFile = useCallback(async (file: File) => {
    setIsProcessing(true);
    setError(null);
    setValidationError(null);
    
    try {
      // Leer archivo Excel
      const arrayBuffer = await file.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: "array" });
      
      const allSheetsData: Record<string, SheetData> = {};
      const validSheetsData: Record<string, SheetData> = {};
      
      // Procesar cada hoja
      for (const sheetName of workbook.SheetNames) {
        const worksheet = workbook.Sheets[sheetName];
        
        // Convertir a JSON para obtener los datos
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
          header: 1,
          defval: "",
        });
        
        // Obtener primeras 50 filas para preview
        const previewRows = jsonData.slice(0, 50) as unknown[][];
        
        // Generar nombres de columnas basados en la primera fila
        let columns: string[] = [];
        if (previewRows.length > 0 && previewRows[0]) {
          columns = previewRows[0].map((cell, index) => {
            const cellStr = String(cell || "").trim();
            return cellStr || `Columna ${index + 1}`;
          }) as string[];
        }
        
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
      
      // Verificar si hay hojas válidas
      const validSheetNames = Object.keys(validSheetsData);
      
      if (validSheetNames.length === 0) {
        // No hay hojas válidas - mostrar error de validación
        const totalSheets = Object.keys(allSheetsData).length;
        setValidationError(
          `No se encontraron hojas que cumplan con las ${REQUIRED_COLUMNS.length} columnas requeridas. ` +
          `Se procesaron ${totalSheets} hoja${totalSheets !== 1 ? 's' : ''} pero ninguna tiene el formato epidemiológico correcto.`
        );
        setSheets({});
        setSelectedSheet("");
        setOriginalFile(null);
      } else {
        // Hay hojas válidas - usar solo esas
        setOriginalFile(file);
        setSheets(validSheetsData);
        
        // Auto-seleccionar primera hoja válida
        setSelectedSheet(validSheetNames[0]);
        
        // Mostrar info si se filtraron hojas
        const totalSheets = Object.keys(allSheetsData).length;
        if (validSheetNames.length < totalSheets) {
          console.log(`Se filtraron ${totalSheets - validSheetNames.length} hojas por no cumplir con el formato requerido`);
        }
      }
      
    } catch (err) {
      console.error("Error processing Excel file:", err);
      setError("Error al procesar el archivo Excel");
      setSheets({});
      setSelectedSheet("");
      setOriginalFile(null);
      setValidationError(null);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setOriginalFile(null);
    setSheets({});
    setSelectedSheet("");
    setError(null);
    setValidationError(null);
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
    error,
    validationError,
    processFile,
    setSelectedSheet,
    clearData,
  };
}