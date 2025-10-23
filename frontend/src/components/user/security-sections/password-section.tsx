"use client";

/**
 * Sección de cambio de contraseña
 */

import { useState } from "react";
import { signOut } from "next-auth/react";
import { Lock, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useChangePassword } from "@/lib/api/hooks/use-user";

export function PasswordSection() {
  const [isChanging, setIsChanging] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const changePasswordMutation = useChangePassword();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Validaciones
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("Todos los campos son obligatorios");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    if (newPassword.length < 8) {
      setError("La nueva contraseña debe tener al menos 8 caracteres");
      return;
    }

    try {
      await changePasswordMutation.mutateAsync({
        body: {
          current_password: currentPassword,
          new_password: newPassword,
        },
      });

      setSuccess("Contraseña cambiada correctamente. Cerrando sesión...");

      // Cerrar sesión después de 2 segundos
      setTimeout(() => {
        signOut({ callbackUrl: "/login" });
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar contraseña");
    }
  };

  const handleCancel = () => {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setIsChanging(false);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="flex flex-row-reverse items-start border-t pt-4 pb-4 gap-6">
      <div className="flex-shrink-0">
        {!isChanging ? (
          <Button
            variant="ghost"
            size="sm"
            className="text-primary hover:text-primary"
            onClick={() => setIsChanging(true)}
          >
            Cambiar contraseña
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancel}
              disabled={changePasswordMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={changePasswordMutation.isPending}
            >
              {changePasswordMutation.isPending ? "Cambiando..." : "Guardar"}
            </Button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3 min-w-0 w-full">
        <h3 className="text-sm font-medium">Contraseña</h3>

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

        {!isChanging ? (
          <p className="text-sm text-muted-foreground">
            Establece una contraseña para proteger tu cuenta
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
            <Alert>
              <Lock className="h-4 w-4" />
              <AlertDescription className="text-xs">
                <strong>Requisitos:</strong> Mínimo 8 caracteres con mayúsculas,
                minúsculas, números y caracteres especiales.
              </AlertDescription>
            </Alert>

            <div className="space-y-2">
              <Label htmlFor="current-password">Contraseña actual</Label>
              <div className="relative">
                <Input
                  id="current-password"
                  type={showCurrentPassword ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password">Nueva contraseña</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirmar nueva contraseña</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            <Alert>
              <AlertDescription className="text-xs">
                ⚠️ Al cambiar tu contraseña, se cerrarán todas tus sesiones activas
                y tendrás que volver a iniciar sesión.
              </AlertDescription>
            </Alert>
          </form>
        )}
      </div>
    </div>
  );
}
