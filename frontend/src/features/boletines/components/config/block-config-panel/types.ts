/**
 * Types for Block Config Panel
 */

// Series configuration for charts
export interface SerieConfig {
  label: string;
  color: string;
  valores: string[];
}

// Form state interface
export interface BlockConfigFormState {
  editTitle: string;
  setEditTitle: (value: string) => void;
  editLimit: string;
  setEditLimit: (value: string) => void;
  editPeriodo: string;
  setEditPeriodo: (value: string) => void;
  editChartType: string;
  setEditChartType: (value: string) => void;
  editEventoCodigo: string;
  setEditEventoCodigo: (value: string) => void;
  editEventosCodigos: string[];
  setEditEventosCodigos: (value: string[]) => void;
  editAgentesCodigos: string[];
  setEditAgentesCodigos: (value: string[]) => void;
  editSoloConfirmados: boolean;
  setEditSoloConfirmados: (value: boolean) => void;
  editSoloInternados: boolean;
  setEditSoloInternados: (value: boolean) => void;
  editSeries: SerieConfig[];
  setEditSeries: (value: SerieConfig[]) => void;
  // grouping mode - determines if series valores are event codes or agent codes
  editAgruparPor: "evento" | "agente";
  setEditAgruparPor: (value: "evento" | "agente") => void;
}

// Available data interface
export interface BlockConfigData {
  tiposEno: { codigo: string; nombre: string }[];
  agentes: { codigo: string; nombre: string }[];
}

// Props for config components
export interface BlockConfigProps {
  formState: BlockConfigFormState;
  data: BlockConfigData;
}
