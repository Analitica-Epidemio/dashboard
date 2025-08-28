"use client"

import React, { useState } from 'react'
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Plus, Trash2, AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from "@/components/ui/alert"

import type { EventStrategy } from '@/lib/api/strategies'

type Strategy = EventStrategy

type FilterType = 
  | 'campo_igual'
  | 'campo_en_lista'
  | 'campo_contiene'
  | 'regex_extraccion'
  | 'campo_existe'
  | 'campo_no_nulo'
  | 'detector_tipo_sujeto'
  | 'extractor_metadata'

type ClassificationRule = {
  id?: number
  classification: string
  priority: number
  is_active: boolean
  auto_approve: boolean
  required_confidence?: number
  filters: FilterCondition[]
}

type FilterCondition = {
  id?: number
  filter_type: FilterType
  field_name: string
  value?: string
  values?: string[]
  logical_operator: 'AND' | 'OR'
  order: number
}

interface StrategyFormProps {
  strategy?: Strategy | null
  onClose: () => void
  onSuccess?: (message: string) => void
}

const FILTER_TYPES: Array<{value: FilterType, label: string, description: string}> = [
  { value: 'campo_igual', label: 'Campo Igual', description: 'El campo debe ser igual a un valor específico' },
  { value: 'campo_en_lista', label: 'Campo en Lista', description: 'El campo debe estar en una lista de valores' },
  { value: 'campo_contiene', label: 'Campo Contiene', description: 'El campo debe contener un texto específico' },
  { value: 'campo_existe', label: 'Campo Existe', description: 'El campo debe existir (no ser nulo)' },
  { value: 'campo_no_nulo', label: 'Campo No Nulo', description: 'El campo no debe estar vacío' },
  { value: 'detector_tipo_sujeto', label: 'Detector Tipo Sujeto', description: 'Detecta si es humano, animal o indeterminado' },
  { value: 'regex_extraccion', label: 'Extracción Regex', description: 'Extrae información usando expresión regular' },
  { value: 'extractor_metadata', label: 'Extractor Metadata', description: 'Extrae metadata adicional sin filtrar' },
]

const CLASSIFICATIONS = [
  'confirmados',
  'sospechosos', 
  'probables',
  'en_estudio',
  'negativos',
  'descartados',
  'notificados',
  'todos',
  'requiere_revision'
]

