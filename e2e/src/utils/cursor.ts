import type { Page } from "playwright";

/**
 * Inyecta un cursor SVG visible en la página.
 *
 * Playwright corre en modo headless sin cursor visible, así que para
 * los videos tutoriales necesitamos inyectar uno que siga al mouse.
 * El cursor se mueve suavemente con CSS transitions.
 */
export async function injectCursor(page: Page): Promise<void> {
  await page.evaluate(() => {
    // Crear el elemento del cursor
    const cursor = document.createElement("div");
    cursor.id = "__playwright-cursor";
    cursor.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M5.65376 12.3673H5.46026L5.31717 12.4976L0.500002 16.8829L0.500002 1.19841L11.7841 12.3673H5.65376Z"
              fill="black" stroke="white" stroke-width="1"/>
      </svg>
    `;

    Object.assign(cursor.style, {
      position: "fixed",
      top: "0",
      left: "0",
      zIndex: "999999",
      pointerEvents: "none",
      transition: "transform 120ms linear",
      transform: "translate(-100px, -100px)",
    });

    document.body.appendChild(cursor);

    // Seguir el mouse
    document.addEventListener("mousemove", (e) => {
      cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
    });

    // Efecto de click: scale bounce
    document.addEventListener("mousedown", () => {
      cursor.style.transition = "transform 80ms ease-in";
      const current = cursor.style.transform;
      cursor.style.transform = current + " scale(0.8)";
    });

    document.addEventListener("mouseup", () => {
      cursor.style.transition = "transform 120ms linear";
      const match = cursor.style.transform.match(
        /translate\([^)]+\)/
      );
      if (match) {
        cursor.style.transform = match[0];
      }
    });
  });
}

/**
 * Mueve el cursor inyectado a una posición específica (para simular movimiento).
 * Útil si querés animar el cursor hacia un elemento antes de hacer click.
 */
export async function moveCursorTo(
  page: Page,
  selector: string
): Promise<void> {
  const box = await page.locator(selector).boundingBox();
  if (box) {
    await page.mouse.move(
      box.x + box.width / 2,
      box.y + box.height / 2,
      { steps: 15 }
    );
  }
}
