"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

export interface SelectedBlockData {
  blockId: string;
  queryType: string;
  /** Specific block type for config panel (e.g., 'curva_loop', 'curva_comparar_eventos') */
  blockType: string;
  queryParams: Record<string, unknown>;
  config: Record<string, unknown>;
  /** Whether this block is inside the event loop template */
  isInEventLoop: boolean;
  // Function to update the block's attributes in the editor
  updateAttributes: (attrs: Record<string, unknown>) => void;
}

interface SelectedBlockContextValue {
  selectedBlock: SelectedBlockData | null;
  selectBlock: (block: SelectedBlockData) => void;
  clearSelection: () => void;
}

const SelectedBlockContext = createContext<SelectedBlockContextValue | null>(null);

export function SelectedBlockProvider({ children }: { children: ReactNode }) {
  const [selectedBlock, setSelectedBlock] = useState<SelectedBlockData | null>(null);

  const selectBlock = useCallback((block: SelectedBlockData) => {
    setSelectedBlock(block);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedBlock(null);
  }, []);

  return (
    <SelectedBlockContext.Provider value={{ selectedBlock, selectBlock, clearSelection }}>
      {children}
    </SelectedBlockContext.Provider>
  );
}

export function useSelectedBlock() {
  const context = useContext(SelectedBlockContext);
  if (!context) {
    throw new Error("useSelectedBlock must be used within SelectedBlockProvider");
  }
  return context;
}
