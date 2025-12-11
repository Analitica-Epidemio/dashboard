// Widget types - defined locally since not in OpenAPI schema

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface WidgetVisualConfig {
  show_title?: boolean;
  show_description?: boolean;
  config?: Record<string, unknown>;
}

export interface WidgetDataConfig {
  source: "manual" | "query";
  query_id?: string;
  query_params?: Record<string, unknown>;
  manual_data?: Record<string, unknown>;
}

export interface BaseWidget {
  id: string;
  type: string;
  title: string;
  description?: string;
  position: WidgetPosition;
  visual_config?: WidgetVisualConfig;
  data_config?: WidgetDataConfig;
}

export interface KPIWidget extends BaseWidget {
  type: "kpi";
  data_config: WidgetDataConfig;
}

export interface GenericWidget extends BaseWidget {
  type: "chart" | "table" | "text" | "image" | "line" | "bar" | "pie" | "map" | "pyramid" | "corridor" | "divider" | "pagebreak";
  data_config?: WidgetDataConfig;
}

// Widget is a discriminated union of all widget types
export type Widget = KPIWidget | GenericWidget;

// Extract the discriminated type field
export type WidgetType = Widget["type"];

export interface WidgetProps {
  widget: Widget;
  data?: Record<string, unknown> | number | unknown[];
  isLoading?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
}
