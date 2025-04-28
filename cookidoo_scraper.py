from local_settings import username, password
import asyncio
import httpx
from selectolax.parser import HTMLParser

BASE_URL = "https://cookidoo.de"

async def get_shopping_list(email: str, password: str) -> list[str]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 1. Startseite laden
        resp = await client.get(BASE_URL)
        tree = HTMLParser(resp.text)

        # 2. Login-Link finden
        login_path = None
        for a in tree.css('a'):
            href = a.attributes.get('href', '')
            if 'profile' in href and 'login' in href:
                login_path = href
                break

        if not login_path:
            raise Exception("Login-Link nicht gefunden!")

        login_url = BASE_URL + login_path

        # 3. Login-Seite laden
        login_page = await client.get(login_url)
        login_tree = HTMLParser(login_page.text)

        # 4. Login-Formular analysieren
        form_action = None
        request_id = None

        for form in login_tree.css('form'):
            form_action = form.attributes.get('action')
            for input_tag in form.css('input'):
                if input_tag.attributes.get('name') == 'requestId':
                    request_id = input_tag.attributes.get('value')
            break

        if not form_action or not request_id:
            raise Exception("Login-Formular oder Request-ID nicht gefunden!")

        # 5. Login-Daten vorbereiten
        login_data = {
            "username": email,
            "password": password,
            "requestId": request_id
        }

        # Wichtig: Login-POST geht auf CIAM-Server!
        login_resp = await client.post(form_action, data=login_data, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE_URL,
            "Referer": login_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        })

        if login_resp.status_code != 200:
            raise Exception(f"Login fehlgeschlagen! Status: {login_resp.status_code}")

        # 6. Check: sind wir jetzt eingeloggt?
        # Lade nochmal die Hauptseite oder direkt die Einkaufsliste
        shopping_url = BASE_URL + "/shopping/de-DE/owned-ingredients"
        shop_resp = await client.get(shopping_url)

        if shop_resp.status_code != 200:
            raise Exception(f"Fehler beim Abrufen der Einkaufsliste! Status: {shop_resp.status_code}")

        # 7. Zutaten extrahieren
        shop_tree = HTMLParser(shop_resp.text)
        ingredients = []

        for li in shop_tree.css('li.pm-check-group__list-item'):
            text = li.text(strip=True)
            if text:
                ingredients.append(text)

        return ingredients

# Test-Call
if __name__ == "__main__":
    import sys

    if not username:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        email = username

    ingredients = asyncio.run(get_shopping_list(email, password))
    print("Gefundene Zutaten:")
    for item in ingredients:
        print("-", item)