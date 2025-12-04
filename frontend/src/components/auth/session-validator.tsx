"use client";

/**
 * SessionValidator Component
 *
 * Valida la sesión periódicamente en el cliente.
 * Si la sesión es inválida (usuario eliminado, token revocado, etc.),
 * fuerza un logout y redirige a login.
 */

import { useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";

export function SessionValidator() {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    // Solo validar si hay una sesión activa
    if (status !== "authenticated" || !session) {
      return;
    }

    // Si la sesión tiene error, hacer logout inmediatamente
    if (session.error) {
      console.log("Session error detected, logging out:", session.error);
      signOut({ callbackUrl: "/login" });
      return;
    }

    // SEGURIDAD: Validar sesión cada 2 minutos para datos médicos sensibles
    const VALIDATION_INTERVAL_MS = 2 * 60 * 1000; // 2 minutos

    const interval = setInterval(async () => {
      try {
        // Forzar revalidación de la sesión
        // Esto trigger el callback jwt() que valida contra el backend
        const response = await fetch("/api/auth/session", {
          method: "GET",
          cache: "no-store",
        });

        if (!response.ok) {
          console.log("Session validation failed, logging out");
          signOut({ callbackUrl: "/login" });
        }

        const updatedSession = await response.json();

        // Si la sesión tiene error, hacer logout
        if (updatedSession?.error) {
          console.log("Session error after validation, logging out");
          signOut({ callbackUrl: "/login" });
        }
      } catch (error) {
        console.error("Error validating session:", error);
      }
    }, VALIDATION_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [session, status, router]);

  // Este componente no renderiza nada
  return null;
}
