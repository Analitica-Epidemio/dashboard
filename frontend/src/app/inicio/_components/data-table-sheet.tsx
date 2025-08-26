"use client";

import React from "react";
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  ColumnDef,
  flexRender,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SheetData } from "./sheet-selector";

interface DataTableSheetProps {
  sheet: SheetData;
}

export function DataTableSheet({ sheet }: DataTableSheetProps) {
  // Crear columnas dinámicamente basadas en los datos
  const columns = React.useMemo<ColumnDef<unknown[]>[]>(() => {
    if (sheet.rows.length === 0) return [];
    
    const firstRow = sheet.rows[0];
    return firstRow.map((_, index) => ({
      id: `col_${index}`,
      header: sheet.columns[index] || `Columna ${index + 1}`,
      accessorFn: (row: unknown[]) => row[index] || "",
      cell: ({ getValue }) => {
        const value = getValue();
        return (
          <div className="max-w-[200px] truncate" title={String(value)}>
            {String(value)}
          </div>
        );
      },
    }));
  }, [sheet]);

  const [globalFilter, setGlobalFilter] = React.useState("");

  const table = useReactTable({
    data: sheet.rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      globalFilter,
    },
    onGlobalFilterChange: setGlobalFilter,
    initialState: {
      pagination: {
        pageSize: 20,
      },
    },
  });

  if (sheet.rows.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        Esta hoja está vacía
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtro global */}
      <div className="flex items-center py-4 px-4">
        <Input
          placeholder="Filtrar datos..."
          value={globalFilter}
          onChange={(event) => setGlobalFilter(event.target.value)}
          className="max-w-sm"
        />
        <div className="ml-auto text-sm text-gray-600">
          {table.getFilteredRowModel().rows.length} de {sheet.rows.length} filas
        </div>
      </div>

      {/* Tabla */}
      <div className="rounded-md border overflow-hidden">
        <div className="overflow-auto max-h-96">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  <TableHead className="w-12 bg-gray-50 sticky left-0 z-10">
                    #
                  </TableHead>
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} className="min-w-[120px]">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row, index) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && "selected"}
                    className="hover:bg-gray-50"
                  >
                    <TableCell className="font-mono text-xs text-gray-400 bg-gray-50 sticky left-0 z-10">
                      {index + 1}
                    </TableCell>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell 
                    colSpan={columns.length + 1} 
                    className="h-24 text-center"
                  >
                    No se encontraron datos.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Paginación */}
      <div className="flex items-center justify-between px-4 py-2">
        <div className="text-sm text-gray-600">
          Página {table.getState().pagination.pageIndex + 1} de{" "}
          {table.getPageCount()}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  );
}