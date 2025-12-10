// Mapeo entre códigos INDEC de departamentos de Chubut y IDs del SVG
export const DEPARTAMENTO_INDEC_TO_SVG: Record<number, string> = {
  26007: 'biedma',
  26014: 'cushamen',
  26021: 'escalante',
  26028: 'florentino_ameghino',
  26035: 'futaleufu',
  26042: 'gaiman',
  26049: 'gastre',
  26056: 'languineo',
  26063: 'martires',
  26070: 'paso_de_indios',
  26077: 'rawson',
  26084: 'rio_senguer',
  26091: 'sarmiento',
  26098: 'tehuelches',
  26105: 'telsen',
};

export function getSvgIdFromIndec(codigoIndec: number): string | undefined {
  return DEPARTAMENTO_INDEC_TO_SVG[codigoIndec];
}

export function getIndecFromSvgId(svgId: string): number | undefined {
  const entry = Object.entries(DEPARTAMENTO_INDEC_TO_SVG).find(
    ([, value]) => value === svgId
  );
  return entry ? parseInt(entry[0]) : undefined;
}
