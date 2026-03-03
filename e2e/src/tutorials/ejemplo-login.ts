import type { TutorialDefinition } from "../types.js";

/**
 * Tutorial ejemplo: flujo de login al dashboard.
 *
 * Para crear un tutorial nuevo, copiá este archivo y modificá los steps.
 * Cada step tiene:
 *   - id:             identificador único
 *   - narration:      texto para el TTS (cuando lo implementen)
 *   - action:         función async que recibe `page` de Playwright
 *   - waitAfterAction: ms a esperar después (default 1000)
 *   - highlight:      selector CSS a resaltar (opcional)
 */
const tutorial: TutorialDefinition = {
  id: "ejemplo-login",
  title: "Login al Dashboard de Epidemiología",
  description: "Muestra cómo ingresar al sistema con email y contraseña",
  setupPath: "/login",
  steps: [
    {
      id: "ver-formulario",
      narration:
        "Esta es la pantalla de login del sistema de epidemiología. Vamos a ingresar con nuestras credenciales.",
      action: async (page) => {
        // Solo esperar a que cargue el form
        await page.waitForSelector("#email", { state: "visible" });
      },
      waitAfterAction: 2000,
    },
    {
      id: "ingresar-email",
      narration: "Primero ingresamos nuestro email.",
      action: async (page) => {
        await page.locator("#email").fill(process.env.LOGIN_EMAIL ?? "");
      },
      waitAfterAction: 1500,
      highlight: "#email",
    },
    {
      id: "ingresar-password",
      narration: "Luego ingresamos la contraseña.",
      action: async (page) => {
        await page.locator("#password").fill(process.env.LOGIN_PASSWORD ?? "");
      },
      waitAfterAction: 1500,
      highlight: "#password",
    },
    {
      id: "click-login",
      narration:
        "Hacemos click en Iniciar Sesión y el sistema nos redirige al dashboard.",
      action: async (page) => {
        await page.locator('button[type="submit"]').click();
        // Esperar a que salga de /login
        await page.waitForURL((url) => !url.pathname.includes("/login"), {
          timeout: 15_000,
        });
      },
      waitAfterAction: 3000,
    },
  ],
};

export default tutorial;
