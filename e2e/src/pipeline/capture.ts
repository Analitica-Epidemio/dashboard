import { chromium, type BrowserContext, type Page } from "playwright";
import { mkdirSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import type { TutorialDefinition, CaptureResult } from "../types.js";
import { loginViaUI } from "../utils/auth.js";
import { injectCursor } from "../utils/cursor.js";
import { highlightElement } from "../utils/highlight.js";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";

interface CaptureOptions {
  headed?: boolean;
}

export async function capture(
  tutorial: TutorialDefinition,
  outputDir: string,
  options: CaptureOptions = {}
): Promise<CaptureResult> {
  const videoDir = resolve(outputDir, "raw");
  if (!existsSync(videoDir)) {
    mkdirSync(videoDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: !options.headed,
  });

  const context: BrowserContext = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: {
      dir: videoDir,
      size: { width: 1280, height: 720 },
    },
  });

  const page: Page = await context.newPage();
  const timestamps: Record<string, number> = {};
  const startTime = Date.now();

  try {
    // Inyectar cursor visible para el video
    await injectCursor(page);

    // Login
    console.log("     → Iniciando sesión...");
    await loginViaUI(page);

    // Navegar a la URL inicial del tutorial
    const setupUrl = `${BASE_URL}${tutorial.setupPath}`;
    console.log(`     → Navegando a ${setupUrl}`);
    await page.goto(setupUrl, { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    // Ejecutar cada paso
    for (const step of tutorial.steps) {
      console.log(`     → Paso: ${step.id}`);
      timestamps[step.id] = Date.now() - startTime;

      // Resaltar elemento si se especifica
      if (step.highlight) {
        await highlightElement(page, step.highlight);
      }

      // Ejecutar la acción
      await step.action(page);

      // Esperar después de la acción
      const waitTime = step.waitAfterAction ?? 1000;
      await page.waitForTimeout(waitTime);
    }

    // Espera final para que el video cierre bien
    await page.waitForTimeout(2000);
  } finally {
    await context.close();
    await browser.close();
  }

  // Playwright guarda el video como .webm en el directorio de grabación.
  // Buscamos el archivo generado.
  const { readdirSync } = await import("node:fs");
  const videoFiles = readdirSync(videoDir).filter((f) => f.endsWith(".webm"));
  const videoPath = videoFiles.length > 0 ? resolve(videoDir, videoFiles[0]) : "";

  if (!videoPath) {
    throw new Error("No se encontró el video grabado");
  }

  console.log(`     → Video guardado: ${videoPath}`);

  return { videoPath, timestamps };
}
