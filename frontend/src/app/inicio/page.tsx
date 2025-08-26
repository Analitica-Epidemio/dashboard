"use client";

import React, { useState, useCallback } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

// Components
import { FileUploadArea } from "./_components/file-upload-area";
import { SheetSelector } from "./_components/sheet-selector";
import { DataTableSheet } from "./_components/data-table-sheet";
import { UploadActions } from "./_components/upload-actions";
import { ValidationError } from "./_components/validation-error";
import { UploadSteps } from "./_components/upload-steps";
import { UploadSuccess } from "./_components/upload-success";
import { UploadProgress } from "./_components/upload-progress";

// Hooks
import { useAsyncSheetUpload } from "./_hooks/use-file-upload";
import { useClientPreview } from "./_hooks/use-client-preview";
import { useJobProgress } from "./_hooks/use-job-progress";

interface UploadSuccessData {
  sheetName: string;
  totalRows: number;
  message: string;
}

export default function Page() {
  const [uploadSuccess, setUploadSuccess] = useState<UploadSuccessData | null>(null);
  
  // Hook for client-side preview
  const {
    originalFile,
    sheets,
    selectedSheet,
    hasValidSheets,
    isProcessing,
    progress,
    error,
    validationError,
    processFile,
    setSelectedSheet,
    clearData,
  } = useClientPreview();

  // Hook for uploading selected sheet
  const sheetUploadMutation = useAsyncSheetUpload();
  
  // Hook for job progress tracking
  const { 
    startPolling
  } = useJobProgress();
  
  // State for current job ID
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  // Handler para cuando el job se completa exitosamente
  const handleJobComplete = useCallback((resultData: { total_rows?: number; columns?: string[]; file_path?: string }) => {
    if (resultData.total_rows && selectedSheet) {
      setUploadSuccess({
        sheetName: selectedSheet,
        totalRows: resultData.total_rows,
        message: `¡Éxito! Hoja "${selectedSheet}" procesada con ${resultData.total_rows.toLocaleString()} filas.`
      });
    }
    setCurrentJobId(null);
  }, [selectedSheet]);

  const handleFileAccepted = useCallback(async (file: File) => {
    setUploadSuccess(null);
    await processFile(file);
  }, [processFile]);

  const handleContinue = async () => {
    if (!originalFile || !selectedSheet) {
      return;
    }

    try {
      console.log(`Iniciando upload de la hoja "${selectedSheet}"...`);
      
      const result = await sheetUploadMutation.mutateAsync({
        originalFile,
        selectedSheetName: selectedSheet,
        originalFilename: originalFile.name,
      });

      // Iniciar tracking del job
      setCurrentJobId(result.job_id);
      startPolling(result.job_id);
      
      console.log("Job iniciado:", result);
      
    } catch (err) {
      console.error("Error al subir hoja:", err);
      // El error se maneja automáticamente por el mutation
    }
  };

  const handleReset = useCallback(() => {
    clearData();
    setUploadSuccess(null);
    sheetUploadMutation.reset();
  }, [clearData, sheetUploadMutation]);

  // Funciones para el componente de éxito
  const handleUploadAnother = useCallback(() => {
    handleReset();
  }, [handleReset]);

  const handleViewDashboard = useCallback(() => {
    // Para el componente de success
    console.log("🚀 Navegando al dashboard...");
    alert("🚧 Dashboard en desarrollo. Los datos se actualizarán automáticamente cuando esté listo.");
  }, []);

  // Determinar paso actual para el breadcrumb
  const getCurrentStep = useCallback((): 'upload' | 'preview' | 'processing' => {
    if (currentJobId || uploadSuccess) return 'processing';
    if (hasValidSheets) return 'preview';
    return 'upload';
  }, [currentJobId, uploadSuccess, hasValidSheets]);

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
        <div className="flex flex-col min-h-screen bg-background">
          <div className="flex-1 w-full max-w-6xl mx-auto px-6 py-8">
          {/* Breadcrumb de pasos */}
          <UploadSteps currentStep={getCurrentStep()} />

          {/* Flujo principal condicional */}
          {uploadSuccess ? (
            <UploadSuccess
              sheetName={uploadSuccess.sheetName}
              totalRows={uploadSuccess.totalRows}
              onUploadAnother={handleUploadAnother}
              onViewDashboard={handleViewDashboard}
            />
          ) : currentJobId ? (
            /* Mostrar progreso cuando hay un job activo */
            <UploadProgress
              jobId={currentJobId}
              onComplete={handleJobComplete}
              onError={(error) => {
                console.error("Job error:", error);
                setCurrentJobId(null);
              }}
              dashboardHref="/dashboard"
            />
          ) : validationError ? (
            <ValidationError
              message={validationError}
              onRetry={handleReset}
            />
          ) : !hasValidSheets ? (
            <FileUploadArea
              onFileAccepted={handleFileAccepted}
              isProcessing={isProcessing}
              progress={progress}
              error={error}
            />
          ) : (
            <>
              <SheetSelector
                sheets={sheets}
                selectedSheet={selectedSheet}
                onSheetChange={setSelectedSheet}
              >
                {(sheet) => <DataTableSheet sheet={sheet} />}
              </SheetSelector>
              
              <UploadActions
                selectedSheet={selectedSheet}
                onContinue={handleContinue}
                onReset={handleReset}
                isUploading={sheetUploadMutation.isPending}
              />
            </>
          )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
