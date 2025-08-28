"use client"

import React from 'react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Eye, Edit, Trash2 } from 'lucide-react'

import type { EventStrategy } from '@/lib/api/strategies'

type Strategy = EventStrategy

interface StrategyListProps {
  strategies: Strategy[]
  onView: (strategy: Strategy) => void
  onEdit: (strategy: Strategy) => void
  onDelete: (strategy: Strategy) => void
}

export function StrategyList({ strategies, onView, onEdit, onDelete }: StrategyListProps) {
  const getStatusBadge = (status: string) => {
    const variants = {
      active: { label: 'Activa', variant: 'default' as const },
      draft: { label: 'Borrador', variant: 'secondary' as const },
      pending_review: { label: 'Pendiente', variant: 'outline' as const }
    }
    const config = variants[status as keyof typeof variants] || { label: status, variant: 'outline' as const }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Nombre</TableHead>
          <TableHead>Evento</TableHead>
          <TableHead>Estado</TableHead>
          <TableHead>Reglas</TableHead>
          <TableHead>Provincia</TableHead>
          <TableHead>Creado por</TableHead>
          <TableHead>Actualizada</TableHead>
          <TableHead>Acciones</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {strategies.map((strategy) => (
          <TableRow key={strategy.id}>
            <TableCell className="font-medium">{strategy.name}</TableCell>
            <TableCell>
              <div className="flex flex-col">
                <span className="text-sm font-medium">{strategy.tipo_eno_name || `Evento ${strategy.tipo_eno_id}`}</span>
                <span className="text-xs text-muted-foreground">ID: {strategy.tipo_eno_id}</span>
              </div>
            </TableCell>
            <TableCell>{getStatusBadge(strategy.status)}</TableCell>
            <TableCell>
              <Badge variant="outline">{(strategy.classification_rules_count || 0)} reglas</Badge>
            </TableCell>
            <TableCell>
              {strategy.usa_provincia_carga ? (
                <Badge variant="secondary">Sí</Badge>
              ) : (
                <Badge variant="outline">No</Badge>
              )}
            </TableCell>
            <TableCell className="text-sm">{strategy.created_by || 'Sistema'}</TableCell>
            <TableCell className="text-sm text-muted-foreground">
              {strategy.updated_at ? new Date(strategy.updated_at).toLocaleDateString() : 'N/A'}
            </TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onView(strategy)}
                  title="Ver detalles"
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(strategy)}
                  title="Editar estrategia"
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => onDelete(strategy)}
                  title="Eliminar estrategia"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}