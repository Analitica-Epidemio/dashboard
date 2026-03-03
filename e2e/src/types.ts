import type { Page } from "playwright";

/** Un paso individual dentro de un tutorial */
export interface TutorialStep {
  /** Identificador único del paso */
  id: string;
  /** Texto de narración para este paso (usado por TTS) */
  narration: string;
  /** Acción a ejecutar en el browser */
  action: (page: Page) => Promise<void>;
  /** Milisegundos a esperar después de la acción (default: 1000) */
  waitAfterAction?: number;
  /** Selector CSS del elemento a resaltar durante este paso */
  highlight?: string;
}

/** Definición completa de un tutorial */
export interface TutorialDefinition {
  /** Identificador único del tutorial */
  id: string;
  /** Título descriptivo */
  title: string;
  /** Descripción breve de qué muestra el tutorial */
  description: string;
  /** URL inicial donde empieza el tutorial (relativa a BASE_URL) */
  setupPath: string;
  /** Lista ordenada de pasos */
  steps: TutorialStep[];
}

/** Opciones de la CLI */
export interface CliOptions {
  /** ID del tutorial a ejecutar */
  tutorial: string;
  /** Saltar fase de captura de video */
  skipCapture: boolean;
  /** Saltar fase de narración */
  skipNarrate: boolean;
  /** Saltar fase de composición */
  skipCompose: boolean;
  /** Mostrar el browser (no headless) */
  headed: boolean;
  /** Directorio de salida */
  outputDir: string;
}

/** Resultado de la fase de narración */
export interface NarrationResult {
  /** Ruta al archivo de audio generado */
  audioPath: string;
  /** Duraciones de cada paso en milisegundos */
  durations: Record<string, number>;
}

/** Resultado de la fase de captura */
export interface CaptureResult {
  /** Ruta al video capturado */
  videoPath: string;
  /** Timestamps de cada paso en milisegundos */
  timestamps: Record<string, number>;
}

/** Resultado de la fase de composición */
export interface ComposeResult {
  /** Ruta al video final */
  finalVideoPath: string;
}
