from local_settings import username, password
import re
import asyncio
from playwright.async_api import async_playwright
from classes import Ingredient
from functions import parse_amount_and_unit

BASE_URL = "https://cookidoo.de"


def parse_ingredients(ingredients):
    ingredients_clean = []

    for raw_ingredient in ingredients:
        if raw_ingredient.startswith("\n"):
            continue

        cleaned = raw_ingredient.strip()
        if not cleaned or cleaned == "\n":
            continue  # leere Einträge überspringen

        # Auftrennen: Zutat und (optional) Menge + Einheit
        parts = cleaned.split("\n")
        name = parts[0].strip()

        amount = None
        unit = None

        if len(parts) > 1:
            # Beispiel: "400 g" -> amount: 400, unit: g
            amount, unit = parse_amount_and_unit(parts[1].strip())
            # amount_unit_match = re.match(r"([\d,\.]+)\s*(.+)", parts[1].strip())
            # if amount_unit_match:
            #     amount_str, unit = amount_unit_match.groups()
            #     amount_str = amount_str.replace(",", ".")  # Komma zu Punkt falls nötig
            #     try:
            #         amount = float(amount_str)
            #     except ValueError:
            #         amount = None  # falls parsing fehlschlägt einfach None setzen

        # Ingredient-Objekt erstellen
        ingredient_obj = Ingredient(name=name, amount=amount, unit=unit)
        ingredients_clean.append(ingredient_obj)

    return ingredients_clean


async def cookidoo_shoppinglist(
    email: str, password: str, base_url=BASE_URL, local="de-DE"
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )  # headless=True wenn unsichtbar gewünscht
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Startseite öffnen
        await page.goto(BASE_URL)

        # 2. Cookie-Abfrage akzeptieren (falls vorhanden)
        try:
            await page.click("text=Akzeptieren", timeout=3000)
            print("Cookies akzeptiert.")
        except:
            print("Keine Cookie-Abfrage gefunden.")

        await page.click("button.core-nav__trigger")

        # 2. Auf "Anmelden" klicken
        await page.click("text=Anmelden")

        # 3. Warten bis Login-Seite geladen ist
        await page.wait_for_selector('input[name="username"]')

        # 4. Login-Daten eingeben
        await page.fill('input[name="username"]', email)
        await page.fill('input[name="password"]', password)

        # 5. Formular abschicken
        await page.click('button[type="submit"]')

        # 6. Warten, bis die Seite nach Login geladen hat
        await page.wait_for_load_state("networkidle")

        # 7. Direkt zur Einkaufsliste gehen
        await page.goto(f"{BASE_URL}/shopping/{local}")

        # 8. Zutaten auslesen
        await page.wait_for_selector("li.pm-check-group__list-item")

        ingredients = await page.locator(
            "li.pm-check-group__list-item"
        ).all_inner_texts()

        await browser.close()
        return parse_ingredients(ingredients=ingredients)

from playwright.async_api import Page

async def check_off_transferred_ingredients(page: Page, ingredients: list):
    for ing in ingredients:
        if not ing.transferred:
            continue

        # Baue einen robusten Selektor
        selector = f'li:has(span[data-type="ingredientNotation"]:has-text("{ing.name}"))'
        if ing.amount and ing.unit:
            selector += f':has(span[data-type="value"]:has-text("{int(ing.amount)}"))'
            selector += f':has(span[data-type="unitNotation"]:has-text("{ing.unit}"))'

        li_element = await page.query_selector(selector)
        if li_element:
            checkbox = await li_element.query_selector('core-checkbox')
            if checkbox:
                checked = await checkbox.get_attribute("aria-checked")
                if checked != "true":
                    await checkbox.click()
                    print(f"✓ Abgehakt: {ing.name}")
                else:
                    print(f"⚠️ Bereits abgehakt: {ing.name}")
        else:
            print(f"❌ Nicht gefunden in der Seite: {ing.name}")
