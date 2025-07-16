# 🛒 cookidoo-bring

Automatically sync your **Cookidoo** shopping list with your **Bring!** grocery list – no more manual copy-pasting!

This project uses `Playwright` and a headless browser to scrape ingredients from your Cookidoo account and pushes them to a Bring! shopping list. It's ideal for automating your weekly meal planning workflow using Docker.


## ✨ Features

- ✅ Scrapes your Cookidoo shopping list
- ✅ Pushes items to a selected Bring! list
- ✅ Normalizes and merges quantities (e.g., `200g` + `100g` → `300g`)
- ✅ Automatically checks off transferred items in Cookidoo
- ✅ Supports custom sync intervals (e.g., every 15 minutes)
- ✅ Works with country-specific Cookidoo domains/languages


## 🐳 Quick Start with Docker
[container on dockerhub](https://hub.docker.com/r/9madmax5/cookidoo-bring)

Create a `docker-compose.yaml` like this:

```yaml
version: '3.8'

services:
  cookidoo-bring:
    image: 9madmax5/cookidoo-bring:dev
    container_name: cookidoo-bring
    restart: unless-stopped
    environment:
      USERNAME: cookidoo@example.com         # your Cookidoo login email
      PASSWORD: cookidoo_pass               # your Cookidoo password
      BRING_USER: bring@example.com         # your Bring! login email
      BRING_PW: bring_pass                  # your Bring! password
      LISTE: MeineEinkaufsliste             # name of your Bring! shopping list
      INTERVAL_MINUTES: 15                  # optional, default: 15
      COOKIDOO_URL: https://cookidoo.de     # optional, adjust per region
      COOKIDOO_LANG: de-DE                  # optional, e.g., de-DE, en-GB, es-ES
```


## ⚙️ Environment Variables

| Variable           | Required | Description                                                  |
|--------------------|----------|--------------------------------------------------------------|
| `USERNAME`         | ✅        | Cookidoo login email                                         |
| `PASSWORD`         | ✅        | Cookidoo password                                            |
| `BRING_USER`       | ✅        | Bring! login email                                           |
| `BRING_PW`         | ✅        | Bring! password                                              |
| `LISTE`            | ✅        | Name of your Bring! shopping list                           |
| `INTERVAL_MINUTES` | ❌        | Sync interval in minutes (default: `15`)                    |
| `COOKIDOO_URL`     | ❌        | Cookidoo base URL (default: `https://cookidoo.de`)          |
| `COOKIDOO_LANG`    | ❌        | Language code (default: `de-DE`, examples: `en-GB`, `es-ES`) |


## 🔁 How It Works

1. Logs into your Cookidoo account using Playwright (headless browser)
2. Scrapes the current shopping list items
3. Normalizes/combines quantities where appropriate
4. Pushes items to the selected Bring! list
5. Optionally merges similar items
6. Marks items as transferred on Cookidoo to avoid duplicates


## 🧪 Local Development

You need **Python 3.11+**.

```bash
pip install -r requirements.txt
python bring_sync.py
```


## 📅 Usage Scenarios

- Keep your Bring shopping list up to date with your planned Cookidoo meals.
- Syncs quantities in a smart way (e.g. adds amounts together instead of duplicating items).
- Can be scheduled on a server or NAS to run continuously.


## ⚠️ Legal

This project is **not affiliated with**, **endorsed by**, or **associated with** Vorwerk or the Cookidoo service. It merely uses publicly accessible interfaces and resources.

All trademarks and copyrights belong to their respective owners.


## ✉️ Contributing / Issues

Missing a feature or something not working? Please open an [issue on GitHub](https://github.com/9Mad-Max5/cookidoo-bring/issues) and describe the problem or feature request.

Contributions are welcome!
