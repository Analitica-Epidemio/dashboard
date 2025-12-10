/**
 * Classification Selector Component
 * Allows selecting multiple epidemiological classifications for filtering
 */

import React from "react";
import { Check, ChevronDown } from "lucide-react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { TipoClasificacion } from "@/features/eventos/api";

// Re-export TipoClasificacion for use by other components
export type { TipoClasificacion };

// Valores de clasificación epidemiológica
const CLASIFICACIONES: TipoClasificacion[] = [
  "CONFIRMADOS",
  "SOSPECHOSOS",
  "PROBABLES",
  "EN_ESTUDIO",
  "NEGATIVOS",
  "DESCARTADOS",
  "NOTIFICADOS",
  "CON_RESULTADO_MORTAL",
  "SIN_RESULTADO_MORTAL",
  "REQUIERE_REVISION",
] as const;

// Colores para cada clasificación
const CLASSIFICATION_COLORS: Record<TipoClasificacion, string> = {
  "CONFIRMADOS": "bg-red-100 text-red-800 border-red-300",
  "SOSPECHOSOS": "bg-yellow-100 text-yellow-800 border-yellow-300",
  "PROBABLES": "bg-orange-100 text-orange-800 border-orange-300",
  "EN_ESTUDIO": "bg-blue-100 text-blue-800 border-blue-300",
  "NEGATIVOS": "bg-green-100 text-green-800 border-green-300",
  "DESCARTADOS": "bg-gray-100 text-gray-800 border-gray-300",
  "NOTIFICADOS": "bg-purple-100 text-purple-800 border-purple-300",
  "CON_RESULTADO_MORTAL": "bg-black text-white border-black",
  "SIN_RESULTADO_MORTAL": "bg-gray-200 text-gray-700 border-gray-400",
  "REQUIERE_REVISION": "bg-pink-100 text-pink-800 border-pink-300",
  "TODOS": "bg-slate-100 text-slate-800 border-slate-300",
};

// Labels amigables
const CLASSIFICATION_LABELS: Record<TipoClasificacion, string> = {
  "CONFIRMADOS": "Confirmados",
  "SOSPECHOSOS": "Sospechosos",
  "PROBABLES": "Probables",
  "EN_ESTUDIO": "En estudio",
  "NEGATIVOS": "Negativos",
  "DESCARTADOS": "Descartados",
  "NOTIFICADOS": "Notificados",
  "CON_RESULTADO_MORTAL": "Con resultado mortal",
  "SIN_RESULTADO_MORTAL": "Sin resultado mortal",
  "REQUIERE_REVISION": "Requiere revisión",
  "TODOS": "Todos",
};

interface ClassificationSelectorProps {
  selectedClassifications: TipoClasificacion[];
  onClassificationChange: (classifications: TipoClasificacion[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const ClassificationSelector: React.FC<ClassificationSelectorProps> = ({
  selectedClassifications,
  onClassificationChange,
  placeholder = "Seleccionar clasificaciones...",
  disabled = false,
}) => {
  const [open, setOpen] = React.useState(false);

  const handleToggleClassification = (classification: TipoClasificacion) => {
    const isSelected = selectedClassifications.includes(classification);

    if (isSelected) {
      // Deseleccionar
      onClassificationChange(
        selectedClassifications.filter((c) => c !== classification)
      );
    } else {
      onClassificationChange([...selectedClassifications, classification]);
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
    <Popover open={open} onOpenChange={setOpen} modal={true}>
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
      <PopoverContent className="w-full p-0 z-[100]" align="start">
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
            {CLASIFICACIONES.map((classification) => {
              const isSelected =
                selectedClassifications.includes(classification);

              return (
                <CommandItem
                  key={classification}
                  value={CLASSIFICATION_LABELS[classification]}
                  onSelect={() => handleToggleClassification(classification)}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-2">
                    <Check
                      className={`h-4 w-4 ${
                        isSelected ? "opacity-100" : "opacity-0"
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
      <span className="text-sm text-gray-500">Todas las clasificaciones</span>
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
