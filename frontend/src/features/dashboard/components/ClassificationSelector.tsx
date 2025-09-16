/**
 * Classification Selector Component
 * Allows selecting multiple epidemiological classifications for filtering
 */

import React from 'react';
import { Check, ChevronDown } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Tipos de clasificación epidemiológica
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
  REQUIERE_REVISION = "REQUIERE_REVISION",
}

// Colores para cada clasificación
const CLASSIFICATION_COLORS: Record<TipoClasificacion, string> = {
  [TipoClasificacion.CONFIRMADOS]: "bg-red-100 text-red-800 border-red-300",
  [TipoClasificacion.SOSPECHOSOS]: "bg-yellow-100 text-yellow-800 border-yellow-300",
  [TipoClasificacion.PROBABLES]: "bg-orange-100 text-orange-800 border-orange-300",
  [TipoClasificacion.EN_ESTUDIO]: "bg-blue-100 text-blue-800 border-blue-300",
  [TipoClasificacion.NEGATIVOS]: "bg-green-100 text-green-800 border-green-300",
  [TipoClasificacion.DESCARTADOS]: "bg-gray-100 text-gray-800 border-gray-300",
  [TipoClasificacion.NOTIFICADOS]: "bg-purple-100 text-purple-800 border-purple-300",
  [TipoClasificacion.CON_RESULTADO_MORTAL]: "bg-black text-white border-black",
  [TipoClasificacion.SIN_RESULTADO_MORTAL]: "bg-gray-200 text-gray-700 border-gray-400",
  [TipoClasificacion.REQUIERE_REVISION]: "bg-pink-100 text-pink-800 border-pink-300",
};

// Labels amigables
const CLASSIFICATION_LABELS: Record<TipoClasificacion, string> = {
  [TipoClasificacion.CONFIRMADOS]: "Confirmados",
  [TipoClasificacion.SOSPECHOSOS]: "Sospechosos",
  [TipoClasificacion.PROBABLES]: "Probables",
  [TipoClasificacion.EN_ESTUDIO]: "En estudio",
  [TipoClasificacion.NEGATIVOS]: "Negativos",
  [TipoClasificacion.DESCARTADOS]: "Descartados",
  [TipoClasificacion.NOTIFICADOS]: "Notificados",
  [TipoClasificacion.CON_RESULTADO_MORTAL]: "Con resultado mortal",
  [TipoClasificacion.SIN_RESULTADO_MORTAL]: "Sin resultado mortal",
  [TipoClasificacion.REQUIERE_REVISION]: "Requiere revisión",
};

interface ClassificationSelectorProps {
  selectedClassifications: TipoClasificacion[];
  onClassificationChange: (classifications: TipoClasificacion[]) => void;
  placeholder?: string;
  disabled?: boolean;
  maxSelections?: number;
}

export const ClassificationSelector: React.FC<ClassificationSelectorProps> = ({
  selectedClassifications,
  onClassificationChange,
  placeholder = "Seleccionar clasificaciones...",
  disabled = false,
  maxSelections,
}) => {
  const [open, setOpen] = React.useState(false);

  const handleToggleClassification = (classification: TipoClasificacion) => {
    const isSelected = selectedClassifications.includes(classification);

    if (isSelected) {
      // Deseleccionar
      onClassificationChange(
        selectedClassifications.filter(c => c !== classification)
      );
    } else {
      // Seleccionar (si no hay límite o no se ha alcanzado)
      if (!maxSelections || selectedClassifications.length < maxSelections) {
        onClassificationChange([...selectedClassifications, classification]);
      }
    }
  };

  const handleClearAll = () => {
    onClassificationChange([]);
  };

  const getButtonLabel = () => {
    if (selectedClassifications.length === 0) {
      return placeholder;
    }
    if (selectedClassifications.length === 1) {
      return CLASSIFICATION_LABELS[selectedClassifications[0]];
    }
    return `${selectedClassifications.length} clasificaciones`;
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
          disabled={disabled}
        >
          <span className="truncate">{getButtonLabel()}</span>
          <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <Command>
          <CommandInput placeholder="Buscar clasificación..." />
          <CommandEmpty>No se encontraron clasificaciones.</CommandEmpty>
          <CommandGroup>
            {selectedClassifications.length > 0 && (
              <CommandItem
                onSelect={handleClearAll}
                className="justify-center text-sm text-gray-600"
              >
                Limpiar selección
              </CommandItem>
            )}
            {Object.values(TipoClasificacion).map((classification) => {
              const isSelected = selectedClassifications.includes(classification);
              const isDisabled = !isSelected && maxSelections &&
                selectedClassifications.length >= maxSelections;

              return (
                <CommandItem
                  key={classification}
                  value={CLASSIFICATION_LABELS[classification]}
                  onSelect={() => handleToggleClassification(classification)}
                  disabled={isDisabled}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <Check
                      className={`h-4 w-4 ${
                        isSelected ? 'opacity-100' : 'opacity-0'
                      }`}
                    />
                    <Badge
                      variant="outline"
                      className={`${CLASSIFICATION_COLORS[classification]} border`}
                    >
                      {CLASSIFICATION_LABELS[classification]}
                    </Badge>
                  </div>
                </CommandItem>
              );
            })}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

// Component to display selected classifications as badges
export const ClassificationBadges: React.FC<{
  classifications: TipoClasificacion[];
  onRemove?: (classification: TipoClasificacion) => void;
}> = ({ classifications, onRemove }) => {
  if (classifications.length === 0) {
    return (
      <span className="text-sm text-gray-500">
        Todas las clasificaciones
      </span>
    );
  }

  return (
    <div className="flex flex-wrap gap-1">
      {classifications.map((classification) => (
        <Badge
          key={classification}
          variant="outline"
          className={`${CLASSIFICATION_COLORS[classification]} border text-xs`}
        >
          {CLASSIFICATION_LABELS[classification]}
          {onRemove && (
            <button
              onClick={() => onRemove(classification)}
              className="ml-1 hover:opacity-70"
              aria-label={`Remover ${CLASSIFICATION_LABELS[classification]}`}
            >
              ×
            </button>
          )}
        </Badge>
      ))}
    </div>
  );
};