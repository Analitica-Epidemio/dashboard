import { test, expect } from "@playwright/test";
import "dotenv/config";

/**
 * Test E2E ejemplo: verifica que el login funcione.
 *
 * Para crear más tests, copiá este archivo.
 * Usá los helpers de ../utils/ para login, esperas, etc.
 *
 * Correr:    pnpm test
 * Con UI:    pnpm test:headed
 * Un solo:   pnpm test -- login
 */

const EMAIL = process.env.LOGIN_EMAIL ?? "";
const PASSWORD = process.env.LOGIN_PASSWORD ?? "";

test.describe("Login", () => {
  test("muestra la página de login", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("#email")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("login exitoso redirige al dashboard", async ({ page }) => {
    test.skip(!EMAIL || !PASSWORD, "LOGIN_EMAIL y LOGIN_PASSWORD requeridos");

    await page.goto("/login");
    await page.locator("#email").fill(EMAIL);
    await page.locator("#password").fill(PASSWORD);
    await page.locator('button[type="submit"]').click();

    // Debe salir de /login
    await page.waitForURL((url) => !url.pathname.includes("/login"), {
      timeout: 15_000,
    });

    // Verificar que estamos en el dashboard (no en login)
    expect(page.url()).not.toContain("/login");
  });

  test("login con credenciales inválidas muestra error", async ({ page }) => {
    await page.goto("/login");
    await page.locator("#email").fill("no-existe@test.com");
    await page.locator("#password").fill("password-invalido");
    await page.locator('button[type="submit"]').click();

    // Debe quedarse en /login (no redirigir)
    await page.waitForTimeout(3000);
    expect(page.url()).toContain("/login");
  });
});
