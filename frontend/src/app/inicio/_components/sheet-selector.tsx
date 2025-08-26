"use client";

import React from "react";

export interface SheetData {
  name: string;
  rows: unknown[][];
  total_rows: number;
  columns: string[];
}

interface SheetSelectorProps {
  sheets: Record<string, SheetData>;
  selectedSheet: string;
  onSheetChange: (sheetName: string) => void;
  children: (sheet: SheetData) => React.ReactNode;
}

export const SheetSelector = React.memo(function SheetSelector({
  sheets,
  selectedSheet,
  onSheetChange,
  children,
}: SheetSelectorProps) {
  const sheetNames = React.useMemo(() => Object.keys(sheets), [sheets]);

  if (sheetNames.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Hojas disponibles</h2>
        <p className="text-gray-600">
          Revisa las primeras 50 filas de cada hoja y selecciona una para
          continuar
        </p>
      </div>

      {/* Custom tabs design - more minimal */}
      <div className="mb-6">
        <div className="border-b border-border">
          <nav className="flex space-x-6">
            {sheetNames.map((sheetName) => (
              <button
                key={sheetName}
                onClick={() => onSheetChange(sheetName)}
                className={`
                  pb-3 px-1 relative text-sm font-medium transition-colors
                  ${selectedSheet === sheetName 
                    ? 'text-foreground border-b-2 border-primary' 
                    : 'text-muted-foreground hover:text-foreground'
                  }
                `}
              >
                <div className="flex items-center space-x-2">
                  <span>{sheetName}</span>
                  <span className="text-xs opacity-75">
                    ({sheets[sheetName].total_rows} filas)
                  </span>
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content for selected sheet */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Hoja: {selectedSheet}</h3>
            <p className="text-sm text-muted-foreground">
              Mostrando las primeras{" "}
              {Math.min(sheets[selectedSheet].rows.length, 49)} de{" "}
              {sheets[selectedSheet].total_rows - 1} filas de datos
            </p>
          </div>
        </div>

        <div className="border border-border rounded-lg">
          {children(sheets[selectedSheet])}
        </div>
      </div>
    </div>
  );
});
