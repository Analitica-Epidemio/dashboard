/**
 * Compact Filter Bar Component
 * Shows applied filters in a compact top bar
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  Edit,
  Download,
  Loader2,
  ExternalLink,
} from 'lucide-react';
import type { FilterCombination } from "../../contexts/filter-context";
import { getEpiWeek } from '../../components/filter-builder/epiweek-utils';

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface CompactFilterBarProps {
  dateRange: DateRange;
  filterCombinations: FilterCombination[];
  onEditFilters: () => void;
  onGenerateZipReport?: () => void;
  onGenerateSignedUrl?: () => void;
  isGeneratingReport?: boolean;
  isGeneratingSignedUrl?: boolean;
}

export const CompactFilterBar: React.FC<CompactFilterBarProps> = ({
  dateRange,
  filterCombinations,
  onEditFilters,
  onGenerateZipReport,
  onGenerateSignedUrl,
  isGeneratingReport = false,
  isGeneratingSignedUrl = false,
}) => {
  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return 'Sin rango';

    // Calcular semanas epidemiológicas
    const startWeek = getEpiWeek(dateRange.from);
    const endWeek = getEpiWeek(dateRange.to);

    // Si es el mismo año, mostrar formato simple
    if (startWeek.year === endWeek.year) {
      return `SE ${startWeek.week} - ${endWeek.week} / ${startWeek.year}`;
    }

    // Si son diferentes años, mostrar ambos
    return `SE ${startWeek.week}/${startWeek.year} - SE ${endWeek.week}/${endWeek.year}`;
  };

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      {/* Main compact bar */}
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Date Range */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg border border-blue-200">
              <Calendar className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">
                {formatDateRange()}
              </span>
            </div>

            {/* Combinations count */}
            <span className="text-sm text-gray-600">
              {filterCombinations.length} {filterCombinations.length === 1 ? 'combinación' : 'combinaciones'}
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Generate Signed URL for SSR */}
            {onGenerateSignedUrl && filterCombinations.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onGenerateSignedUrl}
                disabled={isGeneratingSignedUrl}
                title="Generar URL para vista de reporte"
                className="bg-green-50 border-green-200 hover:bg-green-100"
              >
                {isGeneratingSignedUrl ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <ExternalLink className="h-4 w-4 mr-1" />
                )}
                {isGeneratingSignedUrl ? 'Generando URL...' : 'Vista Reporte'}
              </Button>
            )}

            {/* Generate ZIP Report */}
            {onGenerateZipReport && filterCombinations.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onGenerateZipReport}
                disabled={isGeneratingReport}
                title={`Generar ${filterCombinations.length} reportes PDF en ZIP`}
                className="bg-blue-50 border-blue-200 hover:bg-blue-100"
              >
                {isGeneratingReport ? (
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-1" />
                )}
                {isGeneratingReport ? 'Generando...' : `Descargar Reportes (${filterCombinations.length})`}
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={onEditFilters}
            >
              <Edit className="h-4 w-4 mr-1" />
              Editar filtros
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};