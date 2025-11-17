// Sistema de bloques para el editor de boletines

export type BlockType =
  | "heading"
  | "paragraph"
  | "table"
  | "chart"
  | "image"
  | "divider"
  | "pagebreak";

export type ChartType = "line" | "bar" | "table_data" | "corridor";

export interface BaseBlock {
  id: string;
  type: BlockType;
  orden: number;
}

export interface HeadingBlock extends BaseBlock {
  type: "heading";
  level: 1 | 2 | 3;
  content: string;
  align?: "left" | "center" | "right";
}

export interface ParagraphBlock extends BaseBlock {
  type: "paragraph";
  content: string; // HTML
  align?: "left" | "center" | "right";
}

export interface TableBlock extends BaseBlock {
  type: "table";
  title?: string;
  dataSource: "manual" | "query";
  // Manual data
  headers?: string[];
  rows?: string[][];
  // Query data (dinámico desde backend)
  query?: {
    type: "top_enos" | "capacidad_hospitalaria" | "casos_suh" | "custom";
    params?: Record<string, unknown>;
  };
  footnote?: string;
}

export interface ChartBlock extends BaseBlock {
  type: "chart";
  chartType: ChartType;
  title?: string;
  dataSource: "manual" | "query";
  // Manual data
  data?: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      color?: string;
    }[];
  };
  // Query data
  query?: {
    type: "corredor_ira" | "virus_respiratorios" | "intoxicacion_co" | "custom";
    params?: Record<string, unknown>;
  };
  footnote?: string;
  height?: number;
}

export interface ImageBlock extends BaseBlock {
  type: "image";
  url: string;
  alt?: string;
  caption?: string;
  width?: number;
  align?: "left" | "center" | "right";
}

export interface DividerBlock extends BaseBlock {
  type: "divider";
}

export interface PageBreakBlock extends BaseBlock {
  type: "pagebreak";
}

export type Block =
  | HeadingBlock
  | ParagraphBlock
  | TableBlock
  | ChartBlock
  | ImageBlock
  | DividerBlock
  | PageBreakBlock;

// Template del boletín con sistema de bloques
export interface BoletinTemplate {
  id?: number;
  nombre: string;
  tipo: "boletin_semanal";
  portada: {
    titulo: string;
    subtitulo?: string;
    incluir_logo: boolean;
    logo_url?: string;
  };
  bloques: Block[];
  created_at?: string;
  updated_at?: string;
}

// Queries disponibles para tablas y gráficos
export const AVAILABLE_QUERIES = {
  tables: [
    {
      id: "top_enos",
      nombre: "Top ENOs",
      descripcion: "Tabla de eventos más frecuentes",
      params: ["top_n", "periodo_semanas", "excluir_respiratorios"],
    },
    {
      id: "capacidad_hospitalaria",
      nombre: "Capacidad Hospitalaria",
      descripcion: "Dotación de camas por hospital",
      params: ["hospitales", "semana"],
    },
    {
      id: "casos_suh",
      nombre: "Casos de SUH",
      descripcion: "Descripción de casos SUH confirmados",
      params: ["periodo_desde", "periodo_hasta"],
    },
  ],
  charts: [
    {
      id: "corredor_ira",
      nombre: "Corredor Endémico IRA",
      descripcion: "Corredor de ETI/Neumonía/Bronquiolitis",
      params: ["tipo_ira", "año"],
    },
    {
      id: "virus_respiratorios",
      nombre: "Virus Respiratorios",
      descripcion: "Detección de virus por semana",
      params: ["tipo_grafico", "año"],
    },
    {
      id: "intoxicacion_co",
      nombre: "Intoxicación CO",
      descripcion: "Casos por UGD comparando años",
      params: ["año_actual", "año_comparacion"],
    },
  ],
};
