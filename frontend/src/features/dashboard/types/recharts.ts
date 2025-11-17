/**
 * Recharts type definitions with proper generic typing
 */

import type { LegendType } from 'recharts';

// Base payload type for chart data points
export interface BaseChartPayload {
  [key: string]: unknown;
}

// Tooltip payload entry with generic typing
export interface TooltipPayloadEntry<TPayload = BaseChartPayload> {
  value?: string | number;
  name?: string | number;
  payload?: TPayload;
  color?: string;
  dataKey?: string | number;
  type?: string;
  strokeDasharray?: string | number;
  fill?: string;
}

// Tooltip props with generic payload typing
export interface TooltipProps<TPayload = BaseChartPayload> {
  active?: boolean;
  payload?: Array<TooltipPayloadEntry<TPayload>>;
  label?: string | number;
}

// Custom label render function props
export interface CustomLabelProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  percent: number;
  index?: number;
  value?: string | number;
  name?: string;
}

// Legend payload type
export interface LegendPayload {
  value: string | number;
  type?: LegendType;
  id?: string;
  color?: string;
  payload?: {
    strokeDasharray?: string | number;
    value?: unknown;
  };
}

// XAxis tick props
export interface XAxisTickProps {
  fontSize?: number;
  angle?: number;
  textAnchor?: 'start' | 'middle' | 'end';
}

// Custom tick component props
export interface CustomTickProps {
  x?: number;
  y?: number;
  payload?: {
    value: string | number;
  };
}

// Specific payload types for different charts
export interface UGDChartPayload extends BaseChartPayload {
  name: string;
  value: number;
  cases: number;
  deaths?: number;
  mortalityRate?: number;
  percentage?: number;
  color?: string;
}

export interface EpidemiologicalPayload extends BaseChartPayload {
  week: number;
  year: number;
  deaths?: number;
  mortalityRate?: number;
  cumulativeMortality?: number;
  [viralAgentId: string]: number | undefined;
}

export interface EndemicCorridorPayload extends BaseChartPayload {
  week: number;
  success: number;
  security: number;
  alert: number;
  currentCases?: number | null;
  mortalityRate?: number;
}

export interface HistoricalPayload extends BaseChartPayload {
  year: number;
  total: number;
  mortalityRate?: number;
  [areaId: string]: number | undefined;
}

export interface AnimalRabiesPayload extends BaseChartPayload {
  period: string;
  cases: number;
  tested: number;
  positive: number;
  positivityRate: number;
  name?: string;
  location?: string;
  value?: number;
  attempts?: number;
  color?: string;
}

export interface SuicideAttemptPayload extends BaseChartPayload {
  week: number;
  attempts: number;
  deaths?: number;
  mortalityRate?: number;
}