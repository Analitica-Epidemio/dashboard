"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface VariableConfig {
  variableId: string;
}

interface VariableConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInsert: (config: VariableConfig) => void;
}

export function VariableConfigDialog({ open, onOpenChange, onInsert }: VariableConfigDialogProps) {
  const [variableId, setVariableId] = useState("año");

  const handleInsert = () => {
    onInsert({ variableId });
    onOpenChange(false);
    setVariableId("año");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Insertar Variable</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="variable-id">Variable</Label>
            <Select value={variableId} onValueChange={setVariableId}>
              <SelectTrigger id="variable-id">
                <SelectValue placeholder="Selecciona una variable" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="año">Año</SelectItem>
                <SelectItem value="semana">Semana</SelectItem>
                <SelectItem value="semana_anterior">Semana Anterior</SelectItem>
                <SelectItem value="fecha_hasta">Fecha Hasta</SelectItem>
                <SelectItem value="fecha_completa">Fecha Completa</SelectItem>
                <SelectItem value="provincia">Provincia</SelectItem>
                <SelectItem value="departamento">Departamento</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              Las variables se reemplazarán automáticamente al generar el boletín
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleInsert}>Insertar Variable</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
