"use client";

import {
  BarChart3,
  LineChart as LineChartIcon,
  PieChart,
  Table,
  Type,
  Image as ImageIcon,
  Minus,
  FileText,
  Map,
  TrendingUp,
  Activity,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

export type WidgetType =
  | "kpi"
  | "table"
  | "line"
  | "bar"
  | "pie"
  | "map"
  | "pyramid"
  | "corridor"
  | "text"
  | "image"
  | "divider"
  | "pagebreak";

interface WidgetDefinition {
  type: WidgetType;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: "data" | "chart" | "content" | "layout";
}

const WIDGET_DEFINITIONS: WidgetDefinition[] = [
  // Data Widgets
  {
    type: "kpi",
    name: "KPI",
    description: "Métrica clave con comparación",
    icon: <TrendingUp className="w-4 h-4" />,
    category: "data",
  },
  {
    type: "table",
    name: "Tabla",
    description: "Tabla de datos",
    icon: <Table className="w-4 h-4" />,
    category: "data",
  },

  // Chart Widgets
  {
    type: "line",
    name: "Gráfico de Líneas",
    description: "Series temporales",
    icon: <LineChartIcon className="w-4 h-4" />,
    category: "chart",
  },
  {
    type: "bar",
    name: "Gráfico de Barras",
    description: "Comparación de categorías",
    icon: <BarChart3 className="w-4 h-4" />,
    category: "chart",
  },
  {
    type: "pie",
    name: "Gráfico Circular",
    description: "Distribución porcentual",
    icon: <PieChart className="w-4 h-4" />,
    category: "chart",
  },
  {
    type: "map",
    name: "Mapa",
    description: "Distribución geográfica",
    icon: <Map className="w-4 h-4" />,
    category: "chart",
  },
  {
    type: "pyramid",
    name: "Pirámide Poblacional",
    description: "Distribución por edad y sexo",
    icon: <Activity className="w-4 h-4" />,
    category: "chart",
  },
  {
    type: "corridor",
    name: "Corredor Endémico",
    description: "Vigilancia epidemiológica",
    icon: <LineChartIcon className="w-4 h-4" />,
    category: "chart",
  },

  // Content Widgets
  {
    type: "text",
    name: "Texto",
    description: "Texto enriquecido",
    icon: <Type className="w-4 h-4" />,
    category: "content",
  },
  {
    type: "image",
    name: "Imagen",
    description: "Imagen o logo",
    icon: <ImageIcon className="w-4 h-4" />,
    category: "content",
  },

  // Layout Widgets
  {
    type: "divider",
    name: "Separador",
    description: "Línea divisoria",
    icon: <Minus className="w-4 h-4" />,
    category: "layout",
  },
  {
    type: "pagebreak",
    name: "Salto de Página",
    description: "Nueva página en PDF",
    icon: <FileText className="w-4 h-4" />,
    category: "layout",
  },
];

interface WidgetLibraryProps {
  onAddWidget: (type: WidgetType) => void;
}

export function WidgetLibrary({ onAddWidget }: WidgetLibraryProps) {
  const categories = {
    data: WIDGET_DEFINITIONS.filter((w) => w.category === "data"),
    chart: WIDGET_DEFINITIONS.filter((w) => w.category === "chart"),
    content: WIDGET_DEFINITIONS.filter((w) => w.category === "content"),
    layout: WIDGET_DEFINITIONS.filter((w) => w.category === "layout"),
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">Widgets</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[calc(100vh-200px)]">
          <div className="space-y-4 px-4 pb-4">
            {/* Data Widgets */}
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground mb-2">
                DATOS
              </h3>
              <div className="space-y-1">
                {categories.data.map((widget) => (
                  <WidgetButton
                    key={widget.type}
                    widget={widget}
                    onClick={() => onAddWidget(widget.type)}
                  />
                ))}
              </div>
            </div>

            {/* Chart Widgets */}
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground mb-2">
                GRÁFICOS
              </h3>
              <div className="space-y-1">
                {categories.chart.map((widget) => (
                  <WidgetButton
                    key={widget.type}
                    widget={widget}
                    onClick={() => onAddWidget(widget.type)}
                  />
                ))}
              </div>
            </div>

            {/* Content Widgets */}
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground mb-2">
                CONTENIDO
              </h3>
              <div className="space-y-1">
                {categories.content.map((widget) => (
                  <WidgetButton
                    key={widget.type}
                    widget={widget}
                    onClick={() => onAddWidget(widget.type)}
                  />
                ))}
              </div>
            </div>

            {/* Layout Widgets */}
            <div>
              <h3 className="text-xs font-semibold text-muted-foreground mb-2">
                LAYOUT
              </h3>
              <div className="space-y-1">
                {categories.layout.map((widget) => (
                  <WidgetButton
                    key={widget.type}
                    widget={widget}
                    onClick={() => onAddWidget(widget.type)}
                  />
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

interface WidgetButtonProps {
  widget: WidgetDefinition;
  onClick: () => void;
}

function WidgetButton({ widget, onClick }: WidgetButtonProps) {
  return (
    <Button
      variant="ghost"
      className="w-full justify-start h-auto py-2 px-3 hover:bg-accent"
      onClick={onClick}
    >
      <div className="flex items-start gap-2 w-full">
        <div className="mt-0.5 text-muted-foreground">{widget.icon}</div>
        <div className="flex-1 text-left">
          <div className="text-sm font-medium">{widget.name}</div>
          <div className="text-xs text-muted-foreground">
            {widget.description}
          </div>
        </div>
      </div>
    </Button>
  );
}
