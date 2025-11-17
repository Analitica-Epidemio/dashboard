"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import dynamic from "next/dynamic";

// Import ChubutMapChart dynamically to avoid SSR issues with D3
const ChubutMapChart = dynamic(
  () => import("@/components/charts/chubut-map-chart").then((mod) => mod.ChubutMapChart),
  { ssr: false }
);

export function MapWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  // Parse data
  let mapData: Array<{ nombre: string; casos: number }> = [];

  if (widget.data_config.source === "manual" && widget.data_config.manual_data) {
    const manualData = widget.data_config.manual_data as { departamentos?: Array<{ nombre: string; casos: number }> };
    mapData = manualData.departamentos || [];
  } else if (data) {
    if (typeof data === "object" && "departamentos" in data) {
      const typedData = data as { departamentos: Array<{ nombre: string; casos: number }> };
      mapData = typedData.departamentos;
    } else if (Array.isArray(data)) {
      // Convert array format
      mapData = (data as Array<Record<string, unknown>>).map((item) => ({
        nombre: String(item.nombre || item.departamento || item.name),
        casos: Number(item.casos || item.value || item.count || 0),
      }));
    }
  }

  // Transform to DepartmentData format with default values for missing fields
  const departmentData = mapData.map((dept, index) => ({
    codigo_indec: 0, // Default value - will need proper mapping
    nombre: dept.nombre,
    zona_ugd: "", // Default empty
    poblacion: 0, // Default value
    casos: dept.casos,
    tasa_incidencia: 0, // Default value
  }));

  const totalCasos = mapData.reduce((sum, dept) => sum + dept.casos, 0);

  return (
    <WidgetContainer
      title={widget.title}
      showTitle={widget.visual_config?.show_title}
      isLoading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
    >
      {mapData.length === 0 ? (
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No hay datos disponibles
        </div>
      ) : (
        <div className="h-full w-full">
          <ChubutMapChart
            data={{
              departamentos: departmentData,
              total_casos: totalCasos,
            }}
          />
        </div>
      )}
    </WidgetContainer>
  );
}
