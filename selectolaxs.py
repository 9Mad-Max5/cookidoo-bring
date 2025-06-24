import asyncio
import httpx
from selectolax.parser import HTMLParser
from local_settings import username, password

EMAIL = username
PASSWORD = password
BASE_URL = "https://cookidoo.de"

async def main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 1. Startseite laden
        resp = await client.get(BASE_URL)
        tree = HTMLParser(resp.text)
        
        # 2. Anmelden-Link finden
        login_path = None
        for a in tree.css('a'):
            href = a.attributes.get('href', '')
            if 'profile' in href and 'login' in href:
                login_path = href
                break

        if not login_path:
            raise Exception("Login-Link nicht gefunden!")
        
        login_url = BASE_URL + login_path
        print(f"Gefundener Login-Link: {login_url}")
        
        # 3. Auf Login-Seite gehen
        login_page = await client.get(login_url)
        login_tree = HTMLParser(login_page.text)

        # 4. Login-Formular vorbereiten
        # Herausfinden wie die Form-Felder heißen:
        # In den meisten Fällen: 'email' und 'password'
        form_data = {
            'email': EMAIL,
            'password': PASSWORD,
            # eventuell hidden Inputs wie CSRF-Token auch füllen!
        }

        # Herausfinden wo das Formular hingeht
        form_action = None
        for form in login_tree.css('form'):
            form_action = form.attributes.get('action')
            break

        if not form_action:
            raise Exception("Login-Formular nicht gefunden!")

        form_url = form_action if form_action.startswith('http') else BASE_URL + form_action
        print(f"Login-Formular URL: {form_url}")

        # 5. Login POST
        login_response = await client.post(form_url, data=form_data)
        print(f"Login-Status: {login_response.status_code}")

        # 6. Überprüfen ob Cookies oder Bearer-Token gesetzt sind
        print(f"Cookies nach Login: {client.cookies.jar}")

        # Jetzt kannst du Anfragen an API-Endpunkte machen mit client.get/post etc.
        # Beispiel:
        shop_list_response = await client.get(f"{BASE_URL}/api/v1/shopping-list/items")
        print(shop_list_response.json())

asyncio.run(main())
