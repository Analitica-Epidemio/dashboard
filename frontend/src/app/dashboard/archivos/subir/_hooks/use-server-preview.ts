"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { getUploadPreviewUrl, getUploadProcessUrl } from "@/lib/api/config";

export interface SheetPreview {
  name: string;
  columns: string[];
  row_count: number;
  preview_rows: unknown[][];
  is_valid: boolean;
  missing_columns: string[];
}

export interface FilePreviewData {
  upload_id: string;
  filename: string;
  file_size: number;
  sheets: SheetPreview[];
  valid_sheets_count: number;
  total_sheets_count: number;
}

interface ProcessRequest {
  upload_id: string;
  sheet_name: string;
}

interface ProcessResponse {
  job_id: string;
  status: string;
  message: string;
  polling_url: string;
}

/**
 * Upload file and get preview from server
 */
async function uploadForPreview(file: File): Promise<FilePreviewData> {
  console.log('📤 Uploading file for preview:', file.name, file.size);

  const formData = new FormData();
  formData.append("file", file);

  // Get auth token
  const { getSession } = await import('next-auth/react');
  const session = await getSession();

  const url = getUploadPreviewUrl();
  console.log('🌐 Uploading to:', url);

  const response = await fetch(url, {
    method: "POST",
    body: formData,
    headers: {
      ...(session?.accessToken && {
        'Authorization': `Bearer ${session.accessToken}`
      })
    }
  });

  console.log('📡 Response status:', response.status);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('❌ Upload error:', errorText);
    try {
      const error = JSON.parse(errorText);
      throw new Error(error.error?.message || "Error al analizar archivo");
    } catch {
      throw new Error(`Error del servidor (${response.status}): ${errorText}`);
    }
  }

  const result = await response.json();
  console.log('✅ Preview data received:', result);
  return result.data;
}

/**
 * Process selected sheet from previously uploaded file
 */
async function processFromPreview(request: ProcessRequest): Promise<ProcessResponse> {
  const { getSession } = await import('next-auth/react');
  const session = await getSession();

  const response = await fetch(getUploadProcessUrl(), {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      ...(session?.accessToken && {
        'Authorization': `Bearer ${session.accessToken}`
      })
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || "Error al procesar archivo");
  }

  const result = await response.json();
  return result.data;
}

/**
 * Modern server-side preview hook
 *
 * Usage:
 * const { uploadForPreview, processSheet, previewData, isUploading, isProcessing, error } = useServerPreview();
 *
 * // 1. Upload and preview
 * const preview = await uploadForPreview.mutateAsync(file);
 *
 * // 2. User selects sheet, then process
 * const job = await processSheet.mutateAsync({ upload_id: preview.upload_id, sheet_name: selectedSheet });
 */
export function useServerPreview() {
  const [previewData, setPreviewData] = useState<FilePreviewData | null>(null);

  const uploadMutation = useMutation({
    mutationFn: uploadForPreview,
    onSuccess: (data) => {
      setPreviewData(data);
    },
  });

  const processMutation = useMutation({
    mutationFn: processFromPreview,
  });

  const reset = () => {
    setPreviewData(null);
    uploadMutation.reset();
    processMutation.reset();
  };

  return {
    // Upload & preview
    uploadForPreview: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,

    // Process
    processSheet: processMutation.mutateAsync,
    isProcessing: processMutation.isPending,
    processError: processMutation.error,

    // Data
    previewData,

    // Utils
    reset,
  };
}
