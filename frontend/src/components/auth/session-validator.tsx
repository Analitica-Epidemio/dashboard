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

    // Validar sesión cada 5 minutos
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
    }, 5 * 60 * 1000); // 5 minutos

    return () => clearInterval(interval);
  }, [session, status, router]);

  // Este componente no renderiza nada
  return null;
}
