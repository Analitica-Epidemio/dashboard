"use client";

import React, { useState, useMemo, useEffect } from "react";
import { CheckSquare, Square, Activity, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useGrupoDetalle } from "@/lib/api/analytics";

interface EventoSelectorProps {
  grupoId: number | null;
  eventosSeleccionados: number[];
  onSeleccionar: (eventos: number[]) => void;
}

export function EventoSelector({
  grupoId,
  eventosSeleccionados,
  onSeleccionar
}: EventoSelectorProps) {
  const [mostrarTodos, setMostrarTodos] = useState(false);
  
  const { data: grupoDetalle, isLoading, error } = useGrupoDetalle(grupoId);
  
  const eventos = useMemo(() => {
    return grupoDetalle?.data?.eventos || [];
  }, [grupoDetalle?.data?.eventos]);

  // Si no hay eventos seleccionados, seleccionar todos por defecto
  useEffect(() => {
    if (eventos.length > 0 && eventosSeleccionados.length === 0) {
      onSeleccionar(eventos.map(e => e.tipo_eno_id));
    }
  }, [eventos, eventosSeleccionados.length, onSeleccionar]);

  const handleToggleEvento = (eventoId: number) => {
    if (eventosSeleccionados.includes(eventoId)) {
      onSeleccionar(eventosSeleccionados.filter(id => id !== eventoId));
    } else {
      onSeleccionar([...eventosSeleccionados, eventoId]);
    }
  };

  const handleSeleccionarTodos = () => {
    if (eventosSeleccionados.length === eventos.length) {
      onSeleccionar([]);
    } else {
      onSeleccionar(eventos.map(e => e.tipo_eno_id));
    }
  };

  const eventosVisibles = mostrarTodos ? eventos : eventos.slice(0, 3);
  const hayMasEventos = eventos.length > 3;

  if (!grupoId) {
    return (
      <div className="text-center p-4">
        <Activity className="h-8 w-8 mx-auto text-muted-foreground opacity-50 mb-2" />
        <p className="text-sm text-muted-foreground">
          Primero selecciona un grupo
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        <span className="text-sm text-muted-foreground">Cargando eventos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-4">
        <AlertCircle className="h-8 w-8 mx-auto text-destructive mb-2" />
        <p className="text-sm text-muted-foreground">
          Error cargando eventos
        </p>
      </div>
    );
  }

  if (eventos.length === 0) {
    return (
      <div className="text-center p-4">
        <Activity className="h-8 w-8 mx-auto text-muted-foreground opacity-50 mb-2" />
        <p className="text-sm text-muted-foreground">
          No hay eventos en este grupo
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header con botón seleccionar todos */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          {eventosSeleccionados.length} de {eventos.length} seleccionados
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSeleccionarTodos}
          className="h-6 text-xs"
        >
          {eventosSeleccionados.length === eventos.length ? (
            <>
              <CheckSquare className="h-3 w-3 mr-1" />
              Deseleccionar
            </>
          ) : (
            <>
              <Square className="h-3 w-3 mr-1" />
              Todos
            </>
          )}
        </Button>
      </div>

      {/* Lista de eventos */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {eventosVisibles.map((evento) => {
          const isSelected = eventosSeleccionados.includes(evento.tipo_eno_id);
          
          return (
            <div
              key={evento.tipo_eno_id}
              className={`
                flex items-start gap-3 p-2 rounded-md border cursor-pointer transition-colors
                ${isSelected 
                  ? "bg-primary/5 border-primary/20" 
                  : "bg-muted/20 border-muted hover:bg-muted/40"
                }
              `}
              onClick={() => handleToggleEvento(evento.tipo_eno_id)}
            >
              <div className="mt-0.5">
                {isSelected ? (
                  <CheckSquare className="h-4 w-4 text-primary" />
                ) : (
                  <Square className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium leading-tight">
                    {evento.nombre}
                  </h4>
                  <Badge variant="outline" className="text-xs shrink-0">
                    {evento.total_casos}
                  </Badge>
                </div>
                
                <div className="mt-1 flex gap-2 text-xs text-muted-foreground">
                  {evento.casos_confirmados > 0 && (
                    <span className="text-green-600">
                      ✓ {evento.casos_confirmados}
                    </span>
                  )}
                  {evento.casos_sospechosos > 0 && (
                    <span className="text-yellow-600">
                      ⚠ {evento.casos_sospechosos}
                    </span>
                  )}
                  {evento.ultimo_caso && (
                    <span>
                      📅 {new Date(evento.ultimo_caso).toLocaleDateString('es-ES', {
                        month: 'short',
                        day: 'numeric'
                      })}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Mostrar más eventos si hay */}
      {hayMasEventos && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setMostrarTodos(!mostrarTodos)}
          className="w-full h-8 text-xs"
        >
          {mostrarTodos ? (
            <>Mostrar menos ({eventos.length - 3} ocultos)</>
          ) : (
            <>Mostrar todos (+{eventos.length - 3} más)</>
          )}
        </Button>
      )}

      {/* Resumen */}
      {eventosSeleccionados.length > 0 && (
        <div className="p-2 bg-primary/5 rounded-md text-xs">
          <span className="font-medium">Incluirá datos de:</span>
          <div className="mt-1 flex flex-wrap gap-1">
            {eventosSeleccionados.slice(0, 2).map((id: number) => {
              const evento = eventos.find(e => e.tipo_eno_id === id);
              return evento ? (
                <Badge key={id} variant="secondary" className="text-xs">
                  {evento.nombre.length > 20 ? evento.nombre.substring(0, 20) + "..." : evento.nombre}
                </Badge>
              ) : null;
            })}
            {eventosSeleccionados.length > 2 && (
              <Badge variant="secondary" className="text-xs">
                +{eventosSeleccionados.length - 2} más
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
}