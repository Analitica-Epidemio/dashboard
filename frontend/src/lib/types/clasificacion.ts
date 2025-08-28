/**
 * Tipos de clasificación epidemiológica que coinciden exactamente
 * con el enum TipoClasificacion del backend
 */

export enum TipoClasificacion {
  CONFIRMADOS = "CONFIRMADOS",
  SOSPECHOSOS = "SOSPECHOSOS", 
  PROBABLES = "PROBABLES",
  EN_ESTUDIO = "EN_ESTUDIO",
  NEGATIVOS = "NEGATIVOS",
  DESCARTADOS = "DESCARTADOS",
  NOTIFICADOS = "NOTIFICADOS",
  CON_RESULTADO_MORTAL = "CON_RESULTADO_MORTAL",
  SIN_RESULTADO_MORTAL = "SIN_RESULTADO_MORTAL",
  REQUIERE_REVISION = "REQUIERE_REVISION"
}

export type TipoClasificacionValue = keyof typeof TipoClasificacion