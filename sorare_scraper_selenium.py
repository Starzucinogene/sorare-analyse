from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import requests
import csv
from datetime import datetime

# --- CONFIGURATION ---
URLS = [
    ("https://sorare.com/fr/football/market/new-signings?s=Cards+On+Sale+Newly+Listed", "in-season"),
    ("https://sorare.com/fr/football/market/manager-sales?s=Cards+On+Sale+Newly+Listed", "classic")
]
WAIT_SECONDS = 10
SCROLL_PAUSE = 3
SCROLL_TIMES = 5
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1366673980945334334/j0oQUz3cc8Y50AY-Gbl0e1RQQU9dIhPgwYsH4Mj6lk-mY6f4-49dJLkQCJjegkwxppeS"  # à remplir
ALERT_THRESHOLD = 0.9
MAX_PRICE_ETH = 0.08
OUTPUT_CSV = "sorare_cards.csv"
FILTERED_PLAYERS = []  # Slugs ciblés (laisser vide pour tout)
FILTERED_POSITIONS = []  # Postes ciblés (laisser vide pour tout)
FILTERED_RARITIES = []  # Raretés ciblées (laisser vide pour tout)

# --- CONVERSION ETH → EUR ---
def get_eth_to_eur():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=eur")
        return r.json()['ethereum']['eur']
    except:
        return None

# --- API PRIX + INFOS SORARE ---
def get_card_info(slug):
    query = """
    query PlayerPrices($slug: String!) {
      player(slug: $slug) {
        position
        cards(first: 1) {
          nodes {
            rarity
            liveSingleSaleOffer {
              price
            }
          }
        }
      }
    }
    """
    variables = {"slug": slug}
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        "https://api.sorare.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers
    )
    try:
        data = response.json()["data"]["player"]
        position = data["position"].lower()
        card = data["cards"]["nodes"][0]
        rarity = card["rarity"].lower()
        price_wei = int(card["liveSingleSaleOffer"]["price"])
        return price_wei / 1e18, position, rarity
    except:
        return None, None, None

# --- DISCORD ---
def send_discord_alert(name, slug, price_eth, price_eur, url):
    if not DISCORD_WEBHOOK_URL:
        return
    message = {
        "content": f"**ALERTE SORARE !**\n{name} ({slug})\nPrix: {price_eth:.4f} ETH ({price_eur:.2f} €)\n{url}"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=message)

# --- CSV SETUP ---
with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Nom", "Slug", "Poste", "Rareté", "Marché", "Prix Affiché", "Prix API (ETH)", "Prix API (EUR)", "URL", "Date"])

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    try:
        for url, market_label in URLS:
            print(f"\n--- Analyse du marché : {market_label.upper()} ---\n")
            driver.get(url)
            time.sleep(WAIT_SECONDS)

            for _ in range(SCROLL_TIMES):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE)

            cards = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/football/player/"]')
            seen = set()
            eth_to_eur = get_eth_to_eur()

            print("Cartes détectées :")
            for card in cards:
                url = card.get_attribute("href")
                if url and url not in seen:
                    seen.add(url)

                    slug_match = re.search(r'/player/([a-z0-9\-]+)', url)
                    slug = slug_match.group(1) if slug_match else "N/A"

                    if FILTERED_PLAYERS and slug not in FILTERED_PLAYERS:
                        continue

                    name_elem = card.find_element(By.CSS_SELECTOR, 'div.text-base')
                    price_elem = card.find_element(By.CSS_SELECTOR, 'div.text-sm')
                    name = name_elem.text if name_elem else "Nom inconnu"
                    price_displayed = price_elem.text if price_elem else "Prix inconnu"

                    price_eth, position, rarity = get_card_info(slug)
                    if not all([price_eth, position, rarity]):
                        continue

                    if FILTERED_POSITIONS and position not in FILTERED_POSITIONS:
                        continue
                    if FILTERED_RARITIES and rarity not in FILTERED_RARITIES:
                        continue

                    if price_eth <= MAX_PRICE_ETH:
                        price_eur = price_eth * eth_to_eur if eth_to_eur else 0
                        print(f"- {name} | Slug: {slug} | Poste: {position} | Rareté: {rarity} | Marché: {market_label} | Affiché: {price_displayed} | API: {price_eth:.4f} ETH ({price_eur:.2f} €) | URL: {url}")
                        writer.writerow([name, slug, position, rarity, market_label, price_displayed, f"{price_eth:.4f}", f"{price_eur:.2f}", url, datetime.now().isoformat()])

                        if price_eth < ALERT_THRESHOLD:
                            send_discord_alert(name, slug, price_eth, price_eur, url)
                    else:
                        print(f"(Ignoré) {name} | Trop cher ou filtré.")

    finally:
        driver.quit()
