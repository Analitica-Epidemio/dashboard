"use client";

import { WidgetContainer } from "./widget-container";
import { WidgetProps } from "./types";
import dynamic from "next/dynamic";

// Import PopulationPyramid dynamically to avoid SSR issues with D3
const PopulationPyramid = dynamic(
  () => import("@/features/dashboard/components/charts/population-pyramid").then((mod) => mod.PopulationPyramid),
  { ssr: false }
);

export function PyramidWidget({ widget, data, isLoading, onEdit, onDelete }: WidgetProps) {
  // Parse data
  let rawPyramidData: Array<{ age_group: string; male: number; female: number }> = [];

  if (widget.data_config.source === "manual" && widget.data_config.manual_data) {
    const manualData = widget.data_config.manual_data as {
      data?: Array<{ age_group: string; male: number; female: number }>;
    };
    rawPyramidData = manualData.data || [];
  } else if (data) {
    if (Array.isArray(data)) {
      rawPyramidData = (data as Array<Record<string, unknown>>).map((item) => ({
        age_group: String(item.age_group || item.grupo_edad || ""),
        male: Number(item.male || item.masculino || item.hombres || 0),
        female: Number(item.female || item.femenino || item.mujeres || 0),
      }));
    } else if (typeof data === "object" && "data" in data) {
      const typedData = data as { data: Array<{ age_group: string; male: number; female: number }> };
      rawPyramidData = typedData.data;
    }
  }

  // Transform from wide format to long format for the pyramid chart
  const pyramidData = rawPyramidData.flatMap((item) => [
    { age: item.age_group, sex: "M" as const, value: item.male },
    { age: item.age_group, sex: "F" as const, value: item.female },
  ]);

  return (
    <WidgetContainer
      title={widget.title}
      showTitle={widget.visual_config?.show_title}
      isLoading={isLoading}
      onEdit={onEdit}
      onDelete={onDelete}
    >
      {pyramidData.length === 0 ? (
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No hay datos disponibles
        </div>
      ) : (
        <div className="h-full w-full flex items-center justify-center">
          <PopulationPyramid data={pyramidData} />
        </div>
      )}
    </WidgetContainer>
  );
}
