import type { Page, BrowserContext } from "playwright";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";
const API_URL = process.env.API_URL ?? "http://localhost:8000";
const LOGIN_EMAIL = process.env.LOGIN_EMAIL ?? "";
const LOGIN_PASSWORD = process.env.LOGIN_PASSWORD ?? "";

/**
 * Login llenando el formulario de /login directamente.
 * Usa los selectores reales del frontend (inputs #email y #password).
 *
 * Es la forma más simple y realista — simula lo que haría un usuario.
 */
export async function loginViaUI(
  page: Page,
  credentials?: { email: string; password: string }
): Promise<void> {
  const email = credentials?.email ?? LOGIN_EMAIL;
  const password = credentials?.password ?? LOGIN_PASSWORD;

  if (!email || !password) {
    throw new Error(
      "Credenciales no configuradas. Setea LOGIN_EMAIL y LOGIN_PASSWORD en .env"
    );
  }

  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });

  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.locator('button[type="submit"]').click();

  // Esperar a que redirija fuera de /login (indica login exitoso)
  await page.waitForURL((url) => !url.pathname.includes("/login"), {
    timeout: 15_000,
  });
}

/**
 * Login programático contra el backend FastAPI + inyectar cookie de NextAuth.
 *
 * Más rápido que loginViaUI porque no renderiza la página de login.
 * Útil para tests donde el login no es lo que estás testeando.
 *
 * Flujo:
 * 1. POST al backend para obtener tokens
 * 2. POST al endpoint de NextAuth para generar la session cookie
 * 3. Inyectar la cookie en el browser context
 */
export async function loginViaAPI(
  context: BrowserContext,
  credentials?: { email: string; password: string }
): Promise<void> {
  const email = credentials?.email ?? LOGIN_EMAIL;
  const password = credentials?.password ?? LOGIN_PASSWORD;

  if (!email || !password) {
    throw new Error(
      "Credenciales no configuradas. Setea LOGIN_EMAIL y LOGIN_PASSWORD en .env"
    );
  }

  // 1. Obtener CSRF token de NextAuth
  const page = await context.newPage();
  const csrfRes = await page.goto(`${BASE_URL}/api/auth/csrf`);
  const csrfData = (await csrfRes?.json()) as { csrfToken: string };
  const csrfToken = csrfData.csrfToken;

  // 2. Login via NextAuth credentials callback
  //    Esto hace que NextAuth llame al backend y setee la session cookie
  await page.goto(`${BASE_URL}/api/auth/callback/credentials`, {
    waitUntil: "commit",
  });

  const response = await page.request.post(
    `${BASE_URL}/api/auth/callback/credentials`,
    {
      form: {
        email,
        password,
        csrfToken,
        json: "true",
      },
    }
  );

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`Login API falló (${response.status()}): ${body}`);
  }

  await page.close();
}

/**
 * Verifica si el usuario está logueado chequeando la session de NextAuth.
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  const response = await page.request.get(`${BASE_URL}/api/auth/session`);
  const session = await response.json();
  return !!session?.user;
}

/**
 * Logout: llama al endpoint de NextAuth para cerrar sesión.
 */
export async function logout(page: Page): Promise<void> {
  // Obtener CSRF token
  const csrfRes = await page.request.get(`${BASE_URL}/api/auth/csrf`);
  const csrfData = (await csrfRes.json()) as { csrfToken: string };

  await page.request.post(`${BASE_URL}/api/auth/signout`, {
    form: {
      csrfToken: csrfData.csrfToken,
      json: "true",
    },
  });
}
