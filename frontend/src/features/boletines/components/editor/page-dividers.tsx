"use client";

interface PageDividersProps {
  editorRef: HTMLDivElement | null;
}

/**
 * Componente que muestra líneas divisorias cada 297mm (altura A4)
 * para indicar dónde cambiaría la página al exportar a PDF.
 * No calcula nada dinámicamente - solo referencias visuales fijas.
 */
export function PageDividers({ editorRef }: PageDividersProps) {
  if (!editorRef) return null;

  // Altura de página A4 en mm
  const pageHeightMm = 297;

  // Mostrar 20 páginas de referencia (suficiente para boletines largos)
  const maxPages = 20;

  return (
    <div className="pointer-events-none absolute left-0 top-0 right-0" style={{ zIndex: 0 }}>
      {Array.from({ length: maxPages }).map((_, index) => {
        const pageNumber = index + 1;
        const topPosition = `${pageHeightMm * pageNumber}mm`;

        return (
          <div
            key={index}
            className="absolute left-0 right-0 flex items-center justify-center"
            style={{ top: topPosition }}
          >
            {/* Línea divisoria */}
            <div className="w-full border-t-2 border-dashed border-blue-400/50" />

            {/* Indicador de cambio de página */}
            <div className="absolute bg-blue-500 text-white text-[10px] font-medium px-3 py-1 rounded-full shadow-sm">
              Aquí cambia la página {pageNumber} → {pageNumber + 1}
            </div>
          </div>
        );
      })}
    </div>
  );
}
