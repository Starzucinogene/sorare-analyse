import requests
import time
import pandas as pd

ETH_EUR_API = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=eur"
SORARE_API = "https://api.sorare.com/graphql"

HEADERS = {"Content-Type": "application/json"}

LIMIT = 5
ALERT_THRESHOLD = 0.9
TARGET_PLAYERS = ["kylian-mbappe", "erling-haaland"]

def get_eth_to_eur():
    try:
        r = requests.get(ETH_EUR_API)
        return r.json()['ethereum']['eur']
    except:
        return None

def get_listed_prices(slug):
    query = """
    query GetListed($slug: String!) {
      player(slug: $slug) {
        cards(first: 5) {
          nodes {
            liveSingleSaleOffer {
              price
            }
          }
        }
      }
    }
    """
    variables = {"slug": slug}
    res = requests.post(SORARE_API, json={"query": query, "variables": variables}, headers=HEADERS)
    try:
        prices = [int(c["liveSingleSaleOffer"]["price"]) / 1e18 for c in res.json()["data"]["player"]["cards"]["nodes"] if c["liveSingleSaleOffer"]]
        return prices
    except:
        return []

def get_sales_history(slug):
    query = """
    query GetSales($slug: String!) {
      player(slug: $slug) {
        cardSample(first: 5) {
          nodes {
            price
          }
        }
      }
    }
    """
    variables = {"slug": slug}
    res = requests.post(SORARE_API, json={"query": query, "variables": variables}, headers=HEADERS)
    try:
        prices = [int(c["price"]) / 1e18 for c in res.json()["data"]["player"]["cardSample"]["nodes"]]
        return prices
    except:
        return []

def scan_players():
    eth_to_eur = get_eth_to_eur() or 0
    alerts = []
    all_data = []

    for slug in TARGET_PLAYERS:
        listed = get_listed_prices(slug)
        sold = get_sales_history(slug)
        all_prices = listed + sold

        if not listed or not sold:
            continue

        avg_price = sum(all_prices) / len(all_prices)
        min_current = min(listed)

        alert = min_current < avg_price * ALERT_THRESHOLD
        eur_price = min_current * eth_to_eur

        all_data.append({
            "slug": slug,
            "min_price_eth": min_current,
            "min_price_eur": eur_price,
            "avg_eth": avg_price,
            "avg_eur": avg_price * eth_to_eur,
            "alert": alert
        })

        if alert:
            alerts.append(slug)

        time.sleep(1.5)

    return pd.DataFrame(all_data), alerts
