// Widget types now come from OpenAPI - see @/lib/api/types
import type { components } from "@/lib/api/types";

// Widget is a discriminated union of all widget types
export type Widget =
  | components["schemas"]["KPIWidget-Output"]
  | components["schemas"]["GenericWidget"];

export type WidgetPosition = components["schemas"]["WidgetPosition"];
export type WidgetVisualConfig = components["schemas"]["WidgetVisualConfig"];

// Extract the discriminated type field
export type WidgetType = Widget["type"];

export interface WidgetProps {
  widget: Widget;
  data?: Record<string, unknown> | number | unknown[];
  isLoading?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
}
