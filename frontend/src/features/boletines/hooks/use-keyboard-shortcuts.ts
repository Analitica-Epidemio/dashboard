"use client";

/**
 * Hook para atajos de teclado en el editor de boletines
 *
 * Atajos disponibles:
 * - Cmd/Ctrl + S: Guardar
 * - Cmd/Ctrl + E: Exportar PDF
 */

import { useEffect, useCallback, useRef } from "react";

interface KeyboardShortcutsOptions {
  onSave?: () => void;
  onExport?: () => void;
  enabled?: boolean;
}

export function useKeyboardShortcuts({
  onSave,
  onExport,
  enabled = true,
}: KeyboardShortcutsOptions) {
  const onSaveRef = useRef(onSave);
  const onExportRef = useRef(onExport);

  // Keep refs updated
  useEffect(() => {
    onSaveRef.current = onSave;
    onExportRef.current = onExport;
  }, [onSave, onExport]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      const isMeta = event.metaKey || event.ctrlKey;

      if (isMeta && event.key === "s") {
        event.preventDefault();
        onSaveRef.current?.();
      }

      if (isMeta && event.key === "e") {
        event.preventDefault();
        onExportRef.current?.();
      }
    },
    [enabled]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

/**
 * Format keyboard shortcut for display
 */
export function formatShortcut(key: string): string {
  const isMac = typeof navigator !== "undefined" && /Mac/.test(navigator.userAgent);
  const modifier = isMac ? "⌘" : "Ctrl";
  return `${modifier}+${key.toUpperCase()}`;
}
