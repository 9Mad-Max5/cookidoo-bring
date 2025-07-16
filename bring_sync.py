import os
import sys
import logging
import aiohttp
import asyncio

from cookidoo_scraper_new import CookidooScraper
from bring_api import Bring
from pint import UnitRegistry
from pint.errors import UndefinedUnitError

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

ureg = UnitRegistry(auto_reduce_dimensions=True)
ureg.formatter.default_format = "~"
Q_ = ureg.Quantity

def is_valid_quantity(q: str) -> bool:
    try:
        Q_(q)
        return True
    except Exception:
        return False


def add_normalize_quantity(q1: str, q2: str) -> str:
    """Addiere zwei Mengenstrings und gebe Ergebnis im Format 123g zurück."""
    try:
        a = Q_(q1)
        b = Q_(q2)

        # Einheit der ersten Angabe beibehalten
        result = a + b.to(a.units)

        # Format ohne Leerzeichen
        value = round(result.magnitude, 2)  # z. B. 123.45
        unit = f"{result.units:~}"  # z. B. "g" statt "gram"
        return f"{value:g}{unit}"  # z. B. "400g" statt "400 g"
    except Exception as e:
        raise ValueError(f"Konnte Mengen nicht verarbeiten: {q1} + {q2} ({e})")


def normalize_quantity(q1: str) -> str:
    """Normalisiere ein Mengenstrings und gebe Ergebnis im Format 123g zurück."""
    try:
        result = Q_(q1)
        # Format ohne Leerzeichen
        value = round(result.magnitude, 2)  # z. B. 123.45
        unit = f"{result.units:~}"  # z. B. "g" statt "gram"
        return f"{value:g}{unit}"  # z. B. "400g" statt "400 g"
    except Exception as e:
        raise ValueError(f"Konnte Mengen nicht verarbeiten: {q1} + {q2} ({e})")


def attempt_to_combine(q1, q2):
    if is_valid_quantity(q1) and is_valid_quantity(q2):
        return add_normalize_quantity(q1, q2)
    elif is_valid_quantity(q2):
        return normalize_quantity(q2)
    elif is_valid_quantity(q1):
        return normalize_quantity(q1)
    else:
        # Fallback, z. B. originalen Text beibehalten oder ignorieren
        return q1 or q2  # je nachdem, was sinnvoll ist


async def push_to_bring(
    username: str, password: str, liste: str, ingredients: list, adding_mode=False
):
    async with aiohttp.ClientSession() as session:
        # Create Bring instance with email and password
        bring = Bring(session, username, password)
        # Login
        await bring.login()

        # Get information about all available shopping lists
        bringesponselists = await bring.load_lists()
        bringlists = bringesponselists.lists
        for lis in bringlists:
            if liste in lis.name:
                selected_list = lis

        items = await bring.get_list(selected_list.listUuid)
        existing_items = [
            item.itemId.lower() for item in items.items.purchase
        ]  # alles lowercase für Robustheit

        # Save an item with specifications to a certain shopping list
        # ingredient = Ingredient()

        for ingredient in ingredients:
            if ingredient.unit and ingredient.amount:
                specification = f"{ingredient.amount}{ingredient.unit}"
            elif ingredient.amount:
                specification = f"{int(ingredient.amount)}"
            else:
                specification = ""

            if ingredient.name.lower() not in existing_items:
                await bring.save_item(
                    list_uuid=selected_list.listUuid,
                    item_name=ingredient.name,
                    specification=str(specification),
                )
                # await bring.save_item(
                #     list_uuid=selected_list.listUuid,
                #     item_name=ingredient.name,
                #     specification=str(specification),
                # )
                ingredient.transferred = True

            elif adding_mode:

                for item in items.items.purchase:
                    if item.itemId.lower() == ingredient.name.lower() and specification:
                        try:
                            new_amount = attempt_to_combine(
                                item.specification, specification
                            )
                            await bring.update_item(
                                list_uuid=selected_list.listUuid,
                                item_name=ingredient.name,
                                specification=str(new_amount),
                            )
                        except UndefinedUnitError:
                            # Da es wahrscheinlich eh nur um einen nicht messbaren Wert handelt können wir ihn verwerfen
                            continue
                            await bring.update_item(
                                list_uuid=selected_list.listUuid,
                                item_name=ingredient.name,
                                specification=str(Q_(specification)),
                            )


# if __name__ == "__main__":
#     import sys

#     if not username:
#         email = sys.argv[1]
#         password = sys.argv[2]
#     else:
#         email = username

#     ingredients = asyncio.run(cookidoo_shoppinglist(email, password))
#     asyncio.run(
#         push_to_bring(
#             username=bring_user,
#             password=bring_pw,
#             liste=LISTE,
#             ingredients=ingredients,
#             adding_mode=True,
#         )
#     )

#     print(ingredients)

#     check_off_transferred_ingredients()


async def main():
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    bring_user = os.getenv("BRING_USER")
    bring_pw = os.getenv("BRING_PW")
    liste = os.getenv("LISTE")
    cookidoo_url = os.getenv("COOKIDOO_URL", "https://cookidoo.de")
    cookidoo_lang = os.getenv("COOKIDOO_LANG", "de-DE")

    # Fehlende Variablen prüfen
    missing = []

    if not username:
        missing.append("Cookidoo username (USERNAME)")
    if not password:
        missing.append("Cookidoo password (PASSWORD)")
    if not bring_user:
        missing.append("Bring username (BRING_USER)")
    if not bring_pw:
        missing.append("Bring password (BRING_PW)")
    if not liste:
        missing.append("Shopping list (LISTE)")

    if missing:
        print("Missing environment variables:")
        for item in missing:
            print(" -", item)
        print("Please add them to your docker environment.")
        sys.exit(1)

    # Login-Daten aus local_settings oder CLI
    email = username if username else sys.argv[1]
    pw = password if username else sys.argv[2]

    # Scraper mit Cookie-Cache und Passwortschutz initialisieren
    scraper = CookidooScraper(email=email, password=pw, base_url=cookidoo_url, locale=cookidoo_lang)
    await scraper.launch()

    # Zutaten holen
    ingredients = await scraper.fetch_ingredients()

    # Zutaten an Bring! übertragen
    await push_to_bring(
        username=bring_user,
        password=bring_pw,
        liste=liste,
        ingredients=ingredients,
        adding_mode=False,
    )

    # Ausgabe zur Kontrolle
    # print(ingredients)
    await scraper.check_off_transferred_ingredients(ingredients=ingredients)
    await scraper.close()


import time


async def main_loop():
    interval_minutes = int(os.getenv("INTERVAL_MINUTES", "15"))  # Default 15 min

    while True:
        try:
            await main()
        except Exception as e:
            logging.exception("Error in the main loop: %s", e)

        logging.info(f"Wait {interval_minutes} minutes till the next run...")
        await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    asyncio.run(main_loop())
