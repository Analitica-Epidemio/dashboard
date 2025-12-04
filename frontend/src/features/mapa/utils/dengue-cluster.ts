/**
 * Algoritmo de clustering epidemiológico para Dengue/Arbovirosis
 *
 * Parámetros basados en evidencia epidemiológica:
 * - Radio: 200m (rango de vuelo del mosquito Aedes aegypti)
 * - Ventana temporal: 15-20 días (ciclo completo de transmisión)
 *
 * Fuente: OPS/OMS - Guía para la vigilancia epidemiológica de dengue
 */

import type { DomicilioMapaItem } from "../api";

// Configuración hardcodeada para dengue (basada en evidencia epidemiológica)
export const DENGUE_CLUSTER_CONFIG = {
  // Radio máximo en metros para considerar casos relacionados
  // Basado en el rango de vuelo del Aedes aegypti (~100-400m, usamos 200m conservador)
  RADIUS_METERS: 200,

  // Ventana temporal en días para considerar casos relacionados
  // Basado en: incubación humano (4-10d) + ciclo en mosquito (8-12d) + incubación nuevo humano
  WINDOW_DAYS: 18,

  // Mínimo de casos para considerar un cluster activo
  MIN_CASES_FOR_CLUSTER: 2,

  // Tipos de ENO que aplican para este clustering (dengue y arbovirosis relacionadas)
  TIPOS_ENO_DENGUE: [
    "Dengue",
    "Dengue con signos de alarma",
    "Dengue grave",
    "Fiebre Chikungunya",
    "Enfermedad por Virus del Zika",
  ],
} as const;

export interface DengueClusterEvent {
  id: number;
  domicilioId: number;
  lat: number;
  lng: number;
  fecha: Date;
  tipoNombre: string;
}

export interface DengueCluster {
  id: string;
  // Centro del cluster (promedio de coordenadas)
  centerLat: number;
  centerLng: number;
  // Radio del cluster en metros (puede ser > 200m si hay casos dispersos)
  radiusMeters: number;
  // Casos incluidos en el cluster
  cases: DengueClusterEvent[];
  // Estadísticas
  totalCases: number;
  dateRange: {
    start: Date;
    end: Date;
  };
  // Si el cluster está "activo" (tiene casos recientes)
  isActive: boolean;
  // Domicilios únicos afectados
  uniqueDomicilios: number;
}

/**
 * Calcula la distancia en metros entre dos puntos geográficos
 * usando la fórmula de Haversine
 */
function haversineDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371000; // Radio de la Tierra en metros
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Filtra domicilios que tienen eventos de dengue/arbovirosis
 */
export function filterDengueDomicilios(
  domicilios: DomicilioMapaItem[]
): DomicilioMapaItem[] {
  return domicilios.filter((dom) => {
    const tipos = Object.keys(dom.tipos_eventos || {});
    return tipos.some((tipo) =>
      DENGUE_CLUSTER_CONFIG.TIPOS_ENO_DENGUE.some(
        (dengueType) => tipo.toLowerCase().includes(dengueType.toLowerCase())
      )
    );
  });
}

/**
 * Algoritmo principal de clustering usando DBSCAN simplificado
 *
 * 1. Filtra solo eventos de dengue
 * 2. Agrupa por proximidad espacial (200m)
 * 3. Agrupa por proximidad temporal (18 días)
 * 4. Genera clusters con estadísticas
 */
export function computeDengueClusters(
  events: DengueClusterEvent[],
  config = DENGUE_CLUSTER_CONFIG
): DengueCluster[] {
  if (events.length < config.MIN_CASES_FOR_CLUSTER) {
    return [];
  }

  // Ordenar eventos por fecha
  const sortedEvents = [...events].sort(
    (a, b) => a.fecha.getTime() - b.fecha.getTime()
  );

  const visited = new Set<number>();
  const clusters: DengueCluster[] = [];

  for (const event of sortedEvents) {
    if (visited.has(event.id)) continue;

    // Buscar vecinos dentro del radio y ventana temporal
    const neighbors = findNeighbors(event, sortedEvents, config, visited);

    if (neighbors.length >= config.MIN_CASES_FOR_CLUSTER) {
      // Expandir cluster
      const clusterEvents = expandCluster(
        event,
        neighbors,
        sortedEvents,
        config,
        visited
      );

      if (clusterEvents.length >= config.MIN_CASES_FOR_CLUSTER) {
        clusters.push(createCluster(clusterEvents, clusters.length));
      }
    }
  }

  return clusters;
}

/**
 * Encuentra vecinos de un evento dentro del radio y ventana temporal
 */
