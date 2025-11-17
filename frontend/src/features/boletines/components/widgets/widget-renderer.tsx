"use client";

import { Widget, WidgetProps } from "./types";
import { KPIWidget } from "./kpi-widget";
import { TableWidget } from "./table-widget";
import { LineChartWidget } from "./line-chart-widget";
import { BarChartWidget } from "./bar-chart-widget";
import { PieChartWidget } from "./pie-chart-widget";
import { MapWidget } from "./map-widget";
import { PyramidWidget } from "./pyramid-widget";

interface WidgetRendererProps extends Omit<WidgetProps, "widget"> {
  widget: Widget;
}

export function WidgetRenderer(props: WidgetRendererProps) {
  const { widget } = props;

  switch (widget.type) {
    case "kpi":
      return <KPIWidget {...props} />;
    case "table":
      return <TableWidget {...props} />;
    case "line":
      return <LineChartWidget {...props} />;
    case "bar":
      return <BarChartWidget {...props} />;
    case "pie":
      return <PieChartWidget {...props} />;
    case "map":
      return <MapWidget {...props} />;
    case "pyramid":
      return <PyramidWidget {...props} />;
    case "corridor":
      // TODO: Implement CorridorWidget (endemic corridor)
      return <PlaceholderWidget {...props} type="Corredor Endémico" />;
    case "text":
      // TODO: Implement TextWidget
      return <PlaceholderWidget {...props} type="Texto" />;
    case "image":
      // TODO: Implement ImageWidget
      return <PlaceholderWidget {...props} type="Imagen" />;
    case "divider":
      // TODO: Implement DividerWidget
      return <PlaceholderWidget {...props} type="Separador" />;
    case "pagebreak":
      // TODO: Implement PageBreakWidget
      return <PlaceholderWidget {...props} type="Salto de Página" />;
    default:
      return <PlaceholderWidget {...props} type="Widget Desconocido" />;
  }
}

function PlaceholderWidget({ widget, type }: WidgetRendererProps & { type: string }) {
  return (
    <div className="h-full border-2 border-dashed border-muted-foreground/25 rounded-lg flex items-center justify-center bg-muted/10">
      <div className="text-center p-4">
        <div className="text-sm font-medium text-muted-foreground mb-1">{type}</div>
        {widget.title && (
          <div className="text-xs text-muted-foreground/75">{widget.title}</div>
        )}
        <div className="text-xs text-muted-foreground/50 mt-2">
          Widget en desarrollo
        </div>
      </div>
    </div>
  );
}
