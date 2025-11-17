"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";

export function TableWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  const config = widget.visual_config?.config || {};
  const showHeader = config.show_header !== false;
  const alternateRows = config.alternate_rows !== false;

  // Parse data
  let tableData: Record<string, unknown>[] = [];
  let columns: string[] = [];

  if (widget.data_config.source === "manual" && widget.data_config.manual_data) {
    const manualData = widget.data_config.manual_data as { rows?: Record<string, unknown>[]; columns?: string[] };
    tableData = manualData.rows || [];
    columns = manualData.columns || [];
  } else if (data) {
    if (Array.isArray(data)) {
      tableData = data as Record<string, unknown>[];
      if (data.length > 0) {
        columns = Object.keys(data[0] as Record<string, unknown>);
      }
    } else if (typeof data === "object" && "rows" in data && "columns" in data) {
      const typedData = data as { rows: Record<string, unknown>[]; columns: string[] };
      tableData = typedData.rows;
      columns = typedData.columns;
    }
  }

  const formatCellValue = (value: unknown): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") {
      return value.toLocaleString("es-AR");
    }
    if (typeof value === "boolean") {
      return value ? "Sí" : "No";
    }
    return String(value);
  };

  return (
    <WidgetContainer
      title={widget.title}
      showTitle={widget.visual_config?.show_title}
      isLoading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
    >
      <ScrollArea className="h-full">
        <Table>
          {showHeader && columns.length > 0 && (
            <TableHeader>
              <TableRow>
                {columns.map((col, idx) => (
                  <TableHead key={idx} className="font-semibold">
                    {col}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
          )}
          <TableBody>
            {tableData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length || 1} className="text-center text-muted-foreground py-8">
                  No hay datos disponibles
                </TableCell>
              </TableRow>
            ) : (
              tableData.map((row, rowIdx) => (
                <TableRow
                  key={rowIdx}
                  className={alternateRows && rowIdx % 2 === 1 ? "bg-muted/50" : ""}
                >
                  {columns.map((col, colIdx) => (
                    <TableCell key={colIdx}>{formatCellValue(row[col])}</TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </ScrollArea>
    </WidgetContainer>
  );
}
