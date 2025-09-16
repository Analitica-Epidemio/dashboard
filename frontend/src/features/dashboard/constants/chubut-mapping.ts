/**
 * Mapeo entre códigos INDEC de departamentos y IDs del SVG de Chubut
 * Solo el mapeo visual debe estar en el frontend
 */

// Mapeo de códigos INDEC a IDs del SVG (kebab-case)
export const DEPARTAMENTO_INDEC_TO_SVG: Record<number, string> = {
  26007: "biedma",
  26014: "cushamen",
  26021: "escalante",
  26028: "florentino-ameghino",
  26035: "futaleufu",
  26042: "gaiman",
  26049: "gastre",
  26056: "languineo",
  26063: "martires",
  26070: "paso-de-indios",
  26077: "rawson",
  26084: "rio-senguer",
  26091: "sarmiento",
  26098: "tehuelches",
  206105: "telsen",
};

// Mapeo inverso: de SVG ID a código INDEC
export const SVG_TO_DEPARTAMENTO_INDEC: Record<string, number> = Object.entries(
  DEPARTAMENTO_INDEC_TO_SVG
).reduce((acc, [indec, svg]) => {
  acc[svg] = parseInt(indec);
  return acc;
}, {} as Record<string, number>);

// Helper functions para el mapeo visual
export function getSvgIdFromIndec(codigoIndec: number): string {
  return DEPARTAMENTO_INDEC_TO_SVG[codigoIndec] || "";
}

export function getIndecFromSvgId(svgId: string): number {
  return SVG_TO_DEPARTAMENTO_INDEC[svgId] || 0;
}