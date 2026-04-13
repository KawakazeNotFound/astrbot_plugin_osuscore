import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    html_path = Path(__file__).parent / "temp_render.html"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1100, "height": 600})
        await page.goto(f"file://{html_path.resolve()}")
        
        # parent container
        rect = await page.evaluate('''() => {
            let el = document.querySelector(".triple-bar-container");
            let rect = el.getBoundingClientRect();
            return {w: rect.width, h: rect.height, x: rect.x, y: rect.y, display: getComputedStyle(el).display};
        }''')
        print(f"Parent: {rect}")
        
        # children
        children = await page.evaluate('''() => {
            let els = document.querySelectorAll(".triple-bar-container div");
            return Array.from(els).map(el => {
                let rect = el.getBoundingClientRect();
                let style = getComputedStyle(el);
                return {className: el.className, w: rect.width, h: rect.height, bg: style.backgroundColor, text: el.textContent};
            });
        }''')
        for c in children:
            print(f"Child: {c}")
            
        await browser.close()

asyncio.run(main())
