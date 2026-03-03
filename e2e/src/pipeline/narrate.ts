import { mkdirSync, existsSync, writeFileSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parseBuffer } from "music-metadata";
import type { TutorialDefinition, NarrationResult } from "../types.js";

const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY ?? "";
const ELEVENLABS_VOICE_ID =
  process.env.ELEVENLABS_VOICE_ID ?? "EXAVITQu4vr4xnSDxMaL"; // "Sarah" por defecto
const ELEVENLABS_MODEL =
  process.env.ELEVENLABS_MODEL ?? "eleven_multilingual_v2";

/** Estima duración en ms basada en largo de texto (~150 palabras/min en español) */
function estimateDuration(text: string): number {
  const words = text.split(/\s+/).length;
  return Math.max(2000, Math.round((words / 150) * 60 * 1000));
}

/** Llama al API de ElevenLabs y retorna el buffer MP3 */
async function generateTTS(text: string): Promise<Buffer> {
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": ELEVENLABS_API_KEY,
      "Content-Type": "application/json",
      Accept: "audio/mpeg",
    },
    body: JSON.stringify({
      text,
      model_id: ELEVENLABS_MODEL,
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75,
        style: 0.0,
        use_speaker_boost: true,
      },
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`ElevenLabs API error (${response.status}): ${body}`);
  }

  const arrayBuffer = await response.arrayBuffer();
  return Buffer.from(arrayBuffer);
}

/** Lee la duración real de un archivo MP3 en milisegundos */
async function getAudioDuration(filePath: string): Promise<number> {
  const buffer = readFileSync(filePath);
  const metadata = await parseBuffer(buffer, { mimeType: "audio/mpeg" });
  const seconds = metadata.format.duration ?? 0;
  return Math.round(seconds * 1000);
}

/**
 * Fase de narración: genera audio TTS para cada paso del tutorial.
 *
 * - Si ELEVENLABS_API_KEY está configurada: genera audio real con ElevenLabs
 * - Si no: usa duraciones estimadas por largo de texto (no genera audio)
 */
export async function narrate(
  tutorial: TutorialDefinition,
  outputDir: string
): Promise<NarrationResult> {
  const audioDir = resolve(outputDir, "audio");
  if (!existsSync(audioDir)) {
    mkdirSync(audioDir, { recursive: true });
  }

  const useTTS = !!ELEVENLABS_API_KEY;
  if (!useTTS) {
    console.log(
      "     ⚠ ELEVENLABS_API_KEY no configurada, usando duraciones estimadas"
    );
  }

  const durations: Record<string, number> = {};

  for (const step of tutorial.steps) {
    const audioPath = resolve(audioDir, `${step.id}.mp3`);

    if (useTTS) {
      // Generar audio real con ElevenLabs
      console.log(`     → Generando TTS para "${step.id}"...`);
      const audioBuffer = await generateTTS(step.narration);
      writeFileSync(audioPath, audioBuffer);
      durations[step.id] = await getAudioDuration(audioPath);
      console.log(`       ✓ ${(durations[step.id] / 1000).toFixed(1)}s`);
    } else {
      // Estimar duración sin generar audio
      durations[step.id] = estimateDuration(step.narration);
      console.log(
        `     → [estimado] "${step.id}": ${(durations[step.id] / 1000).toFixed(1)}s — "${step.narration}"`
      );
    }
  }

  // Guardar duraciones para la fase de composición
  const durationsPath = resolve(outputDir, "durations.json");
  writeFileSync(durationsPath, JSON.stringify(durations, null, 2));

  return { audioPath: audioDir, durations };
}
