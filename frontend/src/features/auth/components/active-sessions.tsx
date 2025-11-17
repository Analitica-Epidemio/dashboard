"use client";

/**
 * Componente para ver y gestionar sesiones activas
 * Muestra dispositivos, IPs y permite cerrar sesiones
 */

import { useState } from "react";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import {
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  X,
  AlertTriangle,
  RefreshCw,
  MapPin,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  useUserSessions,
  useLogoutSession,
  useLogoutAllSessions,
} from "@/features/auth/api";

/**
 * Detecta el tipo de dispositivo desde el user agent
 */
function getDeviceType(userAgent: string | null): {
  type: "desktop" | "mobile" | "tablet" | "unknown";
  icon: React.ReactNode;
  label: string;
} {
  if (!userAgent) {
    return {
      type: "unknown",
      icon: <Globe className="h-4 w-4" />,
      label: "Desconocido",
    };
  }

  const ua = userAgent.toLowerCase();

  if (ua.includes("mobile") || ua.includes("android")) {
    return {
      type: "mobile",
      icon: <Smartphone className="h-4 w-4" />,
      label: "Móvil",
    };
  }

  if (ua.includes("tablet") || ua.includes("ipad")) {
    return {
      type: "tablet",
      icon: <Tablet className="h-4 w-4" />,
      label: "Tablet",
    };
  }

  return {
    type: "desktop",
    icon: <Monitor className="h-4 w-4" />,
    label: "Escritorio",
  };
}

/**
 * Extrae información del navegador y OS del user agent
 */
function parseUserAgent(userAgent: string | null): {
  browser: string;
  os: string;
} {
  if (!userAgent) {
    return { browser: "Desconocido", os: "Desconocido" };
  }

  const ua = userAgent;

  // Detectar navegador
  let browser = "Desconocido";
  if (ua.includes("Chrome/")) browser = "Chrome";
  else if (ua.includes("Firefox/")) browser = "Firefox";
  else if (ua.includes("Safari/") && !ua.includes("Chrome/")) browser = "Safari";
  else if (ua.includes("Edge/")) browser = "Edge";

  // Detectar OS
  let os = "Desconocido";
  if (ua.includes("Windows")) os = "Windows";
  else if (ua.includes("Mac OS X")) os = "macOS";
  else if (ua.includes("Linux")) os = "Linux";
  else if (ua.includes("Android")) os = "Android";
  else if (ua.includes("iOS")) os = "iOS";

  return { browser, os };
}

export function ActiveSessions() {
  // Hooks de OpenAPI
  const { data: sessions, isLoading: loading, refetch } = useUserSessions();
  const logoutSessionMutation = useLogoutSession();
  const logoutAllSessionsMutation = useLogoutAllSessions();

  // Estados locales
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);
  const [showLogoutAllDialog, setShowLogoutAllDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogoutSession = async (sessionId: number) => {
    try {
      setError(null);
      await logoutSessionMutation.mutateAsync({
        params: {
          path: { session_id: sessionId },
        },
      });
      setSessionToDelete(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al cerrar sesión";
      setError(errorMessage);
    }
  };

  const handleLogoutAll = async () => {
    try {
      setError(null);
      await logoutAllSessionsMutation.mutateAsync({});
      // Recargar la página para que el usuario tenga que volver a iniciar sesión nuevamente
      window.location.href = '/login';
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Error al cerrar todas las sesiones";
      setError(errorMessage);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sesiones Activas</CardTitle>
          <CardDescription>Cargando sesiones...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                Sesiones Activas
              </CardTitle>
              <CardDescription>
                Dispositivos desde donde has iniciado sesión
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Actualizar
              </Button>
              {sessions && sessions.length > 1 && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowLogoutAllDialog(true)}
                >
                  Cerrar todas
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!loading && sessions?.length === 0 && (
            <Alert>
              <AlertDescription>No hay sesiones activas</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            {sessions?.map((sessionInfo) => {
              const device = getDeviceType(sessionInfo.user_agent);
              const { browser, os } = parseUserAgent(sessionInfo.user_agent);

              return (
                <div
                  key={sessionInfo.id}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex gap-4 flex-1">
                      {/* Icono del dispositivo */}
                      <div className="flex-shrink-0 mt-1">{device.icon}</div>

                      {/* Información del dispositivo */}
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold">
                            {browser} en {os}
                          </h4>
                          {sessionInfo.is_current && (
                            <Badge variant="default" className="text-xs">
                              Esta sesión
                            </Badge>
                          )}
                        </div>

                        <div className="text-sm text-muted-foreground space-y-1">
                          <div className="flex items-center gap-2">
                            <MapPin className="h-3 w-3" />
                            <span>
                              IP: {sessionInfo.ip_address || "Desconocida"}
                            </span>
                          </div>

                          <div>
                            Última actividad:{" "}
                            {format(
                              new Date(sessionInfo.last_activity),
                              "dd MMM yyyy, HH:mm",
                              { locale: es }
                            )}
                          </div>

                          <div className="text-xs">
                            Creada:{" "}
                            {format(
                              new Date(sessionInfo.created_at),
                              "dd MMM yyyy, HH:mm",
                              { locale: es }
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Botón para cerrar sesión */}
                    {!sessionInfo.is_current && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSessionToDelete(sessionInfo.id)}
                        disabled={logoutSessionMutation.isPending}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {sessions && sessions.length > 0 && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Seguridad:</strong> Si ves sesiones que no reconoces,
                ciérralas inmediatamente y cambia tu contraseña.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Dialog para confirmar cierre de sesión */}
      <AlertDialog
        open={sessionToDelete !== null}
        onOpenChange={(open) => !open && setSessionToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Cerrar esta sesión?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción cerrará la sesión en ese dispositivo. El usuario
              tendrá que volver a iniciar sesión.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() =>
                sessionToDelete && handleLogoutSession(sessionToDelete)
              }
            >
              Cerrar sesión
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Dialog para confirmar cierre de todas las sesiones */}
      <AlertDialog
        open={showLogoutAllDialog}
        onOpenChange={setShowLogoutAllDialog}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Cerrar todas las sesiones?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta acción cerrará TODAS las sesiones activas, incluida la
              actual. Tendrás que volver a iniciar sesión nuevamente.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleLogoutAll} className="bg-destructive">
              Cerrar todas
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
