"use client";

import { GeoJSON } from "react-leaflet";
import type { GeoJSONFeatureCollection, GeoJSONFeature } from "@/features/mapa/api";
import type { PathOptions } from "leaflet";
import { useMemo } from "react";

interface ChoroplethLayerProps {
  data: GeoJSONFeatureCollection;
  colorField: "total_eventos" | "total_casos" | "tasa_incidencia" | "poblacion";
  colorScale?: string[]; // Array of colors from low to high
  onFeatureClick?: (feature: GeoJSONFeature) => void;
}

// Color for zero cases (distinct gray)
const ZERO_COLOR = "#e8e8e8";
// Color for no data (lighter gray with pattern feel)
const NO_DATA_COLOR = "#f5f5f5";

// Default color scale - more saturated for better contrast
// Starts with a visible light orange/yellow for low values
const DEFAULT_SCALE = [
  "#fee5d9", // Very light salmon (1+ case)
  "#fcbba1", // Light salmon
  "#fc9272", // Medium salmon
  "#fb6a4a", // Salmon-red
  "#ef3b2c", // Red
  "#cb181d", // Dark red
  "#99000d", // Very dark red
];

/**
 * Get color for a value using logarithmic scale for better differentiation
 * of low values (1, 2, 5 cases should look different)
 */
function getColor(
  value: number | null | undefined,
  max: number,
  colorScale: string[],
  useLogScale: boolean = true
): string {
  // No data
  if (value === null || value === undefined) {
    return NO_DATA_COLOR;
  }

  // Zero cases - distinct color
  if (value === 0) {
    return ZERO_COLOR;
  }

  // If max is 0 or 1, just use first color
  if (max <= 1) {
    return colorScale[0];
  }

  let ratio: number;

  if (useLogScale && max > 10) {
    // Logarithmic scale: better for epidemiological data with wide ranges
    // log(1) = 0, log(max) = max_log
    // This spreads out low values more
    const logValue = Math.log(value + 1);
    const logMax = Math.log(max + 1);
    ratio = logValue / logMax;
  } else {
    // Linear scale for small ranges
    ratio = value / max;
  }

  ratio = Math.min(Math.max(ratio, 0), 1);
  const index = Math.min(
    Math.floor(ratio * colorScale.length),
    colorScale.length - 1
  );

  return colorScale[index];
}

export function ChoroplethLayer({
  data,
  colorField,
  colorScale = DEFAULT_SCALE,
  onFeatureClick,
}: ChoroplethLayerProps) {
  // Calculate max value for color scaling
  const maxValue = useMemo(() => {
    let max = 0;
    for (const feature of data.features) {
      const value = feature.properties[colorField];
      if (typeof value === "number" && value > max) {
        max = value;
      }
    }
    return max;
  }, [data, colorField]);

  const style = (feature: GeoJSONFeature | undefined): PathOptions => {
    if (!feature) {
      return { fillColor: "#f0f0f0", weight: 1, color: "#666", fillOpacity: 0.7 };
    }

    const value = feature.properties[colorField];
    const color = getColor(
      typeof value === "number" ? value : null,
      maxValue,
      colorScale
    );

    return {
      fillColor: color,
      weight: 1,
      opacity: 1,
      color: "#666",
      fillOpacity: 0.7,
    };
  };

  const onEachFeature = (feature: GeoJSONFeature, layer: L.Layer) => {
    // Hover effects
    layer.on({
      mouseover: (e) => {
        const target = e.target;
        target.setStyle({
          weight: 3,
          color: "#333",
          fillOpacity: 0.9,
        });
        target.bringToFront();
      },
      mouseout: (e) => {
        const target = e.target;
        target.setStyle(style(feature));
      },
      click: () => {
        if (onFeatureClick) {
          onFeatureClick(feature);
        }
      },
    });

    // Tooltip content
    const props = feature.properties;
    const value = props[colorField];
    const valueStr = typeof value === "number"
      ? colorField === "tasa_incidencia"
        ? `${value.toFixed(2)} por 100k hab.`
        : value.toLocaleString()
      : "Sin datos";

    const tooltipContent = `
      <div class="text-sm">
        <div class="font-semibold">${props.nombre}</div>
        ${props.provincia ? `<div class="text-xs text-gray-500">${props.provincia}</div>` : ""}
        <div class="mt-1">
          <span class="font-medium">${
            colorField === "total_eventos" ? "Eventos" :
            colorField === "total_casos" ? "Casos" :
            colorField === "tasa_incidencia" ? "Tasa" :
            "Poblacion"
          }:</span> ${valueStr}
        </div>
        ${props.poblacion ? `<div class="text-xs text-gray-500">Pob: ${props.poblacion.toLocaleString()}</div>` : ""}
      </div>
    `;

    layer.bindTooltip(tooltipContent, {
      sticky: true,
      direction: "top",
      className: "choropleth-tooltip",
    });
  };

  // Need to cast because react-leaflet types don't match exactly
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const geoJSONData = data as any;

  return (
    <GeoJSON
      key={`${colorField}-${data.features.length}`}
      data={geoJSONData}
      style={style as (feature?: GeoJSON.Feature) => PathOptions}
      onEachFeature={onEachFeature as (feature: GeoJSON.Feature, layer: L.Layer) => void}
    />
  );
}

// Legend component
interface ChoroplethLegendProps {
  title: string;
  colorScale?: string[];
  maxValue: number;
  unit?: string;
}

/**
 * Generate legend labels using logarithmic scale to match the color function
 */
function getLogScaleLabels(maxValue: number, steps: number): string[] {
  if (maxValue <= 10) {
    // For small ranges, use linear labels
    return Array.from({ length: steps }, (_, i) =>
      Math.round((i / (steps - 1)) * maxValue).toString()
    );
  }

  // Logarithmic labels
  const labels: string[] = [];
  for (let i = 0; i < steps; i++) {
    const ratio = i / (steps - 1);
    // Inverse of the log scale formula
    const value = Math.round(Math.exp(ratio * Math.log(maxValue + 1)) - 1);
    labels.push(value.toLocaleString());
  }
  return labels;
}

export function ChoroplethLegend({
  title,
  colorScale = DEFAULT_SCALE,
  maxValue,
  unit = "",
}: ChoroplethLegendProps) {
  const labels = getLogScaleLabels(maxValue, colorScale.length);

  return (
    <div className="absolute bottom-8 left-4 z-[1000] bg-white rounded-lg shadow-lg p-3 min-w-[140px]">
      <div className="text-sm font-semibold mb-2">{title}</div>
      <div className="flex flex-col gap-1">
        {/* Zero cases */}
        <div className="flex items-center gap-2">
          <div
            className="w-5 h-4 rounded-sm border border-gray-300"
            style={{ backgroundColor: ZERO_COLOR }}
          />
          <span className="text-xs text-gray-600">0{unit}</span>
        </div>
        {/* Color scale for 1+ cases */}
        {colorScale.map((color, i) => {
          const label = i === 0 ? "1+" : labels[i];
          return (
            <div key={i} className="flex items-center gap-2">
              <div
                className="w-5 h-4 rounded-sm border border-gray-300"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-600">
                {label}{unit}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-2">
        <div
          className="w-5 h-4 rounded-sm border border-gray-300"
          style={{ backgroundColor: NO_DATA_COLOR }}
        />
        <span className="text-xs text-gray-500">Sin datos</span>
      </div>
    </div>
  );
}
