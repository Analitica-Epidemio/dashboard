import {
  copyFileSync,
  mkdirSync,
  existsSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { execSync } from "node:child_process";
import { resolve } from "node:path";
import type { TutorialDefinition, ComposeResult } from "../types.js";

/** Chequea si ffmpeg está instalado */
function hasFFmpeg(): boolean {
  try {
    execSync("ffmpeg -version", { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

/**
 * Fase de composición: combina video + audio en un video final.
 *
 * - Si hay archivos de audio y ffmpeg está instalado: merge real
 * - Si no hay audio o no hay ffmpeg: copia el video raw como final
 *
 * Prerequisito para merge real: `brew install ffmpeg`
 */
export async function compose(
  tutorial: TutorialDefinition,
  outputDir: string
): Promise<ComposeResult> {
  const finalDir = resolve(outputDir, "final");
  if (!existsSync(finalDir)) {
    mkdirSync(finalDir, { recursive: true });
  }

  const rawDir = resolve(outputDir, "raw");
  const audioDir = resolve(outputDir, "audio");
  const finalVideoPath = resolve(finalDir, `${tutorial.id}.mp4`);

  // Buscar video raw
  if (!existsSync(rawDir)) {
    console.log("     → No existe directorio raw (¿se saltó la captura?)");
    return { finalVideoPath };
  }

  const videoFiles = readdirSync(rawDir).filter((f) => f.endsWith(".webm"));
  if (videoFiles.length === 0) {
    console.log("     → No se encontró video raw para componer");
    return { finalVideoPath };
  }

  const rawVideoPath = resolve(rawDir, videoFiles[0]);

  // Buscar audios generados
  const audioFiles = existsSync(audioDir)
    ? readdirSync(audioDir)
        .filter((f) => f.endsWith(".mp3"))
        .sort()
    : [];

  const canMerge = audioFiles.length > 0 && hasFFmpeg();

  if (!canMerge) {
    if (audioFiles.length === 0) {
      console.log("     ⚠ No hay archivos de audio, copiando video sin narración");
    } else {
      console.log(
        "     ⚠ ffmpeg no encontrado, copiando video sin narración (instalar: brew install ffmpeg)"
      );
    }

    // Copiar raw como final (sin audio) — convertir a mp4 si hay ffmpeg, sino copiar webm
    if (hasFFmpeg()) {
      execSync(
        `ffmpeg -y -i "${rawVideoPath}" -c:v libx264 -preset fast -crf 23 "${finalVideoPath}"`,
        { stdio: "pipe" }
      );
    } else {
      const webmFinal = finalVideoPath.replace(".mp4", ".webm");
      copyFileSync(rawVideoPath, webmFinal);
      console.log(`     → Video copiado como: ${webmFinal}`);
      return { finalVideoPath: webmFinal };
    }

    console.log(`     → Video guardado: ${finalVideoPath}`);
    return { finalVideoPath };
  }

  // --- Merge real con FFmpeg ---

  // 1. Concatenar todos los audios en uno solo
  const concatListPath = resolve(outputDir, "audio-concat.txt");
  const concatContent = audioFiles
    .map((f) => `file '${resolve(audioDir, f)}'`)
    .join("\n");
  writeFileSync(concatListPath, concatContent);

  const mergedAudioPath = resolve(outputDir, "narration.mp3");
  console.log(`     → Concatenando ${audioFiles.length} audios...`);
  execSync(
    `ffmpeg -y -f concat -safe 0 -i "${concatListPath}" -c copy "${mergedAudioPath}"`,
    { stdio: "pipe" }
  );

  // 2. Merge video + audio
  console.log("     → Mezclando video + audio...");
  execSync(
    `ffmpeg -y -i "${rawVideoPath}" -i "${mergedAudioPath}" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -shortest "${finalVideoPath}"`,
    { stdio: "pipe" }
  );

  console.log(`     → Video final: ${finalVideoPath}`);
  return { finalVideoPath };
}
