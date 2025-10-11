"use client";

import { useEffect, useState, useRef, useMemo } from "react";
import { MapContainer, TileLayer, useMap, GeoJSON } from "react-leaflet";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEventosMapa, type EventoMapaItem } from "@/lib/api/mapa";
import * as topojson from "topojson-client";
import "leaflet/dist/leaflet.css";
import "./mapa-styles.css";
import L from "leaflet";
import type { Feature, FeatureCollection, Geometry } from "geojson";
import departamentosIdsData from "./departamentos_ids.json";

// Fix Leaflet default icon issue with Next.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
});

interface MapaInteractivoProps {
  nivel: "provincia" | "departamento" | "localidad";
  onNivelChange: (nivel: "provincia" | "departamento" | "localidad") => void;
  selectedProvinciaId?: number | null;
  selectedDepartamentoId?: number | null;
  onProvinciaSelect?: (id: number | null) => void;
  onDepartamentoSelect?: (id: number | null) => void;
}

// Ya no necesitamos coordenadas de provincias ni mapeo de nombres
// porque solo mostramos departamentos

// Función para interpolar entre dos colores
function interpolateColor(color1: [number, number, number], color2: [number, number, number], factor: number): string {
  const r = Math.round(color1[0] + factor * (color2[0] - color1[0]));
  const g = Math.round(color1[1] + factor * (color2[1] - color1[1]));
  const b = Math.round(color1[2] + factor * (color2[2] - color1[2]));
  return `rgb(${r}, ${g}, ${b})`;
}

// Paleta de colores: verde → amarillo → naranja → rojo
const COLOR_PALETTE: Array<[number, number, number]> = [
  [34, 197, 94],   // verde (#22c55e)
  [132, 204, 22],  // lima (#84cc16)
  [234, 179, 8],   // amarillo (#eab308)
  [251, 146, 60],  // naranja claro (#fb923c)
  [249, 115, 22],  // naranja (#f97316)
  [239, 68, 68],   // rojo claro (#ef4444)
  [220, 38, 38],   // rojo (#dc2626)
  [153, 27, 27],   // rojo oscuro (#991b1b)
];

// Calcular percentiles para distribución más realista
function calculateQuantiles(values: number[], quantiles: number[]): number[] {
  const sorted = [...values].sort((a, b) => a - b);
  return quantiles.map(q => {
    const index = Math.ceil(sorted.length * q) - 1;
    return sorted[Math.max(0, index)] || 0;
  });
}

function getColorForEventos(total: number, quantiles: number[]): string {
  if (total === 0) return "#e5e7eb"; // gris claro

  // Encontrar en qué cuantil cae el valor
  let quantileIndex = 0;
  for (let i = 0; i < quantiles.length; i++) {
    if (total <= quantiles[i]) {
      quantileIndex = i;
      break;
    }
  }

  // Si es mayor que todos los cuantiles, usar el último color
  if (total > quantiles[quantiles.length - 1]) {
    const lastColor = COLOR_PALETTE[COLOR_PALETTE.length - 1];
    return `rgb(${lastColor[0]}, ${lastColor[1]}, ${lastColor[2]})`;
  }

  // Interpolar entre colores basándonos en la posición dentro del cuantil
  const colorIndex = Math.min(quantileIndex, COLOR_PALETTE.length - 2);
  const lowerBound = quantileIndex === 0 ? 0 : quantiles[quantileIndex - 1];
  const upperBound = quantiles[quantileIndex];

  let factor = 0;
  if (upperBound > lowerBound) {
    factor = (total - lowerBound) / (upperBound - lowerBound);
  }

  return interpolateColor(COLOR_PALETTE[colorIndex], COLOR_PALETTE[colorIndex + 1], factor);
}

function MapController({
  onZoomChange,
}: {
  onZoomChange: (zoom: number) => void;
}) {
  const map = useMap();

  useEffect(() => {
    const handleZoomEnd = () => {
      onZoomChange(map.getZoom());
    };

    map.on('zoomend', handleZoomEnd);

    return () => {
      map.off('zoomend', handleZoomEnd);
    };
  }, [map, onZoomChange]);

  return null;
}

// Normalizar nombre para matching
const normalizeName = (name: string): string => {
  return name
    .toUpperCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, ""); // quitar tildes
};

// Mapeo de departamentos (importado desde JSON)
const DEPARTAMENTOS_IDS = departamentosIdsData as Record<string, {
  provincia: string;
  departamento: string;
  id_provincia_indec: number;
  id_departamento_indec: number;
}>;

