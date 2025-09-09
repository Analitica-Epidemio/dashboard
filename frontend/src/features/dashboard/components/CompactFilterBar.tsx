/**
 * Compact Filter Bar Component
 * Shows applied filters in a compact top bar
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar,
  Filter,
  Edit,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface FilterCombination {
  id: string;
  groupId: string | null;
  groupName?: string;
  eventIds: number[];
  eventNames?: string[];
  label?: string;
  color?: string;
}

interface DateRange {
  from: Date | null;
  to: Date | null;
}

interface CompactFilterBarProps {
  dateRange: DateRange;
  filterCombinations: FilterCombination[];
  onEditFilters: () => void;
  expanded?: boolean;
  onToggleExpand?: () => void;
}

export const CompactFilterBar: React.FC<CompactFilterBarProps> = ({
  dateRange,
  filterCombinations,
  onEditFilters,
  expanded = false,
  onToggleExpand,
}) => {
  const formatDateRange = () => {
    if (!dateRange.from || !dateRange.to) return 'Sin rango';
    const options: Intl.DateTimeFormatOptions = { day: '2-digit', month: 'short' };
    return `${dateRange.from.toLocaleDateString('es', options)} - ${dateRange.to.toLocaleDateString('es', options)}`;
  };

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      {/* Main compact bar */}
      <div className="px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1 min-w-0">
            {/* Date Range */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg border border-blue-200">
              <Calendar className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">
                {formatDateRange()}
              </span>
            </div>

            {/* Filter combinations summary */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                {filterCombinations.length} {filterCombinations.length === 1 ? 'combinación' : 'combinaciones'}:
              </span>
              
              {/* Show first 3 combinations inline */}
              <div className="flex items-center gap-2">
                {filterCombinations.slice(0, 3).map((combination, index) => (
                  <div
                    key={combination.id}
                    className={`px-2 py-1 rounded-lg border-2 ${combination.color || 'bg-gray-100 border-gray-300'}`}
                  >
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs bg-white h-5">
                        #{index + 1}
                      </Badge>
                      <span className="text-xs font-medium text-gray-900">
                        {combination.groupName}
                      </span>
                      {combination.eventIds.length > 0 && (
                        <Badge variant="secondary" className="text-xs bg-white/80 h-5">
                          {combination.eventIds.length}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
                
                {filterCombinations.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{filterCombinations.length - 3} más
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {onToggleExpand && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleExpand}
              >
                {expanded ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-1" />
                    Ocultar detalles
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-1" />
                    Ver detalles
                  </>
                )}
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

      {/* Expanded details */}
      {expanded && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {filterCombinations.map((combination, index) => (
              <div
                key={combination.id}
                className={`p-3 rounded-lg border-2 ${combination.color || 'bg-white border-gray-300'}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-white">
                      #{index + 1}
                    </Badge>
                    <span className="font-semibold text-sm text-gray-900">
                      {combination.groupName}
                    </span>
                  </div>
                </div>
                
                <div className="space-y-1">
                  <p className="text-xs text-gray-600">
                    Eventos ({combination.eventIds.length}):
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {combination.eventNames?.slice(0, 2).map((name, i) => (
                      <Badge key={i} variant="secondary" className="text-xs bg-white/80">
                        {name}
                      </Badge>
                    ))}
                    {combination.eventNames && combination.eventNames.length > 2 && (
                      <Badge variant="secondary" className="text-xs bg-white/80">
                        +{combination.eventNames.length - 2}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};