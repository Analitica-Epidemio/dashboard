"use client";

import React, { useState } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

// Components
import { FileUploadArea } from "./_components/file-upload-area";
import { SheetSelector } from "./_components/sheet-selector";
import { DataTableSheet } from "./_components/data-table-sheet";
import { UploadActions } from "./_components/upload-actions";
import { ValidationError } from "./_components/validation-error";

// Hooks
import { useSheetUpload } from "./_hooks/use-file-upload";
import { useClientPreview } from "./_hooks/use-client-preview";

export default function Page() {
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  
  // Hook for client-side preview
  const {
    originalFile,
    sheets,
    selectedSheet,
    hasValidSheets,
    isProcessing,
    error,
    validationError,
    processFile,
    setSelectedSheet,
    clearData,
  } = useClientPreview();

  // Hook for uploading selected sheet
  const sheetUploadMutation = useSheetUpload();

  const handleFileAccepted = async (file: File) => {
    setUploadSuccess(null);
    await processFile(file);
  };

  const handleContinue = async () => {
    if (!originalFile || !selectedSheet) {
      return;
    }

    try {
      const result = await sheetUploadMutation.mutateAsync({
        originalFile,
        selectedSheetName: selectedSheet,
        originalFilename: originalFile.name,
      });

      setUploadSuccess(
        `¡Éxito! Hoja "${result.sheet_name}" subida con ${result.total_rows} filas procesadas.`
      );
      
      console.log("Upload exitoso:", result);
      
      // Opcional: limpiar después del éxito
      // clearData();
      
    } catch (err) {
      console.error("Error al subir hoja:", err);
    }
  };

  const handleReset = () => {
    clearData();
    setUploadSuccess(null);
    sheetUploadMutation.reset();
  };

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <div className="flex flex-col items-center min-h-screen bg-gray-100 p-6">
          {/* Mensaje de éxito */}
          {uploadSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 max-w-2xl">
              <p className="font-medium">{uploadSuccess}</p>
            </div>
          )}

          {/* Mostrar error de validación si no hay hojas válidas */}
          {validationError ? (
            <ValidationError
              message={validationError}
              onRetry={handleReset}
            />
          ) : !hasValidSheets ? (
            <FileUploadArea
              onFileAccepted={handleFileAccepted}
              isProcessing={isProcessing}
              error={error}
            />
          ) : (
            <SheetSelector
              sheets={sheets}
              selectedSheet={selectedSheet}
              onSheetChange={setSelectedSheet}
            >
              {(sheet) => <DataTableSheet sheet={sheet} />}
            </SheetSelector>
          )}

          {hasValidSheets && (
            <UploadActions
              selectedSheet={selectedSheet}
              onContinue={handleContinue}
              onReset={handleReset}
              isUploading={sheetUploadMutation.isPending}
            />
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
