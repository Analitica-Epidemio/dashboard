"use client";

/**
 * Series Editor Component
 *
 * Permite configurar las series de un gráfico:
 * - Label de cada serie
 * - Color de cada serie
 * - Qué códigos (eventos o agentes) agrupa cada serie
 */

import { useState, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronUp,
  Palette,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Colores predefinidos para series
const PRESET_COLORS = [
  "#2196F3", // blue
  "#F44336", // red
  "#4CAF50", // green
  "#FF9800", // orange
  "#9C27B0", // purple
  "#00BCD4", // cyan
  "#E91E63", // pink
  "#795548", // brown
  "#607D8B", // blue-grey
  "#FFEB3B", // yellow
];

export interface SerieConfig {
  label: string;
  color: string;
  valores: string[];
}

interface SeriesEditorProps {
  series: SerieConfig[];
  onChange: (series: SerieConfig[]) => void;
  availableItems: { codigo: string; nombre: string }[];
  itemType: "evento" | "agente";
  maxSeries?: number;
}

export function SeriesEditor({
  series,
  onChange,
  availableItems,
  itemType,
  maxSeries = 10,
}: SeriesEditorProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const [itemSearch, setItemSearch] = useState("");

  // Filter available items by search
  const filteredItems = useMemo(() => {
    if (!itemSearch.trim()) return availableItems;
    const lower = itemSearch.toLowerCase();
    return availableItems.filter(
      (item) =>
        item.nombre.toLowerCase().includes(lower) ||
        item.codigo.toLowerCase().includes(lower)
    );
  }, [availableItems, itemSearch]);

  // Get next available color
  const getNextColor = useCallback(() => {
    const usedColors = series.map((s) => s.color);
    return PRESET_COLORS.find((c) => !usedColors.includes(c)) || PRESET_COLORS[0];
  }, [series]);

  // Add new series
  const addSeries = useCallback(() => {
    if (series.length >= maxSeries) return;

    const newSeries: SerieConfig = {
      label: `Serie ${series.length + 1}`,
      color: getNextColor(),
      valores: [],
    };
    onChange([...series, newSeries]);
    setExpandedIndex(series.length);
  }, [series, maxSeries, getNextColor, onChange]);

  // Remove series
  const removeSeries = useCallback(
    (index: number) => {
      const newSeries = series.filter((_, i) => i !== index);
      onChange(newSeries);
      if (expandedIndex === index) {
        setExpandedIndex(newSeries.length > 0 ? 0 : null);
      } else if (expandedIndex !== null && expandedIndex > index) {
        setExpandedIndex(expandedIndex - 1);
      }
    },
    [series, expandedIndex, onChange]
  );

  // Update series
  const updateSeries = useCallback(
    (index: number, updates: Partial<SerieConfig>) => {
      const newSeries = series.map((s, i) =>
        i === index ? { ...s, ...updates } : s
      );
      onChange(newSeries);
    },
    [series, onChange]
  );

  // Toggle valor in series
  const toggleValor = useCallback(
    (seriesIndex: number, codigo: string) => {
      const serie = series[seriesIndex];
      const valores = serie.valores.includes(codigo)
        ? serie.valores.filter((v) => v !== codigo)
        : [...serie.valores, codigo];
      updateSeries(seriesIndex, { valores });
    },
    [series, updateSeries]
  );

  // Move series up/down
  const moveSeries = useCallback(
    (index: number, direction: "up" | "down") => {
      const newIndex = direction === "up" ? index - 1 : index + 1;
      if (newIndex < 0 || newIndex >= series.length) return;

      const newSeries = [...series];
      [newSeries[index], newSeries[newIndex]] = [newSeries[newIndex], newSeries[index]];
      onChange(newSeries);
      setExpandedIndex(newIndex);
    },
    [series, onChange]
  );

  // Check if codigo is used in another series
  const isUsedInOtherSeries = useCallback(
    (codigo: string, currentSeriesIndex: number) => {
      return series.some(
        (s, i) => i !== currentSeriesIndex && s.valores.includes(codigo)
      );
    },
    [series]
  );

  const itemLabel = itemType === "evento" ? "eventos" : "agentes";

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">Series del gráfico</Label>
        <Badge variant="secondary" className="text-xs">
          {series.length} {series.length === 1 ? "serie" : "series"}
        </Badge>
      </div>

      {series.length === 0 ? (
        <div className="text-center py-6 border-2 border-dashed rounded-lg bg-muted/20">
          <p className="text-sm text-muted-foreground mb-3">
            No hay series configuradas
          </p>
          <Button variant="outline" size="sm" onClick={addSeries}>
            <Plus className="h-4 w-4 mr-1" />
            Agregar serie
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {series.map((serie, index) => {
            const isExpanded = expandedIndex === index;

            return (
              <div
                key={index}
                className={cn(
                  "border rounded-lg overflow-hidden transition-all",
                  isExpanded ? "bg-card shadow-sm" : "bg-muted/20"
                )}
              >
                {/* Header */}
                <div
                  className="flex items-center gap-2 p-3 cursor-pointer hover:bg-muted/30"
                  onClick={() => {
                    setExpandedIndex(isExpanded ? null : index);
                    setItemSearch(""); // Clear search when switching series
                  }}
                >
                  <GripVertical className="h-4 w-4 text-muted-foreground/50" />

                  {/* Color indicator */}
                  <div
                    className="w-4 h-4 rounded-full shrink-0 border"
                    style={{ backgroundColor: serie.color }}
                  />

                  {/* Label */}
                  <span className="flex-1 text-sm font-medium truncate">
                    {serie.label || `Serie ${index + 1}`}
                  </span>

                  {/* Valores count */}
                  <Badge variant="outline" className="text-xs">
                    {serie.valores.length} {itemLabel}
                  </Badge>

                  {/* Expand/collapse */}
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="p-3 pt-0 space-y-3 border-t">
                    {/* Label input */}
                    <div className="space-y-1.5">
                      <Label className="text-xs text-muted-foreground">
                        Nombre de la serie (aparece en leyenda)
                      </Label>
                      <Input
                        value={serie.label}
                        onChange={(e) =>
                          updateSeries(index, { label: e.target.value })
                        }
                        placeholder="Ej: Influenza A"
                        className="h-8 text-sm"
                      />
                    </div>

                    {/* Color picker */}
                    <div className="space-y-1.5">
                      <Label className="text-xs text-muted-foreground">
                        Color
                      </Label>
                      <div className="flex items-center gap-2 flex-wrap">
                        {PRESET_COLORS.map((color) => (
                          <button
                            key={color}
                            type="button"
                            className={cn(
                              "w-6 h-6 rounded-full border-2 transition-transform hover:scale-110",
                              serie.color === color
                                ? "border-foreground scale-110"
                                : "border-transparent"
                            )}
                            style={{ backgroundColor: color }}
                            onClick={() => updateSeries(index, { color })}
                          />
                        ))}
                        <div className="relative">
                          <input
                            type="color"
                            value={serie.color}
                            onChange={(e) =>
                              updateSeries(index, { color: e.target.value })
                            }
                            className="absolute inset-0 w-6 h-6 opacity-0 cursor-pointer"
                          />
                          <div className="w-6 h-6 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center">
                            <Palette className="h-3 w-3 text-muted-foreground" />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Valores selector */}
                    <div className="space-y-1.5">
                      <Label className="text-xs text-muted-foreground">
                        {itemType === "evento" ? "Eventos" : "Agentes"} que agrupa
                        esta serie
                      </Label>
                      {/* Search input */}
                      <div className="relative">
                        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                        <Input
                          placeholder={`Buscar ${itemType === "evento" ? "eventos" : "agentes"}...`}
                          value={itemSearch}
                          onChange={(e) => setItemSearch(e.target.value)}
                          className="h-8 pl-7 text-xs"
                        />
                      </div>
                      <div className="max-h-[150px] overflow-y-auto border rounded-md divide-y">
                        {filteredItems.length === 0 ? (
                          <p className="text-xs text-muted-foreground p-3 text-center">
                            No se encontraron resultados
                          </p>
                        ) : filteredItems.map((item) => {
                          const isSelected = serie.valores.includes(item.codigo);
                          const isUsedElsewhere = isUsedInOtherSeries(
                            item.codigo,
                            index
                          );

                          return (
                            <div
                              key={item.codigo}
                              className={cn(
                                "flex items-center gap-2 px-2 py-1.5 cursor-pointer transition-colors",
                                isSelected
                                  ? "bg-primary/10"
                                  : isUsedElsewhere
                                    ? "bg-muted/50 opacity-50"
                                    : "hover:bg-muted/30"
                              )}
                              onClick={() => toggleValor(index, item.codigo)}
                            >
                              <div
                                className={cn(
                                  "w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-all",
                                  isSelected
                                    ? "bg-primary border-primary"
                                    : "border-muted-foreground/30"
                                )}
                              >
                                {isSelected && (
                                  <svg
                                    className="h-3 w-3 text-primary-foreground"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={3}
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      d="M5 13l4 4L19 7"
                                    />
                                  </svg>
                                )}
                              </div>
                              <span className="text-xs truncate flex-1">
                                {item.nombre}
                              </span>
                              {isUsedElsewhere && !isSelected && (
                                <Badge
                                  variant="outline"
                                  className="text-[9px] px-1 py-0"
                                >
                                  En otra serie
                                </Badge>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      {serie.valores.length > 0 && (
                        <p className="text-xs text-muted-foreground">
                          Los datos de estos {serie.valores.length} {itemLabel} se
                          sumarán bajo el label &quot;{serie.label}&quot;
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          disabled={index === 0}
                          onClick={() => moveSeries(index, "up")}
                        >
                          <ChevronUp className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 px-2"
                          disabled={index === series.length - 1}
                          onClick={() => moveSeries(index, "down")}
                        >
                          <ChevronDown className="h-4 w-4" />
                        </Button>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => removeSeries(index)}
                      >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Eliminar
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add button */}
      {series.length > 0 && series.length < maxSeries && (
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={addSeries}
        >
          <Plus className="h-4 w-4 mr-1" />
          Agregar serie
        </Button>
      )}

      {/* Help text */}
      <p className="text-xs text-muted-foreground">
        Cada serie aparece como una línea/barra separada en el gráfico. Podés
        agrupar múltiples {itemLabel} bajo una misma serie.
      </p>
    </div>
  );
}
