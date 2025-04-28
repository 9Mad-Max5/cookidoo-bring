from local_settings import bring_user, bring_pw
from bring_api import Bring

import aiohttp
import asyncio
import logging
import sys

from bring_api import Bring

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

LISTE = "Wohnung"

async def main():
  async with aiohttp.ClientSession() as session:
    # Create Bring instance with email and password
    bring = Bring(session, bring_user, bring_pw)
    # Login
    await bring.login()

    # Get information about all available shopping lists
    bringesponselists = await bring.load_lists()
    bringlists = bringesponselists.lists
    for lis in bringlists:
      if LISTE in lis.name:
        wohnungs_list = lis

    # Save an item with specifications to a certain shopping list
    await bring.save_item(wohnungs_list.listUuid, 'Frischkäse')

    # Save another item
    await bring.save_item(wohnungs_list.listUuid, 'Karotten')

    # Get all the items of a list
    items = await bring.get_list(wohnungs_list.listUuid)
    print(items)

    # # Check off an item
    # await bring.complete_item(lists[0]['listUuid'], 'Carrots')

    # # Remove an item from a list
    # await bring.remove_item(lists[0]['listUuid'], 'Milk')

asyncio.run(main())

# # Hol dir deine Standardliste
# shopping_lists = bring.load_lists()
# list_uuid = shopping_lists["lists"][0]["listUuid"]  # erste Liste nehmen

# # Artikel hinzufügen
# bring.save_item("Milch", "", list_uuid)
# bring.save_item("Eier", "", list_uuid)
# print("Zutaten erfolgreich hinzugefügt!")
