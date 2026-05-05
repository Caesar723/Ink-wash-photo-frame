from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright


class BrowserRenderer:
    def __init__(self, config):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None

    async def start(self):
        if self.browser is not None:
            return

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-extensions",
                "--disable-sync",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--disable-translate",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
            ],
        )

        self.context = await self.browser.new_context(
            viewport={
                "width": self.config["target_img_size"][1],
                "height": self.config["target_img_size"][0],
            },
            device_scale_factor=1,
        )

    async def render_url(self, url: str):
        await self.start()

        page = None
        try:
            page = await self.context.new_page()

            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45_000,
            )

            # 给 CSS、字体、图片一点时间渲染
            await page.wait_for_timeout(1000)

            image_bytes = await page.screenshot(
                full_page=False,
                timeout=45_000,
            )

            with Image.open(BytesIO(image_bytes)) as img:
                return img.convert("RGB").copy()

        finally:
            if page is not None:
                await page.close()

    async def close(self):
        if self.context is not None:
            await self.context.close()
            self.context = None

        if self.browser is not None:
            await self.browser.close()
            self.browser = None

        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None