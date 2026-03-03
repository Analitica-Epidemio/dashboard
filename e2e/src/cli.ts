import "dotenv/config";
import { resolve } from "node:path";
import type { CliOptions, TutorialDefinition } from "./types.js";
import { capture } from "./pipeline/capture.js";
import { narrate } from "./pipeline/narrate.js";
import { compose } from "./pipeline/compose.js";

function parseArgs(): CliOptions {
  const args = process.argv.slice(2);
  const options: CliOptions = {
    tutorial: "",
    skipCapture: false,
    skipNarrate: false,
    skipCompose: false,
    headed: false,
    outputDir: resolve(import.meta.dirname, "../output"),
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--tutorial":
      case "-t":
        options.tutorial = args[++i];
        break;
      case "--skip-capture":
        options.skipCapture = true;
        break;
      case "--skip-narrate":
        options.skipNarrate = true;
        break;
      case "--skip-compose":
        options.skipCompose = true;
        break;
      case "--headed":
        options.headed = true;
        break;
      case "--output":
      case "-o":
        options.outputDir = resolve(args[++i]);
        break;
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
    }
  }

  if (!options.tutorial) {
    console.error("Error: --tutorial <id> es requerido\n");
    printHelp();
    process.exit(1);
  }

  return options;
}

function printHelp() {
  console.log(`
Uso: pnpm start --tutorial <id> [opciones]

Opciones:
  --tutorial, -t <id>   ID del tutorial a ejecutar (requerido)
  --skip-capture        Saltar captura de video
  --skip-narrate        Saltar generación de narración
  --skip-compose        Saltar composición final
  --headed              Mostrar el browser (no headless)
  --output, -o <dir>    Directorio de salida (default: ./output)
  --help, -h            Mostrar esta ayuda

Tutoriales disponibles:
  ejemplo-login         Flujo de login al dashboard
`);
}

async function loadTutorial(id: string): Promise<TutorialDefinition> {
  try {
    const mod = await import(`./tutorials/${id}.js`);
    return mod.default as TutorialDefinition;
  } catch {
    console.error(`Error: tutorial "${id}" no encontrado en src/tutorials/`);
    console.error(`Asegurate de que existe el archivo src/tutorials/${id}.ts`);
    process.exit(1);
  }
}

async function main() {
  const options = parseArgs();
  const tutorial = await loadTutorial(options.tutorial);

  console.log(`\n▶ Tutorial: ${tutorial.title}`);
  console.log(`  ${tutorial.description}\n`);

  const outputDir = resolve(options.outputDir, tutorial.id);

  // Fase 1: Narración (genera audio + duraciones)
  if (!options.skipNarrate) {
    console.log("📝 Fase 1: Generando narración...");
    await narrate(tutorial, outputDir);
    console.log("   ✓ Narración completada\n");
  }

  // Fase 2: Captura (graba video del browser)
  if (!options.skipCapture) {
    console.log("🎥 Fase 2: Capturando video...");
    await capture(tutorial, outputDir, { headed: options.headed });
    console.log("   ✓ Captura completada\n");
  }

  // Fase 3: Composición (merge video + audio)
  if (!options.skipCompose) {
    console.log("🎬 Fase 3: Componiendo video final...");
    await compose(tutorial, outputDir);
    console.log("   ✓ Composición completada\n");
  }

  console.log(`✅ Tutorial "${tutorial.id}" generado en: ${outputDir}\n`);
}

main().catch((err) => {
  console.error("Error fatal:", err);
  process.exit(1);
});
