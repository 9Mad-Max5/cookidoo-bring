import asyncio
from playwright.async_api import async_playwright
from local_settings import username, password
# EMAIL = "DEINE_EMAIL@domain.com"
# PASSWORD = "DEIN_PASSWORT"
COOKIDOO_URL = "https://cookidoo.de"  # Oder cookidoo.xx je nach Land

async def get_bearer_token():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # False für besseres Debugging
        page = await browser.new_page()

        # Gehe zur Cookidoo-Loginseite
        # await page.goto(f"{COOKIDOO_URL}/login")
        "https://eu.login.vorwerk.com/ciam/login?ui_locales=de-DE&market=de&requestId=7b8ea1c0-ef30-4660-94dd-9d96d764cf0a&view_type=login"

        # Email und Passwort eingeben
        await page.fill('input[type="email"]', username)
        await page.fill('input[type="password"]', password)

        # Auf Login klicken
        await page.click('button[type="submit"]')

        # Warten, bis wir eingeloggt sind (z.B. wenn die Startseite erscheint)
        await page.wait_for_load_state('networkidle')
        
        # Interceptiere alle Requests und filtere den Bearer-Token
        async def handle_request(request):
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer"):
                print(f"Bearer Token gefunden: {auth_header}")
                await browser.close()
                exit(0)

        page.on("request", handle_request)

        # Shopping-List-Seite aufrufen, damit ein autorisierter Request ausgelöst wird
        await page.goto(f"{COOKIDOO_URL}/shopping")

        # Falls kein Token nach einiger Zeit gefunden wird
        await asyncio.sleep(10)
        print("Kein Bearer-Token gefunden.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_bearer_token())