export function StrategyForm({ strategy, onClose }: StrategyFormProps) {
  const [formData, setFormData] = useState({
    name: strategy?.name || '',
    tipo_eno_id: strategy?.tipo_eno_id || '',
    active: strategy?.active || false,
    usa_provincia_carga: strategy?.usa_provincia_carga || false,
    provincia_field: strategy?.provincia_field || 'PROVINCIA_RESIDENCIA',
    confidence_threshold: strategy?.confidence_threshold || 0.5,
    description: strategy?.description || ''
  })

  const [rules, setRules] = useState<ClassificationRule[]>([
    {
      classification: 'confirmados',
      priority: 1,
      is_active: true,
      auto_approve: true,
      filters: []
    }
  ])

  const [errors, setErrors] = useState<string[]>([])

  const addRule = () => {
    const newRule: ClassificationRule = {
      classification: 'sospechosos',
      priority: rules.length + 1,
      is_active: true,
      auto_approve: true,
      filters: []
    }
    setRules([...rules, newRule])
  }

  const updateRule = (index: number, updates: Partial<ClassificationRule>) => {
    const newRules = [...rules]
    newRules[index] = { ...newRules[index], ...updates }
    setRules(newRules)
  }

  const removeRule = (index: number) => {
    setRules(rules.filter((_, i) => i !== index))
  }

  const addFilter = (ruleIndex: number) => {
    const newFilter: FilterCondition = {
      filter_type: 'campo_igual',
      field_name: '',
      value: '',
      logical_operator: 'AND',
      order: rules[ruleIndex].filters.length
    }
    
    const newRules = [...rules]
    newRules[ruleIndex].filters.push(newFilter)
    setRules(newRules)
  }

  const updateFilter = (ruleIndex: number, filterIndex: number, updates: Partial<FilterCondition>) => {
    const newRules = [...rules]
    newRules[ruleIndex].filters[filterIndex] = { 
      ...newRules[ruleIndex].filters[filterIndex], 
      ...updates 
    }
    setRules(newRules)
  }

  const removeFilter = (ruleIndex: number, filterIndex: number) => {
    const newRules = [...rules]
    newRules[ruleIndex].filters.splice(filterIndex, 1)
    setRules(newRules)
  }

  const validateForm = () => {
    const newErrors: string[] = []
    
    if (!formData.name.trim()) {
      newErrors.push('El nombre es requerido')
    }
    
    if (!formData.tipo_eno_id) {
      newErrors.push('El ID del tipo de evento es requerido')
    }

    if (rules.length === 0) {
      newErrors.push('Debe definir al menos una regla')
    }

    rules.forEach((rule, ruleIndex) => {
      if (!rule.classification) {
        newErrors.push(`Regla ${ruleIndex + 1}: Debe seleccionar una clasificación`)
      }
      
      rule.filters.forEach((filter, filterIndex) => {
        if (!filter.field_name.trim()) {
          newErrors.push(`Regla ${ruleIndex + 1}, Filtro ${filterIndex + 1}: El nombre del campo es requerido`)
        }
        
        if ((filter.filter_type === 'campo_igual' || filter.filter_type === 'campo_contiene') && !filter.value?.trim()) {
          newErrors.push(`Regla ${ruleIndex + 1}, Filtro ${filterIndex + 1}: El valor es requerido`)
        }
        
        if (filter.filter_type === 'campo_en_lista' && (!filter.values || filter.values.length === 0)) {
          newErrors.push(`Regla ${ruleIndex + 1}, Filtro ${filterIndex + 1}: Debe proporcionar al menos un valor`)
        }
      })
    })

    setErrors(newErrors)
    return newErrors.length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    const strategyData = {
      ...formData,
      classification_rules: rules
    }

    console.log('Guardando estrategia:', strategyData)
    // TODO: Implementar llamada a API
    onClose()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {errors.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <ul className="space-y-1">
              {errors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="name">Nombre de la Estrategia</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            placeholder="ej: Estrategia Dengue 2024"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tipo_eno_id">ID Tipo de Evento</Label>
          <Input
            id="tipo_eno_id"
            type="number"
            value={formData.tipo_eno_id}
            onChange={(e) => setFormData(prev => ({ ...prev, tipo_eno_id: Number(e.target.value) }))}
            placeholder="ej: 21010100"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descripción / Notas</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          placeholder="Describa el propósito y alcance de esta estrategia..."
          className="min-h-[80px]"
        />
        <p className="text-xs text-muted-foreground">
          Agregue cualquier información relevante que ayude a entender cómo funciona esta estrategia
        </p>
      </div>

      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <Switch
            id="active"
            checked={formData.active}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, active: checked }))}
          />
          <Label htmlFor="active">Estrategia Activa</Label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Switch
            id="usa_provincia"
            checked={formData.usa_provincia_carga}
            onCheckedChange={(checked) => setFormData(prev => ({ ...prev, usa_provincia_carga: checked }))}
          />
          <Label htmlFor="usa_provincia">Filtrar por Provincia</Label>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Reglas de Clasificación</h3>
          <Button type="button" onClick={addRule}>
            <Plus className="mr-2 h-4 w-4" />
            Agregar Regla
          </Button>
        </div>

        {rules.map((rule, ruleIndex) => (
          <Card key={ruleIndex}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Regla {ruleIndex + 1}
                  <Badge className="ml-2" variant="outline">
                    Prioridad: {rule.priority}
                  </Badge>
                </CardTitle>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRule(ruleIndex)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Clasificación</Label>
                  <Select
                    value={rule.classification}
                    onValueChange={(value) => updateRule(ruleIndex, { classification: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CLASSIFICATIONS.map(classification => (
                        <SelectItem key={classification} value={classification}>
                          {classification}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>Prioridad</Label>
                  <Input
                    type="number"
                    value={rule.priority}
                    onChange={(e) => updateRule(ruleIndex, { priority: Number(e.target.value) })}
                    min={1}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Confianza Mínima</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={rule.required_confidence || 0.5}
                    onChange={(e) => updateRule(ruleIndex, { required_confidence: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={rule.is_active}
                    onCheckedChange={(checked) => updateRule(ruleIndex, { is_active: checked })}
                  />
                  <Label>Activa</Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={rule.auto_approve}
                    onCheckedChange={(checked) => updateRule(ruleIndex, { auto_approve: checked })}
                  />
                  <Label>Auto-aprobar</Label>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Filtros</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => addFilter(ruleIndex)}
                  >
                    <Plus className="mr-2 h-3 w-3" />
                    Agregar Filtro
                  </Button>
                </div>

                {rule.filters.map((filter, filterIndex) => (
                  <div key={filterIndex} className="p-3 border rounded-lg bg-muted/50 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Filtro {filterIndex + 1}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFilter(ruleIndex, filterIndex)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Tipo de Filtro</Label>
                        <Select
                          value={filter.filter_type}
                          onValueChange={(value: FilterType) => 
                            updateFilter(ruleIndex, filterIndex, { filter_type: value })
                          }
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {FILTER_TYPES.map(type => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-1">
                        <Label className="text-xs">Campo</Label>
                        <Input
                          className="h-8"
                          value={filter.field_name}
                          onChange={(e) => updateFilter(ruleIndex, filterIndex, { field_name: e.target.value })}
                          placeholder="ej: CLASIFICACION_MANUAL"
                        />
                      </div>
                    </div>

                    {(filter.filter_type === 'campo_igual' || filter.filter_type === 'campo_contiene') && (
                      <div className="space-y-1">
                        <Label className="text-xs">Valor</Label>
                        <Input
                          className="h-8"
                          value={filter.value || ''}
                          onChange={(e) => updateFilter(ruleIndex, filterIndex, { value: e.target.value })}
                          placeholder="ej: Caso confirmado"
                        />
                      </div>
                    )}

                    {filter.filter_type === 'campo_en_lista' && (
                      <div className="space-y-1">
                        <Label className="text-xs">Valores (separados por coma)</Label>
                        <Textarea
                          className="h-16"
                          value={filter.values?.join(', ') || ''}
                          onChange={(e) => updateFilter(ruleIndex, filterIndex, { 
                            values: e.target.value.split(',').map(v => v.trim()).filter(v => v) 
                          })}
                          placeholder="ej: Caso confirmado, Caso probable"
                        />
                      </div>
                    )}

                    <div className="flex items-center gap-4">
                      <div className="space-y-1">
                        <Label className="text-xs">Operador Lógico</Label>
                        <Select
                          value={filter.logical_operator}
                          onValueChange={(value: 'AND' | 'OR') => 
                            updateFilter(ruleIndex, filterIndex, { logical_operator: value })
                          }
                        >
                          <SelectTrigger className="w-20 h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="AND">AND</SelectItem>
                            <SelectItem value="OR">OR</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      
                      <div className="space-y-1">
                        <Label className="text-xs">Orden</Label>
                        <Input
                          className="w-16 h-8"
                          type="number"
                          value={filter.order}
                          onChange={(e) => updateFilter(ruleIndex, filterIndex, { order: Number(e.target.value) })}
                          min={0}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onClose}>
          Cancelar
        </Button>
        <Button type="submit">
          {strategy ? 'Actualizar' : 'Crear'} Estrategia
        </Button>
      </div>
    </form>
  )
}