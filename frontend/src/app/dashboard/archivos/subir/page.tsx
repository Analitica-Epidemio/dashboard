"use client";

import React, { useState, useCallback } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/features/layout/components";
import { ArrowLeft, FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";

// Modern components
import { ModernFileUpload } from "./_components/modern-file-upload";
import { ModernSheetPreview } from "./_components/modern-sheet-preview";
import { UploadProgress } from "./_components/upload-progress";
import { UploadSuccess } from "./_components/upload-success";

// Hooks
import { useServerPreview } from "./_hooks/use-server-preview";
import { useJobProgress } from "./_hooks/use-job-progress";

export default function ModernUploadPage() {
  const {
    uploadForPreview,
    isUploading,
    uploadError,
    processSheet,
    isProcessing,
    processError,
    previewData,
    reset,
  } = useServerPreview();

  const { startPolling } = useJobProgress();

  const [selectedSheet, setSelectedSheet] = useState<string | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<{
    sheetName: string;
    totalRows: number;
  } | null>(null);

  // Handle file selection
  const handleFileSelected = useCallback(
    async (file: File) => {
      console.log('📁 File selected:', file.name, file.type, file.size);
      try {
        console.log('⏳ Starting upload...');
        const preview = await uploadForPreview(file);
        console.log('✅ Upload complete, preview:', preview);

        // Auto-select first valid sheet
        const validSheets = preview.sheets.filter((s) => s.is_valid);
        console.log('📊 Valid sheets:', validSheets.length);
        if (validSheets.length > 0) {
          setSelectedSheet(validSheets[0].name);
          console.log('✓ Auto-selected sheet:', validSheets[0].name);
        }
      } catch (error) {
        console.error("❌ Error uploading file:", error);
      }
    },
    [uploadForPreview]
  );

  // Handle processing
  const handleProcess = useCallback(async () => {
    if (!previewData || !selectedSheet) return;

    try {
      const result = await processSheet({
        upload_id: previewData.upload_id,
        sheet_name: selectedSheet,
      });

      // Iniciar job con el ID real
      setCurrentJobId(result.job_id);
      startPolling(result.job_id);
    } catch (error) {
      console.error("Error processing sheet:", error);
      setCurrentJobId(null);
    }
  }, [previewData, selectedSheet, processSheet, startPolling]);

  // Handle job completion
  const handleJobComplete = useCallback(
    (resultData: { total_rows?: number }) => {
      if (resultData.total_rows && selectedSheet) {
        setUploadSuccess({
          sheetName: selectedSheet,
          totalRows: resultData.total_rows,
        });
      }
      setCurrentJobId(null);
    },
    [selectedSheet]
  );

  // Handle job error
  const handleJobError = useCallback((error: string) => {
    console.error("Job error:", error);
    setCurrentJobId(null);
  }, []);

  // Reset everything
  const handleReset = useCallback(() => {
    reset();
    setSelectedSheet(null);
    setCurrentJobId(null);
    setUploadSuccess(null);
  }, [reset]);

  // Determine current view
  const currentView = uploadSuccess
    ? "success"
    : currentJobId
    ? "processing"
    : previewData
    ? "preview"
    : "upload";

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
        <div className="flex flex-col min-h-screen overflow-y-auto bg-muted">
          <div className="flex-1 w-full mx-auto px-6 py-8 max-w-7xl">
            {/* Header */}
            <div className="mb-12">
              <div className="flex items-center justify-between mb-8">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <FileUp className="w-5 h-5 text-muted-foreground" />
                    <h1 className="text-2xl font-semibold">
                      Subir archivo
                    </h1>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {currentView === "upload" && "Sube tu archivo Excel o CSV para empezar"}
                    {currentView === "preview" && "Revisa y selecciona la hoja que deseas procesar"}
                    {currentView === "processing" && "Analizando y guardando datos en la base de datos"}
                    {currentView === "success" && "Archivo procesado exitosamente"}
                  </p>
                </div>

                {/* Back button si está en preview */}
                {currentView === "preview" && !isProcessing && (
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    size="sm"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Subir otro
                  </Button>
                )}
              </div>

              {/* Progress steps - más discretos */}
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className={currentView === "upload" ? "text-foreground font-medium" : ""}>
                  1. Subir
                </span>
                <span>→</span>
                <span className={currentView === "preview" ? "text-foreground font-medium" : ""}>
                  2. Seleccionar
                </span>
                <span>→</span>
                <span className={currentView === "processing" || currentView === "success" ? "text-foreground font-medium" : ""}>
                  3. Procesar
                </span>
              </div>
            </div>

            {/* Main content */}
            <div>
              {currentView === "upload" && (
                <ModernFileUpload
                  onFileSelected={handleFileSelected}
                  isUploading={isUploading}
                  error={uploadError?.message}
                />
              )}

              {currentView === "preview" && previewData && (
                <ModernSheetPreview
                  sheets={previewData.sheets}
                  selectedSheet={selectedSheet}
                  onSheetSelect={setSelectedSheet}
                  onProcess={handleProcess}
                  onCancel={handleReset}
                  isProcessing={isProcessing}
                  filename={previewData.filename}
                  fileSize={previewData.file_size}
                />
              )}

              {currentView === "processing" && currentJobId && (
                <UploadProgress
                  jobId={currentJobId}
                  onComplete={handleJobComplete}
                  onError={handleJobError}
                />
              )}

              {currentView === "success" && uploadSuccess && (
                <UploadSuccess
                  sheetName={uploadSuccess.sheetName}
                  totalRows={uploadSuccess.totalRows}
                  onUploadAnother={handleReset}
                />
              )}
            </div>

            {/* Error display */}
            {(uploadError || processError) && currentView === "upload" && (
              <div className="mt-6 p-3 bg-background border border-destructive rounded-lg max-w-2xl mx-auto">
                <p className="text-sm text-destructive">
                  {uploadError?.message || processError?.message}
                </p>
              </div>
            )}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
