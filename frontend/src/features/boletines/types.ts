/**
 * Shared types for boletines features (used by analytics and boletines)
 */

export interface EventoSeleccionado {
  id: number;
  codigo: string;
  nombre: string;
  tipo: "tipo_eno" | "grupo_eno" | "grupo_de_enfermedades";
  order: number;
}

export interface PeriodoConfig {
  semana: number;
  anio: number;
  numSemanas: number;
  tituloCustom: string;
}
