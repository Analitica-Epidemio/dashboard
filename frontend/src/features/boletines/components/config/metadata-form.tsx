"use client";

import { useEffect } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useUpdateBoletinMetadata } from "@/features/boletines/api";
import type { BoletinTemplateConfigResponse } from "@/features/boletines/api";

const autoridadSchema = z.object({
  nombre: z.string().min(1, "Requerido"),
  cargo: z.string().min(1, "Requerido"),
});

const metadataSchema = z.object({
  institucion: z.string().min(1, "Requerido"),
  autoridades: z.array(autoridadSchema),
  periodo_default: z.enum([
    "ultima_semana",
    "ultimas_4_semanas",
    "personalizado",
  ]),
});

type MetadataFormData = z.infer<typeof metadataSchema>;

function parseMetadata(meta: Record<string, unknown>): MetadataFormData {
  return {
    institucion: (meta.institucion as string) || "",
    autoridades: Array.isArray(meta.autoridades)
      ? (meta.autoridades as { nombre: string; cargo: string }[])
      : [],
    periodo_default:
      (meta.periodo_default as MetadataFormData["periodo_default"]) ||
      "ultima_semana",
  };
}

interface MetadataFormProps {
  config: BoletinTemplateConfigResponse;
}

export function MetadataForm({ config }: MetadataFormProps) {
  const queryClient = useQueryClient();
  const updateMetadata = useUpdateBoletinMetadata();

  const meta = config.boletin_metadata ?? {};

  const form = useForm<MetadataFormData>({
    resolver: zodResolver(metadataSchema),
    defaultValues: parseMetadata(meta),
  });

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors, isDirty },
  } = form;

  const { fields, append, remove } = useFieldArray({
    control,
    name: "autoridades",
  });

  const periodoValue = watch("periodo_default");

  // Reset form when config changes externally
  useEffect(() => {
    if (config.boletin_metadata) {
      form.reset(parseMetadata(config.boletin_metadata));
    }
  }, [config.boletin_metadata, form]);

  const onSubmit = handleSubmit(async (data) => {
    try {
      await updateMetadata.mutateAsync({
        body: {
          boletin_metadata: {
            ...meta,
            institucion: data.institucion,
            autoridades: data.autoridades,
            periodo_default: data.periodo_default,
          },
        },
      });
      queryClient.invalidateQueries({
        queryKey: ["get", "/api/v1/boletines/config"],
      });
      form.reset(data);
      toast.success("Datos guardados");
    } catch {
      toast.error("Error al guardar");
    }
  });

  return (
    <form onSubmit={onSubmit} className="max-w-2xl space-y-6 py-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Institución</CardTitle>
          <CardDescription>
            Datos de la institución que aparecen en la portada del boletín
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="institucion">Nombre de la institución</Label>
            <Input
              id="institucion"
              placeholder="Ministerio de Salud del Chubut"
              {...register("institucion")}
            />
            {errors.institucion && (
              <p className="text-sm text-destructive">
                {errors.institucion.message}
              </p>
            )}
          </div>

          <Separator />

          <div className="space-y-2">
            <Label htmlFor="periodo_default">Período por defecto</Label>
            <p className="text-sm text-muted-foreground">
              Rango temporal que se usa al generar un nuevo boletín
            </p>
            <Select
              value={periodoValue}
              onValueChange={(v) =>
                setValue(
                  "periodo_default",
                  v as MetadataFormData["periodo_default"],
                  { shouldDirty: true }
                )
              }
            >
              <SelectTrigger className="w-64">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ultima_semana">Última semana</SelectItem>
                <SelectItem value="ultimas_4_semanas">
                  Últimas 4 semanas
                </SelectItem>
                <SelectItem value="personalizado">Personalizado</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Autoridades</CardTitle>
          <CardDescription>
            Personas que firman o figuran en la portada del boletín
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {fields.length === 0 && (
            <p className="text-sm text-muted-foreground py-2">
              No hay autoridades cargadas. Agregá al menos una.
            </p>
          )}

          {fields.map((field, index) => (
            <div key={field.id} className="flex gap-2 items-start">
              <div className="flex-1 space-y-1">
                <Input
                  placeholder="Nombre completo"
                  {...register(`autoridades.${index}.nombre`)}
                />
                {errors.autoridades?.[index]?.nombre && (
                  <p className="text-sm text-destructive">
                    {errors.autoridades[index].nombre?.message}
                  </p>
                )}
              </div>
              <div className="flex-1 space-y-1">
                <Input
                  placeholder="Cargo (ej: Director de Epidemiología)"
                  {...register(`autoridades.${index}.cargo`)}
                />
                {errors.autoridades?.[index]?.cargo && (
                  <p className="text-sm text-destructive">
                    {errors.autoridades[index].cargo?.message}
                  </p>
                )}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="shrink-0 text-muted-foreground hover:text-destructive"
                onClick={() => remove(index)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => append({ nombre: "", cargo: "" })}
          >
            <Plus className="h-4 w-4 mr-1" />
            Agregar autoridad
          </Button>
        </CardContent>
      </Card>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!isDirty || updateMetadata.isPending}>
          {updateMetadata.isPending ? "Guardando..." : "Guardar cambios"}
        </Button>
        {isDirty && (
          <span className="text-sm text-amber-600">
            Cambios sin guardar
          </span>
        )}
      </div>
    </form>
  );
}
