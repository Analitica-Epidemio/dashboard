"""
Playwright-based Report Generator
Captures the frontend report page as PDF with exact UI
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright
import tempfile

logger = logging.getLogger(__name__)

class PlaywrightReportGenerator:
    """
    Generates reports by capturing the frontend report page using Playwright.
    This ensures exact UI fidelity in the generated PDFs.
    """

    def __init__(self):
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.timeout = 30000  # 30 seconds timeout

    async def generate_pdf_from_page(
        self,
        combinations: list,
        date_range: Dict[str, str],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF by capturing the report page

        Args:
            combinations: Filter combinations with data
            date_range: Date range for the report
            output_path: Optional path to save the PDF

        Returns:
            PDF content as bytes
        """
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox']
            )

            try:
                # Create new page
                page = await browser.new_page(
                    viewport={'width': 1280, 'height': 1024}
                )

                # Build SSR report page URL with parameters
                params = {
                    'dateFrom': date_range.get('from', ''),
                    'dateTo': date_range.get('to', ''),
                    'filters': self._serialize_combinations(combinations)
                }

                # Use print-optimized page that renders server-side
                report_url = f"{self.frontend_url}/reports-print?{urlencode(params)}"
                logger.info(f"Navigating to report page: {report_url}")

                # Navigate to report page
                await page.goto(report_url, wait_until='networkidle')

                # Wait for page to load completely
                try:
                    # Wait for report content
                    await page.wait_for_selector('#report-content', timeout=self.timeout)
                    logger.info("Report content loaded")

                    # Wait for client-side hydration and chart rendering
                    await asyncio.sleep(2)

                    # Wait for DynamicChart components to render
                    try:
                        await page.wait_for_selector('.dynamic-chart', timeout=15000)
                        logger.info("Dynamic charts detected")
                    except:
                        logger.info("No dynamic charts found, continuing...")

                    # Additional wait for SVG charts to fully render
                    await asyncio.sleep(3)

                    # Check chart containers
                    chart_containers = await page.query_selector_all('.charts-container')
                    if chart_containers:
                        logger.info(f"Found {len(chart_containers)} chart containers")

                    # Count actual SVG elements (from Recharts)
                    svgs = await page.query_selector_all('svg')
                    if svgs:
                        logger.info(f"Found {len(svgs)} SVG charts")

                    # Check for indicators
                    indicators = await page.query_selector_all('.text-2xl.font-bold')
                    if indicators:
                        logger.info(f"Found {len(indicators)} indicators")

                except Exception as e:
                    logger.warning(f"Some elements may not have loaded: {e}")

                # Final wait for complete rendering
                await asyncio.sleep(2)

                # Hide generation controls before capturing
                await page.evaluate("""
                    // Find elements that should be hidden when printing
                    const controls = document.querySelectorAll('[class*="print:hidden"]');
                    controls.forEach(el => el.style.display = 'none');
                    // Also try standard class selector
                    const printHidden = document.querySelectorAll('.print\\\\:hidden');
                    printHidden.forEach(el => el.style.display = 'none');
                """)

                # Generate PDF
                pdf_options = {
                    'format': 'A4',
                    'print_background': True,
                    'margin': {
                        'top': '20px',
                        'right': '20px',
                        'bottom': '20px',
                        'left': '20px'
                    },
                    'prefer_css_page_size': True
                }

                if output_path:
                    pdf_options['path'] = output_path

                pdf_content = await page.pdf(**pdf_options)

                logger.info(f"PDF generated successfully, size: {len(pdf_content)} bytes")
                return pdf_content

            finally:
                await browser.close()

    async def generate_screenshot(
        self,
        combinations: list,
        date_range: Dict[str, str],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate screenshot of the report page

        Args:
            combinations: Filter combinations with data
            date_range: Date range for the report
            output_path: Optional path to save the screenshot

        Returns:
            Screenshot as bytes (PNG)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox']
            )

            try:
                page = await browser.new_page(
                    viewport={'width': 1920, 'height': 1080}
                )

                # Build SSR report page URL with parameters
                params = {
                    'dateFrom': date_range.get('from', ''),
                    'dateTo': date_range.get('to', ''),
                    'filters': self._serialize_combinations(combinations)
                }

                # Use print-optimized page that renders server-side
                report_url = f"{self.frontend_url}/reports-print?{urlencode(params)}"
                logger.info(f"Navigating to report page for screenshot: {report_url}")

                # Navigate to report page
                await page.goto(report_url, wait_until='networkidle')

                # Wait for page to load completely - same timing as PDF generation
                try:
                    # Wait for report content
                    await page.wait_for_selector('#report-content', timeout=self.timeout)
                    logger.info("Report content loaded for screenshot")

                    # Wait for client-side hydration and chart rendering
                    await asyncio.sleep(2)

                    # Wait for DynamicChart components to render
                    try:
                        await page.wait_for_selector('.dynamic-chart', timeout=15000)
                        logger.info("Dynamic charts detected in screenshot")
                    except:
                        logger.info("No dynamic charts found for screenshot, continuing...")

                    # Additional wait for SVG charts to fully render
                    await asyncio.sleep(3)

                    # Count actual SVG elements (from Recharts)
                    svgs = await page.query_selector_all('svg')
                    if svgs:
                        logger.info(f"Found {len(svgs)} SVG charts for screenshot")

                except Exception as e:
                    logger.warning(f"Some elements may not have loaded for screenshot: {e}")

                # Final wait for complete rendering
                await asyncio.sleep(2)

                # Hide controls before capturing
                await page.evaluate("""
                    // Find elements that should be hidden when printing
                    const controls = document.querySelectorAll('[class*="print:hidden"]');
                    controls.forEach(el => el.style.display = 'none');
                    // Also try standard class selector
                    const printHidden = document.querySelectorAll('.print\\\\:hidden');
                    printHidden.forEach(el => el.style.display = 'none');
                """)

                # Take screenshot
                screenshot_options = {
                    'full_page': True,
                    'type': 'png'
                }

                if output_path:
                    screenshot_options['path'] = output_path

                screenshot = await page.screenshot(**screenshot_options)

                logger.info(f"Screenshot generated, size: {len(screenshot)} bytes")
                return screenshot

            finally:
                await browser.close()

    def _serialize_combinations(self, combinations: list) -> str:
        """
        Serialize combinations for URL parameter
        """
        import json

        # Simplify combinations for URL
        simplified = []
        for combo in combinations:
            simplified.append({
                'id': combo.get('id'),
                'groupId': str(combo.get('group_id')) if combo.get('group_id') else None,
                'groupName': combo.get('group_name'),
                'eventIds': combo.get('event_ids', []),
                'eventNames': combo.get('event_names', []),
                'clasificaciones': combo.get('clasificaciones', [])
            })

        return json.dumps(simplified)

    async def test_connection(self) -> bool:
        """
        Test if Playwright can connect to the frontend

        Returns:
            True if connection successful
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    response = await page.goto(self.frontend_url, wait_until='domcontentloaded')
                    success = response.status < 400
                    logger.info(f"Frontend connection test: {'Success' if success else 'Failed'}")
                    return success
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"Frontend connection test failed: {e}")
            return False


# Singleton instance
playwright_generator = PlaywrightReportGenerator()