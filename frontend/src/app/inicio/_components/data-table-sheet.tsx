"use client";

import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SheetData } from "./sheet-selector";

interface DataTableSheetProps {
  sheet: SheetData;
}

export function DataTableSheet({ sheet }: DataTableSheetProps) {
  if (sheet.rows.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Esta hoja está vacía
      </div>
    );
  }

  return (
    <div className="overflow-auto max-h-[500px]">
      <Table>
        <TableHeader className="sticky top-0 bg-background z-10">
          <TableRow>
            <TableHead className="w-12 bg-muted sticky left-0 z-20 border-r">
              #
            </TableHead>
            {sheet.columns.map((column, index) => (
              <TableHead key={index} className="min-w-[120px] font-medium">
                <div className="truncate" title={column}>
                  {column}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sheet.rows.map((row, rowIndex) => (
            <TableRow
              key={rowIndex}
              className="hover:bg-muted/50"
            >
              <TableCell className="font-mono text-xs text-muted-foreground bg-muted sticky left-0 z-10 border-r">
                {rowIndex + 1}
              </TableCell>
              {row.map((cell, cellIndex) => (
                <TableCell key={cellIndex} className="max-w-[200px]">
                  <div className="truncate" title={String(cell)}>
                    {String(cell || "")}
                  </div>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}