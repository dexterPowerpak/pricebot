
import os, asyncio, json
import yaml
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

async def run():
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="state.json" if os.path.exists("state.json") else None)
        page = await context.new_page()

        # Login only if needed
        await page.goto("https://example.com/account", wait_until="domcontentloaded")
        if "Login" in await page.inner_text("body"):
            await page.goto("https://example.com/login", wait_until="domcontentloaded")
            await page.fill('input[name="username"]', os.environ["SITE_USER"])
            await page.fill('input[name="password"]', os.environ["SITE_PASS"])
            await page.click('button[type="submit"]')
            await page.wait_for_load_state("networkidle")
            await context.storage_state(path="state.json")

        results = []
        for product in config["products"]:
            await page.goto(product["url"], wait_until="networkidle")
            await page.wait_for_selector(product["price_selector"])
            price = await page.inner_text(product["price_selector"])
            sku = None
            if product.get("sku_selector"):
                loc = page.locator(product["sku_selector"])
                if await loc.count():
                    sku = await loc.inner_text()
            results.append({
                "url": product["url"],
                "sku": sku.strip() if sku else None,
                "price": price.strip()
            })

        print(json.dumps(results, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
