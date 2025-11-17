"use client";

/**
 * Sección de información de perfil
 * Permite actualizar nombre y apellido
 */

import { useState } from "react";
import { User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useUpdateProfile } from "@/features/auth/api";

interface ProfileInfoSectionProps {
  profile: {
    nombre: string;
    apellido: string;
  };
}

export function ProfileInfoSection({ profile }: ProfileInfoSectionProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [nombre, setNombre] = useState(profile.nombre);
  const [apellido, setApellido] = useState(profile.apellido);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const updateProfileMutation = useUpdateProfile();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const data: { nombre?: string; apellido?: string } = {};
    if (nombre !== profile.nombre) data.nombre = nombre;
    if (apellido !== profile.apellido) data.apellido = apellido;

    if (Object.keys(data).length === 0) {
      setError("No hay cambios para guardar");
      return;
    }

    try {
      await updateProfileMutation.mutateAsync({ body: data });
      setSuccess("Perfil actualizado correctamente");
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al actualizar perfil");
    }
  };

  const handleCancel = () => {
    setNombre(profile.nombre);
    setApellido(profile.apellido);
    setIsEditing(false);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="flex flex-row-reverse items-start border-t pt-4 pb-4 gap-6">
      <div className="flex-shrink-0">
        {!isEditing ? (
          <Button
            variant="ghost"
            size="sm"
            className="text-primary hover:text-primary"
            onClick={() => setIsEditing(true)}
          >
            Editar perfil
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancel}
              disabled={updateProfileMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={updateProfileMutation.isPending}
            >
              {updateProfileMutation.isPending ? "Guardando..." : "Guardar"}
            </Button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3 min-w-0 w-full">
        <h3 className="text-sm font-medium">Perfil</h3>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {success && (
          <Alert>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {!isEditing ? (
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div className="min-w-0">
              <p className="font-medium truncate">
                {profile.nombre} {profile.apellido}
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre</Label>
                <Input
                  id="nombre"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Tu nombre"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apellido">Apellido</Label>
                <Input
                  id="apellido"
                  value={apellido}
                  onChange={(e) => setApellido(e.target.value)}
                  placeholder="Tu apellido"
                />
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
