"use client";

import React from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

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

export function SheetSelector({ 
  sheets, 
  selectedSheet, 
  onSheetChange, 
  children 
}: SheetSelectorProps) {
  const sheetNames = Object.keys(sheets);

  if (sheetNames.length === 0) {
    return null;
  }

  return (
    <div className="w-full max-w-6xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Hojas disponibles</h2>
        <p className="text-gray-600">
          Revisa las primeras 50 filas de cada hoja y selecciona una para continuar
        </p>
      </div>

      <Tabs value={selectedSheet} onValueChange={onSheetChange} className="w-full">
        <TabsList className="mb-4">
          {sheetNames.map((sheetName) => (
            <TabsTrigger key={sheetName} value={sheetName}>
              {sheetName}
              <span className="ml-2 text-xs text-gray-500">
                ({sheets[sheetName].total_rows} filas)
              </span>
            </TabsTrigger>
          ))}
        </TabsList>

        {sheetNames.map((sheetName) => (
          <TabsContent key={sheetName} value={sheetName}>
            <div className="border rounded-lg bg-white">
              <div className="p-4 border-b">
                <h3 className="text-lg font-semibold">
                  Hoja: {sheetName}
                </h3>
                <p className="text-sm text-gray-600">
                  Mostrando las primeras {Math.min(sheets[sheetName].rows.length, 50)} 
                  de {sheets[sheetName].total_rows} filas
                </p>
              </div>
              
              {children(sheets[sheetName])}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}