function findNeighbors(
  event: DengueClusterEvent,
  allEvents: DengueClusterEvent[],
  config: typeof DENGUE_CLUSTER_CONFIG,
  visited: Set<number>
): DengueClusterEvent[] {
  const windowMs = config.WINDOW_DAYS * 24 * 60 * 60 * 1000;

  return allEvents.filter((other) => {
    if (other.id === event.id || visited.has(other.id)) return false;

    // Verificar proximidad temporal
    const timeDiff = Math.abs(event.fecha.getTime() - other.fecha.getTime());
    if (timeDiff > windowMs) return false;

    // Verificar proximidad espacial
    const distance = haversineDistance(
      event.lat,
      event.lng,
      other.lat,
      other.lng
    );
    return distance <= config.RADIUS_METERS;
  });
}

/**
 * Expande un cluster agregando vecinos de vecinos (DBSCAN)
 */
function expandCluster(
  seedEvent: DengueClusterEvent,
  neighbors: DengueClusterEvent[],
  allEvents: DengueClusterEvent[],
  config: typeof DENGUE_CLUSTER_CONFIG,
  visited: Set<number>
): DengueClusterEvent[] {
  const cluster: DengueClusterEvent[] = [seedEvent];
  visited.add(seedEvent.id);

  const queue = [...neighbors];

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current.id)) continue;

    visited.add(current.id);
    cluster.push(current);

    // Buscar vecinos del vecino
    const currentNeighbors = findNeighbors(current, allEvents, config, visited);
    if (currentNeighbors.length >= config.MIN_CASES_FOR_CLUSTER) {
      queue.push(...currentNeighbors);
    }
  }

  return cluster;
}

/**
 * Crea un objeto cluster con estadísticas calculadas
 */
function createCluster(
  events: DengueClusterEvent[],
  index: number
): DengueCluster {
  // Calcular centro (promedio de coordenadas)
  const centerLat = events.reduce((sum, e) => sum + e.lat, 0) / events.length;
  const centerLng = events.reduce((sum, e) => sum + e.lng, 0) / events.length;

  // Calcular radio máximo desde el centro
  let maxRadius: number = DENGUE_CLUSTER_CONFIG.RADIUS_METERS;
  for (const event of events) {
    const dist = haversineDistance(centerLat, centerLng, event.lat, event.lng);
    if (dist > maxRadius) maxRadius = dist;
  }
  // Agregar un pequeño margen
  maxRadius = Math.max(maxRadius * 1.1, DENGUE_CLUSTER_CONFIG.RADIUS_METERS as number);

  // Calcular rango de fechas
  const dates = events.map((e) => e.fecha.getTime());
  const minDate = new Date(Math.min(...dates));
  const maxDate = new Date(Math.max(...dates));

  // Verificar si está activo (tiene casos en los últimos 7 días)
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const isActive = events.some((e) => e.fecha >= sevenDaysAgo);

  // Domicilios únicos
  const uniqueDomicilios = new Set(events.map((e) => e.domicilioId)).size;

  return {
    id: `cluster-${index}`,
    centerLat,
    centerLng,
    radiusMeters: maxRadius,
    cases: events,
    totalCases: events.length,
    dateRange: {
      start: minDate,
      end: maxDate,
    },
    isActive,
    uniqueDomicilios,
  };
}

/**
 * Convierte domicilios con eventos a formato para clustering.
 * Usa fechas_eventos del backend (garantizado por OpenAPI).
 */
export function domiciliosToDengueEvents(
  domicilios: DomicilioMapaItem[],
  tipoGrupoMapping: Record<string, { grupoId: string; grupoNombre: string }>,
  dengueGrupoId?: string
): DengueClusterEvent[] {
  const events: DengueClusterEvent[] = [];

  for (const dom of domicilios) {
    // Verificar si tiene algún tipo de dengue
    const tipos = Object.entries(dom.tipos_eventos ?? {});
    const hasDengue = tipos.some(([tipoNombre]) =>
      DENGUE_CLUSTER_CONFIG.TIPOS_ENO_DENGUE.some((t) =>
        tipoNombre.toLowerCase().includes(t.toLowerCase())
      ) ||
      (dengueGrupoId &&
        tipoGrupoMapping[tipoNombre]?.grupoId === dengueGrupoId)
    );

    if (!hasDengue) continue;

    // Crear un evento por cada fecha (garantizado por backend)
    (dom.fechas_eventos ?? []).forEach((fechaStr, i) => {
      events.push({
        id: dom.id_domicilio * 1000 + i,
        domicilioId: dom.id_domicilio,
        lat: dom.latitud,
        lng: dom.longitud,
        fecha: new Date(fechaStr),
        tipoNombre: dom.tipo_evento_predominante ?? "Dengue",
      });
    });
  }

  return events;
}
