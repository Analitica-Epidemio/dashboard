import type { Page } from "playwright";

/**
 * Resalta un elemento con un borde rojo pulsante.
 *
 * El highlight dura 2 segundos y luego se remueve automáticamente.
 * Útil para los videos tutoriales — muestra al viewer dónde mirar.
 */
export async function highlightElement(
  page: Page,
  selector: string,
  options: { duration?: number; color?: string } = {}
): Promise<void> {
  const duration = options.duration ?? 2000;
  const color = options.color ?? "#ef4444"; // rojo tailwind red-500

  await page.evaluate(
    ({ selector, duration, color }) => {
      const el = document.querySelector(selector);
      if (!el) return;

      // Crear overlay
      const overlay = document.createElement("div");
      overlay.className = "__playwright-highlight";
      const rect = el.getBoundingClientRect();

      Object.assign(overlay.style, {
        position: "fixed",
        top: `${rect.top - 4}px`,
        left: `${rect.left - 4}px`,
        width: `${rect.width + 8}px`,
        height: `${rect.height + 8}px`,
        border: `3px solid ${color}`,
        borderRadius: "6px",
        zIndex: "999998",
        pointerEvents: "none",
        animation: "__pw-pulse 0.6s ease-in-out infinite alternate",
        boxShadow: `0 0 12px ${color}40`,
      });

      // Inyectar keyframes si no existen
      if (!document.getElementById("__pw-highlight-styles")) {
        const style = document.createElement("style");
        style.id = "__pw-highlight-styles";
        style.textContent = `
          @keyframes __pw-pulse {
            from { opacity: 1; }
            to { opacity: 0.4; }
          }
        `;
        document.head.appendChild(style);
      }

      document.body.appendChild(overlay);

      // Auto-remover después de la duración
      setTimeout(() => overlay.remove(), duration);
    },
    { selector, duration, color }
  );
}

/**
 * Remueve todos los highlights activos de la página.
 */
export async function clearHighlights(page: Page): Promise<void> {
  await page.evaluate(() => {
    document
      .querySelectorAll(".__playwright-highlight")
      .forEach((el) => el.remove());
  });
}
