import asyncio
import json
import os
import base64
import hashlib
from typing import List
from cryptography.fernet import Fernet
from playwright.async_api import async_playwright, Page
from functions import parse_amount_and_unit
from classes import Ingredient

BASE_URL = "https://cookidoo.de"
COOKIE_FILE = "cookidoo_cookies.enc"


class CookidooScraper:
    def __init__(self, email: str, password: str, base_url=BASE_URL, locale="de-DE"):
        self.email = email
        self.password = password
        self.base_url = base_url
        self.locale = locale
        self.context = None
        self.page = None
        self.browser = None

    # just a wrapper now to maintain the 
    def _generate_key(self):
        return self._password_to_fernet_key(self.password)

    def _password_to_fernet_key(self, password: str) -> Fernet:
        # 1. Hash aus Passwort erzeugen (SHA-256 = 32 Bytes)
        key = hashlib.sha256(password.encode()).digest()

        # 2. Base64-codieren → Fernet-kompatibel
        fernet_key = base64.urlsafe_b64encode(key)

        # 3. Fernet-Instanz zurückgeben
        return Fernet(fernet_key)

    def _save_encrypted_cookies(self, cookies):
        fernet = self._generate_key()
        data = json.dumps(cookies).encode()
        encrypted = fernet.encrypt(data)
        with open(COOKIE_FILE, "wb") as f:
            f.write(encrypted)

    def _load_encrypted_cookies(self):
        if not os.path.exists(COOKIE_FILE):
            return None
        fernet = self._generate_key()
        with open(COOKIE_FILE, "rb") as f:
            encrypted = f.read()
        try:
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted)
        except Exception as e:
            print("⚠️ Fehler beim Entschlüsseln der Cookies:", e)
            return None

    async def _accept_cookies(self):
        try:
            await self.page.click("text=Akzeptieren", timeout=3000)
            print("Cookies akzeptiert.")
        except:
            print("Keine Cookie-Abfrage gefunden.")

    async def _login(self):
        await self.page.goto(self.base_url)
        await self._accept_cookies()
        await self.page.click("button.core-nav__trigger")
        await self.page.click("text=Anmelden")
        await self.page.wait_for_selector('input[name="username"]')
        await self.page.fill('input[name="username"]', self.email)
        await self.page.fill('input[name="password"]', self.password)
        await self.page.click('button[type="submit"]')
        await self.page.wait_for_load_state("networkidle")

    async def _load_context(self):
        cookies = self._load_encrypted_cookies()
        context = await self.browser.new_context()
        self.page = await context.new_page()

        if cookies:
            await context.add_cookies(cookies)
            await self.page.goto(f"{self.base_url}/shopping/{self.locale}")
            if "Anmelden" in await self.page.content():
                print("⚠️ Cookies nicht mehr gültig – erneuter Login notwendig.")
                await self._login()
            else:
                print("✅ Login durch gespeicherte Cookies.")
        else:
            await self._login()

        # Cookies nach Login speichern
        cookies = await context.cookies()
        self._save_encrypted_cookies(cookies)
        self.context = context

    async def fetch_ingredients(self) -> List[Ingredient]:
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            await self._load_context()
            await self.page.goto(f"{self.base_url}/shopping/{self.locale}")
            await self.page.wait_for_selector("li.pm-check-group__list-item")

            raw_ingredients = await self.page.locator(
                "li.pm-check-group__list-item"
            ).all_inner_texts()

            return self._parse_ingredients(raw_ingredients)

    def _parse_ingredients(self, ingredients: List[str]) -> List[Ingredient]:
        ingredients_clean = []
        for raw in ingredients:
            if raw.startswith("\n"):
                continue
            parts = raw.strip().split("\n")
            name = parts[0].strip()
            if not name:
                continue
            amount = unit = None
            if len(parts) > 1:
                amount, unit = parse_amount_and_unit(parts[1].strip())
            ingredients_clean.append(Ingredient(name=name, amount=amount, unit=unit))
        return ingredients_clean

    async def check_off_transferred_ingredients(self, ingredients: List[Ingredient]):
        items = self.page.locator("li.pm-check-group__list-item")
        count = await items.count()

        for ing in ingredients:
            if not getattr(ing, "transferred", False):
                continue

            found = False
            for i in range(count):
                item = items.nth(i)

                # Einzelne Felder extrahieren
                try:
                    name = await item.locator('span[data-type="ingredientNotation"]').text_content()
                    value = await item.locator('span[data-type="value"]').text_content()
                    unit = await item.locator('span[data-type="unitNotation"]').text_content()
                except:
                    continue  # Wenn Struktur fehlschlägt, überspringen

                # Whitespace säubern
                name = name.strip()
                value = value.strip()
                unit = unit.strip()

                # Vergleich
                if name == ing.name and value == str(int(ing.amount)) and unit == ing.unit:
                    checkbox = item.locator("core-checkbox")
                    checked = await checkbox.get_attribute("aria-checked")
                    if checked != "true":
                        await checkbox.click()
                        print(f"✓ Abgehakt: {name}")
                    else:
                        print(f"⚠️ Bereits abgehakt: {name}")
                    found = True
                    break

            if not found:
                print(f"❌ Nicht gefunden: {ing.name}")

    async def close(self):
        await self.browser.close()
        # await self.playwright.stop()
