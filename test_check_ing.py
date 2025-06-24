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
