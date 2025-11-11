"use client"

import React, { useState } from 'react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Edit,
  Search,
  Calendar,
  User,
  Filter
} from 'lucide-react'

type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE' | 'ACTIVATE' | 'DEACTIVATE'

type AuditLogEntry = {
  id: number
  strategy_id: number
  strategy_name: string
  action: AuditAction
  field_changed: string
  old_value?: string
  new_value?: string
  changed_by: string
  changed_at: string
  ip_address?: string
  user_agent?: string
}

// Mock data for demonstration
const mockAuditData: AuditLogEntry[] = [
  {
    id: 1,
    strategy_id: 1,
    strategy_name: 'Estrategia Rabia Animal',
    action: 'UPDATE',
    field_changed: 'classification_rules',
    old_value: 'Regla confirmados: confianza >= 0.7',
    new_value: 'Regla confirmados: confianza >= 0.8',
    changed_by: 'Dr. García',
    changed_at: '2024-03-20T14:45:00Z',
    ip_address: '192.168.1.100'
  },
  {
    id: 2,
    strategy_id: 2,
    strategy_name: 'Estrategia Dengue',
    action: 'CREATE',
    field_changed: 'strategy',
    old_value: undefined,
    new_value: 'Estrategia creada con 5 reglas',
    changed_by: 'Dra. Martínez',
    changed_at: '2024-02-01T09:15:00Z',
    ip_address: '192.168.1.105'
  },
  {
    id: 3,
    strategy_id: 1,
    strategy_name: 'Estrategia Rabia Animal',
    action: 'UPDATE',
    field_changed: 'usa_provincia_carga',
    old_value: 'true',
    new_value: 'false',
    changed_by: 'Dr. García',
    changed_at: '2024-03-15T11:30:00Z',
    ip_address: '192.168.1.100'
  },
  {
    id: 4,
    strategy_id: 3,
    strategy_name: 'Estrategia Hepatitis C',
    action: 'DEACTIVATE',
    field_changed: 'active',
    old_value: 'true',
    new_value: 'false',
    changed_by: 'Dr. Rodriguez',
    changed_at: '2024-03-10T16:20:00Z',
    ip_address: '192.168.1.120'
  },
  {
    id: 5,
    strategy_id: 2,
    strategy_name: 'Estrategia Dengue',
    action: 'UPDATE',
    field_changed: 'confidence_threshold',
    old_value: '0.5',
    new_value: '0.6',
    changed_by: 'Dra. Martínez',
    changed_at: '2024-03-05T08:45:00Z',
    ip_address: '192.168.1.105'
  }
]

export function AuditLog() {
  const [entries] = useState(mockAuditData)
  const [filters, setFilters] = useState({
    action: '',
    strategy: '',
    user: '',
    dateFrom: '',
    dateTo: '',
    search: ''
  })

  const getActionIcon = (action: AuditAction) => {
    switch (action) {
      case 'CREATE':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'UPDATE':
        return <Edit className="h-4 w-4 text-blue-500" />
      case 'DELETE':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'ACTIVATE':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'DEACTIVATE':
        return <AlertCircle className="h-4 w-4 text-orange-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getActionBadge = (action: AuditAction) => {
    const variants: Record<AuditAction, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
      CREATE: { label: 'Creado', variant: 'default' },
      UPDATE: { label: 'Actualizado', variant: 'secondary' },
      DELETE: { label: 'Eliminado', variant: 'destructive' },
      ACTIVATE: { label: 'Activado', variant: 'default' },
      DEACTIVATE: { label: 'Desactivado', variant: 'outline' }
    }
    const config = variants[action]
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const uniqueStrategies = Array.from(new Set(entries.map(e => e.strategy_name)))
  const uniqueUsers = Array.from(new Set(entries.map(e => e.changed_by)))

  const filteredEntries = entries.filter(entry => {
    if (filters.action && entry.action !== filters.action) return false
    if (filters.strategy && entry.strategy_name !== filters.strategy) return false
    if (filters.user && entry.changed_by !== filters.user) return false
    if (filters.search && !entry.field_changed.toLowerCase().includes(filters.search.toLowerCase()) && 
        !entry.strategy_name.toLowerCase().includes(filters.search.toLowerCase())) return false
    // TODO: Add date filtering
    return true
  })

  const clearFilters = () => {
    setFilters({
      action: '',
      strategy: '',
      user: '',
      dateFrom: '',
      dateTo: '',
      search: ''
    })
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span className="text-sm font-medium">Filtros:</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          <Input
            placeholder="Buscar..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="w-48"
          />
        </div>

        <Select
          value={filters.action}
          onValueChange={(value) => setFilters(prev => ({ ...prev, action: value }))}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Acción" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todas las acciones</SelectItem>
            <SelectItem value="CREATE">Creado</SelectItem>
            <SelectItem value="UPDATE">Actualizado</SelectItem>
            <SelectItem value="DELETE">Eliminado</SelectItem>
            <SelectItem value="ACTIVATE">Activado</SelectItem>
            <SelectItem value="DEACTIVATE">Desactivado</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={filters.strategy}
          onValueChange={(value) => setFilters(prev => ({ ...prev, strategy: value }))}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Estrategia" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todas las estrategias</SelectItem>
            {uniqueStrategies.map(strategy => (
              <SelectItem key={strategy} value={strategy}>{strategy}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filters.user}
          onValueChange={(value) => setFilters(prev => ({ ...prev, user: value }))}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Usuario" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos los usuarios</SelectItem>
            {uniqueUsers.map(user => (
              <SelectItem key={user} value={user}>{user}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={clearFilters}>
          Limpiar
        </Button>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Mostrando {filteredEntries.length} de {entries.length} entradas
        </p>
      </div>

      {/* Audit Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Acción</TableHead>
              <TableHead>Estrategia</TableHead>
              <TableHead>Campo Modificado</TableHead>
              <TableHead>Cambio</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredEntries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getActionIcon(entry.action)}
                    {getActionBadge(entry.action)}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="font-medium text-sm">{entry.strategy_name}</span>
                    <span className="text-xs text-muted-foreground">ID: {entry.strategy_id}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <code className="bg-muted px-2 py-1 rounded text-xs">
                    {entry.field_changed}
                  </code>
                </TableCell>
                <TableCell className="max-w-xs">
                  <div className="space-y-1">
                    {entry.old_value && (
                      <div className="text-xs">
                        <span className="text-red-600">- </span>
                        <span className="text-muted-foreground">{entry.old_value}</span>
                      </div>
                    )}
                    {entry.new_value && (
                      <div className="text-xs">
                        <span className="text-green-600">+ </span>
                        <span>{entry.new_value}</span>
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    <span className="text-sm">{entry.changed_by}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <div className="text-sm">
                      <div>{new Date(entry.changed_at).toLocaleDateString()}</div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(entry.changed_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground font-mono">
                  {entry.ip_address}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {filteredEntries.length === 0 && (
        <div className="text-center py-8">
          <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No se encontraron registros</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Intenta ajustar los filtros para ver más resultados
          </p>
        </div>
      )}
    </div>
  )
}