export function MapaInteractivo({
  nivel: externalNivel,
  onNivelChange,
  selectedProvinciaId: externalProvinciaId,
  selectedDepartamentoId: externalDepartamentoId,
  onProvinciaSelect,
  onDepartamentoSelect,
}: MapaInteractivoProps) {
  const [currentZoom, setCurrentZoom] = useState(6); // Empezar en nivel departamento
  const [geoJsonData, setGeoJsonData] = useState<FeatureCollection | null>(null);
  const [loadingTopoJson, setLoadingTopoJson] = useState(true);
  const geoJsonRef = useRef<L.GeoJSON>(null);

  // Usar Canvas renderer para mejor performance
  const canvasRenderer = useMemo(() => L.canvas({ padding: 0.5 }), []);

  // Determinar nivel automáticamente según el zoom
  // Empezamos directamente en departamento (zoom inicial 6)
  const nivel = useMemo(() => {
    if (currentZoom < 6) return "departamento"; // siempre departamento en zoom bajo
    if (currentZoom < 10) return "departamento";
    return "localidad";
  }, [currentZoom]);

  // Usar el hook con autenticación
  const { data, isLoading, error } = useEventosMapa({
    nivel,
    id_provincia_indec: null,
    id_departamento_indec: null,
  });

  const eventos = data?.data?.items || [];
  const loading = isLoading;

  // Ya no necesitamos mapa de eventos por provincia porque solo mostramos departamentos

  // Calcular escala de colores basada en los datos reales
  const colorScale = useMemo(() => {
    if (eventos.length === 0) return [1, 10, 50, 100, 500, 1000, 5000];

    const totales = eventos.map((e: EventoMapaItem) => e.total_eventos).filter(t => t > 0);
    if (totales.length === 0) return [1, 10, 50, 100, 500, 1000, 5000];

    const min = Math.min(...totales);
    const max = Math.max(...totales);

    console.log("📊 Min eventos:", min, "Max eventos:", max);

    // Si la distribución tiene mucha variabilidad (max >> min), usar escala logarítmica
    if (max / min > 100) {
      // Escala logarítmica para mejor distribución visual
      const logMin = Math.log10(Math.max(1, min));
      const logMax = Math.log10(max);
      const step = (logMax - logMin) / 7;

      const scale = Array.from({ length: 7 }, (_, i) => {
        return Math.round(Math.pow(10, logMin + step * (i + 1)));
      });

      console.log("📊 Usando escala logarítmica:", scale);
      return scale;
    } else {
      // Para distribuciones más uniformes, usar cuantiles
      const calculatedQuantiles = calculateQuantiles(totales, [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]);
      console.log("📊 Usando cuantiles:", calculatedQuantiles);
      return calculatedQuantiles;
    }
  }, [eventos]);

  // Cargar TopoJSON una sola vez al montar el componente
  useEffect(() => {
    const topoJsonFile = "/topojson/departamentos-argentina.topojson";
    const objectName = "departamentos-argentina";

    fetch(topoJsonFile)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then((topoData) => {
        // Convertir TopoJSON a GeoJSON
        const geoJson = topojson.feature(topoData, topoData.objects[objectName]) as unknown as FeatureCollection;
        setGeoJsonData(geoJson);
        setLoadingTopoJson(false);
      })
      .catch((err) => {
        console.error("Error cargando TopoJSON:", err);
        setGeoJsonData(null);
        setLoadingTopoJson(false);
      });
  }, []); // Solo cargar una vez

  // Procesar GeoJSON - siempre mostrar departamentos individuales
  const processedGeoJsonData = useMemo(() => {
    if (!geoJsonData) return null;

    // Siempre procesar como departamentos individuales con sus IDs
    let matchedCount = 0;
    const departamentosConIds: Feature[] = geoJsonData.features.map((feature: Feature<Geometry>) => {
      const provincia = feature.properties?.provincia;
      const departamento = feature.properties?.departamento || feature.properties?.nombre;

      if (provincia && departamento) {
        const key = `${normalizeName(provincia)}_${normalizeName(departamento)}`;
        const deptInfo = DEPARTAMENTOS_IDS[key];

        if (deptInfo) {
          matchedCount++;
          return {
            ...feature,
            properties: {
              ...feature.properties,
              id_provincia_indec: deptInfo.id_provincia_indec,
              id_departamento_indec: deptInfo.id_departamento_indec,
            },
          };
        }
      }

      return feature;
    });

    console.log(`🔍 GeoJSON: Matched ${matchedCount} de ${geoJsonData.features.length} departamentos con IDs`);

    // Mostrar algunos ejemplos
    const ejemplos = departamentosConIds.slice(0, 3).map(f => ({
      nombre: f.properties?.departamento,
      provincia: f.properties?.provincia,
      id_prov: f.properties?.id_provincia_indec,
      id_dept: f.properties?.id_departamento_indec,
    }));
    console.log("🔍 Ejemplos de departamentos procesados:", ejemplos);

    return {
      type: "FeatureCollection" as const,
      features: departamentosConIds,
    };
  }, [geoJsonData]); // Removido 'nivel' de las dependencias ya que siempre procesamos igual

  // Notificar cambios de nivel al padre
  useEffect(() => {
    if (onNivelChange) {
      onNivelChange(nivel);
    }
  }, [nivel, onNivelChange]);

  const handleZoomChange = (zoom: number) => {
    setCurrentZoom(zoom);
  };

  // Ya no necesitamos estilos para provincias porque solo mostramos departamentos

  // Crear un mapa de eventos por departamento para coloreado
  const eventosPorDepartamento = useMemo(() => {
    const map = eventos.reduce((acc: Record<string, EventoMapaItem>, evento: EventoMapaItem) => {
      if (evento.id_departamento_indec && evento.id_provincia_indec) {
        const key = `${evento.id_provincia_indec}_${evento.id_departamento_indec}`;
        acc[key] = evento;
      }
      return acc;
    }, {} as Record<string, EventoMapaItem>);

    // Debug: mostrar primeros eventos
    console.log("🔍 Eventos por departamento (primeros 5):", Object.entries(map).slice(0, 5));
    console.log("🔍 Total eventos mapeados:", Object.keys(map).length);

    return map;
  }, [eventos]);

  // Estilo para departamentos según eventos
  const getDepartamentoStyle = (feature?: Feature) => {
    if (!feature?.properties) {
      return {
        fillColor: "#e5e7eb",
        weight: 1,
        opacity: 0.5,
        color: "#9ca3af",
        fillOpacity: 0.3,
      };
    }

    // Intentar obtener los IDs del departamento
    const props = feature.properties;
    const idProvinciaIndec = props.id_provincia_indec;
    const idDepartamentoIndec = props.id_departamento_indec;

    // Si no tenemos IDs, devolver gris
    if (!idProvinciaIndec || !idDepartamentoIndec) {
      return {
        fillColor: "#e5e7eb",
        weight: 1,
        opacity: 0.5,
        color: "#9ca3af",
        fillOpacity: 0.3,
      };
    }

    const key = `${idProvinciaIndec}_${idDepartamentoIndec}`;
    const eventoData = eventosPorDepartamento[key];
    const total = eventoData?.total_eventos || 0;

    // Debug para el primer departamento con eventos
    if (total > 0 && Math.random() < 0.01) {
      console.log(`🎨 Coloreando ${props.departamento}:`, {
        key,
        total,
        color: getColorForEventos(total, colorScale),
      });
    }

    if (total === 0) {
      return {
        fillColor: "#e5e7eb",
        weight: 1,
        opacity: 0.5,
        color: "#9ca3af",
        fillOpacity: 0.3,
      };
    }

    return {
      fillColor: getColorForEventos(total, colorScale),
      weight: 1.5,
      opacity: 1,
      color: "#ffffff",
      fillOpacity: 0.7,
    };
  };

  // Ya no necesitamos handlers para provincias porque solo mostramos departamentos

  // Eventos de interacción con departamentos
  const onEachDepartamentoFeature = (feature: Feature, layer: L.Layer) => {
    const departamento = feature.properties?.departamento || feature.properties?.nombre;
    const provincia = feature.properties?.provincia;
    const idProvinciaIndec = feature.properties?.id_provincia_indec;
    const idDepartamentoIndec = feature.properties?.id_departamento_indec;

    // Guardar el estilo original en una propiedad custom del layer
    const initialStyle = getDepartamentoStyle(feature);
    (layer as any)._initialStyle = initialStyle;

    layer.on({
      mouseover: (e) => {
        const layer = e.target;
        layer.setStyle({
          weight: 3,
          color: "#000",
          fillOpacity: 0.9,
        });
        layer.bringToFront();
      },
      mouseout: (e) => {
        // Restaurar el estilo guardado
        const savedStyle = (e.target as any)._initialStyle;
        if (savedStyle) {
          e.target.setStyle(savedStyle);
        }
      },
    });

    // Tooltip estático con los datos iniciales
    const key = idProvinciaIndec && idDepartamentoIndec ? `${idProvinciaIndec}_${idDepartamentoIndec}` : null;
    const eventoData = key ? eventosPorDepartamento[key] : null;
    const tooltipContent = `
      <div style="padding: 8px;">
        <strong>${departamento}</strong><br/>
        <span style="color: #666; font-size: 12px;">${provincia}</span><br/>
        <span style="color: #666;">Eventos: <strong>${eventoData?.total_eventos || 0}</strong></span><br/>
        <span style="font-size: 11px; color: #999;">Haz zoom para ver localidades</span>
      </div>
    `;

    layer.bindTooltip(tooltipContent, {
      permanent: false,
      direction: "center",
      className: "custom-tooltip",
    });
  };


  const getNivelLabel = () => {
    switch (nivel) {
      case "provincia":
        return { title: "Provincias", description: "Haz zoom para ver departamentos", color: "bg-blue-500" };
      case "departamento":
        return { title: "Departamentos", description: "Haz zoom para ver localidades", color: "bg-blue-500" };
      case "localidad":
        return { title: "Localidades", description: "Vista detallada", color: "bg-purple-500" };
    }
  };

  const nivelInfo = getNivelLabel();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <CardTitle>Mapa de Eventos Epidemiologicos</CardTitle>
            <CardDescription className="mt-2">
              Explora la distribución geográfica de eventos epidemiológicos
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${nivelInfo.color}`}></div>
              <div className="text-sm">
                <div className="font-semibold">{nivelInfo.title}</div>
                <div className="text-xs text-muted-foreground">{nivelInfo.description}</div>
              </div>
            </div>
            <div className="text-sm text-muted-foreground px-3 py-1.5 bg-gray-50 rounded-lg">
              Zoom: <span className="font-mono font-semibold">{currentZoom.toFixed(1)}</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="text-red-500 text-center py-4 mb-4 bg-red-50 rounded-lg border border-red-200">
            <strong>Error:</strong> No se pudieron cargar los eventos del mapa
          </div>
        )}

        {(loading || loadingTopoJson) && (
          <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-[1000] bg-white shadow-lg rounded-lg px-4 py-3 flex items-center gap-3 border">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-sm font-medium">
              {loadingTopoJson ? "Cargando límites geográficos..." : "Cargando eventos..."}
            </span>
          </div>
        )}

        <div style={{ height: "600px", width: "100%" }}>
          <MapContainer
            center={[-38.416097, -63.616671]}
            zoom={6}
            minZoom={5}
            maxZoom={12}
            maxBounds={[
              [-56.0, -77.0], // Suroeste - más margen hacia el oeste
              [-20.0, -52.0], // Noreste - más margen
            ]}
            maxBoundsViscosity={0.7}
            style={{ height: "100%", width: "100%", borderRadius: "8px" }}
            scrollWheelZoom={true}
            preferCanvas={true}
            zoomAnimation={true}
            markerZoomAnimation={true}
          >
            <MapController onZoomChange={handleZoomChange} />

            {/* Usar CartoDB Positron que tiene colores más suaves */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              subdomains="abcd"
            />

            {/* Capa de departamentos/localidades con TopoJSON */}
            {processedGeoJsonData && !loadingTopoJson && !loading && eventos.length > 0 && (
              <GeoJSON
                key={nivel}
                ref={geoJsonRef}
                data={processedGeoJsonData}
                style={getDepartamentoStyle}
                onEachFeature={onEachDepartamentoFeature}
                renderer={canvasRenderer}
              />
            )}
          </MapContainer>
        </div>

        {!loading && eventos.length > 0 && (
          <div className="mt-4 space-y-3">
            <div className="text-muted-foreground text-sm">
              Total de ubicaciones: <strong>{eventos.length}</strong>
            </div>

            {/* Leyenda con gradiente */}
            <div className="flex flex-col gap-2">
              <div className="text-xs font-semibold text-gray-700">Escala de eventos (basada en distribución real)</div>
              <div className="flex items-center gap-3">
                {/* Gradiente visual */}
                <div
                  className="h-6 flex-1 rounded-md border border-gray-300"
                  style={{
                    background: `linear-gradient(to right,
                      #e5e7eb 0%,
                      rgb(${COLOR_PALETTE[0].join(',')}) 5%,
                      rgb(${COLOR_PALETTE[1].join(',')}) 18%,
                      rgb(${COLOR_PALETTE[2].join(',')}) 31%,
                      rgb(${COLOR_PALETTE[3].join(',')}) 44%,
                      rgb(${COLOR_PALETTE[4].join(',')}) 57%,
                      rgb(${COLOR_PALETTE[5].join(',')}) 70%,
                      rgb(${COLOR_PALETTE[6].join(',')}) 83%,
                      rgb(${COLOR_PALETTE[7].join(',')}) 100%
                    )`
                  }}
                ></div>
              </div>

              {/* Etiquetas con valores de la escala */}
              <div className="flex justify-between text-xs text-gray-600 px-1">
                <span>0</span>
                {colorScale.map((value, i) => (
                  <span key={i} className="font-mono">{value >= 1000 ? `${(value/1000).toFixed(1)}k` : Math.round(value)}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {!loading && eventos.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No hay eventos para mostrar en este nivel
          </div>
        )}
      </CardContent>
    </Card>
  );
}
