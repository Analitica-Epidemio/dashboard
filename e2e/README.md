# E2E Tests & Tutoriales en Video

Tests end-to-end con Playwright y generador de videos tutoriales para el dashboard de epidemiología.

## Setup

```bash
# Desde la raíz del proyecto:
make e2e-setup

# O manualmente:
cd e2e
pnpm install
pnpm exec playwright install chromium
```

Copiar `.env.example` a `.env` y completar las credenciales:

```bash
cp .env.example .env
```

## Tests E2E

```bash
# Correr todos los tests
make e2e-test

# Con browser visible
make e2e-test-headed

# Con UI interactiva de Playwright
cd e2e && pnpm test:ui

# Con debugger (paso a paso)
cd e2e && pnpm test:debug

# Un test específico
cd e2e && pnpm test -- login
```

### Crear un test nuevo

1. Crear archivo en `src/tests/mi-test.spec.ts`
2. Usar helpers de `src/utils/` para login, esperas, etc.

```ts
import { test, expect } from "@playwright/test";
import "dotenv/config";

test("mi feature funciona", async ({ page }) => {
  // Usar loginViaUI si necesitás estar logueado:
  // import { loginViaUI } from "../utils/auth.js";
  // await loginViaUI(page);

  await page.goto("/mi-pagina");
  await expect(page.locator("h1")).toContainText("Mi Título");
});
```

## Tutoriales en Video

Graba videos del dashboard navegando automáticamente. Útil para onboarding y documentación.

```bash
# Grabar un tutorial (con browser visible)
make e2e-tutorial t=ejemplo-login

# Sin browser visible (más rápido)
cd e2e && pnpm tutorial ejemplo-login

# Saltar fases
cd e2e && pnpm start --tutorial ejemplo-login --skip-narrate --skip-compose
```

Los videos se guardan en `output/<tutorial-id>/`.

### Crear un tutorial nuevo

1. Crear archivo en `src/tutorials/mi-tutorial.ts`
2. Exportar un `TutorialDefinition` por default

```ts
import type { TutorialDefinition } from "../types.js";

const tutorial: TutorialDefinition = {
  id: "mi-tutorial",
  title: "Mi Tutorial",
  description: "Qué muestra este tutorial",
  setupPath: "/pagina-inicial",
  steps: [
    {
      id: "paso-1",
      narration: "Texto para el TTS",
      action: async (page) => {
        await page.click("button.mi-boton");
      },
      waitAfterAction: 2000,
      highlight: "button.mi-boton", // opcional: resalta el elemento
    },
  ],
};

export default tutorial;
```

3. Correr: `make e2e-tutorial t=mi-tutorial`

## Estructura

```
e2e/
├── src/
│   ├── types.ts              # Tipos compartidos
│   ├── cli.ts                # Entry point del CLI de tutoriales
│   ├── pipeline/
│   │   ├── capture.ts        # Graba video con Playwright
│   │   ├── narrate.ts        # TTS con ElevenLabs (opcional)
│   │   └── compose.ts        # Merge video+audio con FFmpeg
│   ├── utils/
│   │   ├── auth.ts           # Login (UI y API)
│   │   ├── page-helpers.ts   # Helpers: waitForUrl, safeClick, etc.
│   │   ├── cursor.ts         # Cursor SVG visible en videos
│   │   └── highlight.ts      # Highlight de elementos en videos
│   ├── tutorials/            # Definiciones de tutoriales
│   │   └── ejemplo-login.ts
│   └── tests/                # Tests E2E
│       └── login.spec.ts
├── output/                   # Videos generados (gitignored)
├── playwright.config.ts
└── .env.example
```

## Utils disponibles

### `auth.ts`
- `loginViaUI(page)` — llena el form de login (simula usuario real)
- `loginViaAPI(context)` — login programático (más rápido, para tests)
- `isLoggedIn(page)` — chequea si hay sesión activa
- `logout(page)` — cierra sesión

### `page-helpers.ts`
- `waitForUrl(page, "/dashboard")` — espera URL
- `waitForSelector(page, ".mi-clase")` — espera elemento visible
- `waitForIdle(page)` — espera que no haya requests pendientes
- `safeClick(page, "button")` — espera visible + click
- `safeFill(page, "#input", "texto")` — espera visible + fill
- `waitForText(page, "Bienvenido")` — espera texto en pantalla

### `cursor.ts` (solo para tutoriales)
- `injectCursor(page)` — inyecta cursor SVG visible
- `moveCursorTo(page, "selector")` — anima cursor hacia elemento

### `highlight.ts` (solo para tutoriales)
- `highlightElement(page, "selector")` — borde rojo pulsante
- `clearHighlights(page)` — limpia highlights

## Narración con ElevenLabs

La narración TTS es **opcional**. Si `ELEVENLABS_API_KEY` está en `.env`, genera audio real con ElevenLabs. Si no, estima duraciones por largo de texto y el pipeline sigue funcionando (video sin audio).

Para activarlo:

1. Crear cuenta en [elevenlabs.io](https://elevenlabs.io)
2. Copiar tu API key
3. Agregar a `.env`:
   ```
   ELEVENLABS_API_KEY=sk_...
   ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL  # "Sarah" (o elegir otra voz)
   ELEVENLABS_MODEL=eleven_multilingual_v2
   ```

## Composición con FFmpeg

Si tenés FFmpeg instalado, `compose.ts` mezcla video + audio automáticamente en MP4. Si no, copia el video raw.

```bash
brew install ffmpeg
```

## TODOs

- [ ] **Storage state**: guardar sesión para no re-loguearse en cada test
- [ ] **Más tutoriales**: crear tutoriales para cada feature del dashboard
- [ ] **Más tests**: ampliar cobertura E2E
- [ ] **CI**: integrar `pnpm test` en el pipeline de deploy

## Scripts (package.json)

| Script | Descripción |
|---|---|
| `pnpm setup` | Instalar todo (deps + Chromium) |
| `pnpm test` | Correr tests E2E |
| `pnpm test:headed` | Tests con browser visible |
| `pnpm test:ui` | UI interactiva de Playwright |
| `pnpm test:debug` | Tests con debugger paso a paso |
| `pnpm tutorial <id>` | Grabar tutorial (headless) |
| `pnpm tutorial:headed <id>` | Grabar tutorial con browser visible |
| `pnpm typecheck` | Verificar tipos TypeScript |
