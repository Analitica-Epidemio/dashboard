import type { Page } from "playwright";

const DEFAULT_TIMEOUT = 10_000;

/**
 * Espera hasta que la URL contenga el substring dado.
 */
export async function waitForUrl(
  page: Page,
  substring: string,
  timeout = DEFAULT_TIMEOUT
): Promise<void> {
  await page.waitForURL((url) => url.toString().includes(substring), {
    timeout,
  });
}

/**
 * Espera un selector con timeout razonable y retorna el elemento.
 */
export async function waitForSelector(
  page: Page,
  selector: string,
  options: { timeout?: number; state?: "visible" | "attached" | "hidden" } = {}
) {
  return page.waitForSelector(selector, {
    timeout: options.timeout ?? DEFAULT_TIMEOUT,
    state: options.state ?? "visible",
  });
}

/**
 * Espera a que la página termine de cargar (sin requests de red pendientes).
 */
export async function waitForIdle(
  page: Page,
  timeout = DEFAULT_TIMEOUT
): Promise<void> {
  await page.waitForLoadState("networkidle", { timeout });
}

/**
 * Hace click en un elemento esperando a que sea visible primero.
 */
export async function safeClick(
  page: Page,
  selector: string,
  options: { timeout?: number } = {}
): Promise<void> {
  const el = await page.waitForSelector(selector, {
    state: "visible",
    timeout: options.timeout ?? DEFAULT_TIMEOUT,
  });
  await el.click();
}

/**
 * Llena un input esperando a que sea visible primero.
 */
export async function safeFill(
  page: Page,
  selector: string,
  value: string,
  options: { timeout?: number } = {}
): Promise<void> {
  const el = await page.waitForSelector(selector, {
    state: "visible",
    timeout: options.timeout ?? DEFAULT_TIMEOUT,
  });
  await el.fill(value);
}

/**
 * Toma un screenshot y lo guarda en el directorio dado.
 */
export async function takeScreenshot(
  page: Page,
  path: string,
  options: { fullPage?: boolean } = {}
): Promise<void> {
  await page.screenshot({
    path,
    fullPage: options.fullPage ?? false,
  });
}

/**
 * Espera a que un texto específico aparezca en la página.
 */
export async function waitForText(
  page: Page,
  text: string,
  timeout = DEFAULT_TIMEOUT
): Promise<void> {
  await page.getByText(text).waitFor({ state: "visible", timeout });
}
