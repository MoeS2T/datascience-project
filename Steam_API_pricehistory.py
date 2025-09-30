import os
import re
import time
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
import pandas as pd

# -----------------
# CONFIG
# -----------------
APPID_DEFAULT = 730  # 730 = CS2/CS:GO, 570 = Dota 2, 440 = TF2
APPID_CS = 730
APPID_DOTA = 570
APPID_TF2 = 440
CURRENCY = 3 # 1=USD, 2=GBP, 3=EUR
COUNTRY = "DE"
REQUESTS_PER_MINUTE = 20
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

# Game prefix for CSV filenames
GAME_PREFIX_CS = "CS_"
GAME_PREFIX_DOTA = "Dota_"
GAME_PREFIX_TF2 = "TF2_"

#ITEMS no prefix (CS only)
ITEMS = [
    "AK-47 | Aquamarine Revenge (Field-Tested)",
"AK-47 | Asiimov (Field-Tested)",
"AK-47 | Bloodsport (Field-Tested)",
"AK-47 | Fire Serpent (Field-Tested)",
"AK-47 | Fuel Injector (Field-Tested)",
"AK-47 | Gold Arabesque (Field-Tested)",
"AK-47 | Jaguar (Field-Tested)",
"AK-47 | Leet Museo (Field-Tested)",
"AK-47 | Legion of Anubis (Field-Tested)",
"AK-47 | Neon Revolution (Field-Tested)",
"AK-47 | Neon Rider (Field-Tested)",
"AK-47 | Nightwish (Field-Tested)",
"AK-47 | Redline (Field-Tested)",
"AK-47 | The Empress (Field-Tested)",
"AK-47 | Vulcan (Field-Tested)",
"AK-47 | Wasteland Rebel (Field-Tested)",
"AK-47 | Wild Lotus (Field-Tested)",
"AK-47 | X-Ray (Field-Tested)",
"AUG | Akihabara Accept (Field-Tested)",
"AUG | Chameleon (Field-Tested)",
"AUG | Stymphalian (Field-Tested)",
"AWP | Asiimov (Field-Tested)",
"AWP | Atheris (Field-Tested)",
"AWP | Chromatic Aberration (Field-Tested)",
"AWP | Containment Breach (Field-Tested)",
"AWP | Desert Hydra (Field-Tested)",
"AWP | Dragon Lore (Field-Tested)",
"AWP | Gungnir (Field-Tested)",
"AWP | Hyper Beast (Field-Tested)",
"AWP | Man-o'-war (Field-Tested)",
"AWP | Medusa (Field-Tested)",
"AWP | Neo-Noir (Field-Tested)",
"AWP | Oni Taiji (Field-Tested)",
"AWP | The Prince (Field-Tested)",
"AWP | Wildfire (Field-Tested)",
"CZ75-Auto | Crimson Web (Field-Tested)",
"CZ75-Auto | Tigris (Field-Tested)",
"CZ75-Auto | Victoria (Factory New)",
"CZ75-Auto | Victoria (Field-Tested)",
"Desert Eagle | Blaze (Factory New)",
"Desert Eagle | Code Red (Field-Tested)",
"Desert Eagle | Kumicho Dragon (Field-Tested)",
"Desert Eagle | Midnight Storm (Field-Tested)",
"Desert Eagle | Ocean Drive (Field-Tested)",
"Desert Eagle | Printstream (Field-Tested)",
"FAMAS | Afterimage (Field-Tested)",
"FAMAS | Commemoration (Field-Tested)",
"FAMAS | Mecha Industries (Field-Tested)",
"FAMAS | Roll Cage (Field-Tested)",
"Five-SeveN | Angry Mob (Field-Tested)",
"Five-SeveN | Hyper Beast (Field-Tested)",
"Galil AR | Chatterbox (Field-Tested)",
"Glock-18 | Bullet Queen (Field-Tested)",
"Glock-18 | Gamma Doppler (Field-Tested)",
"Glock-18 | Neo-Noir (Field-Tested)",
"Glock-18 | Wasteland Rebel (Field-Tested)",
"Glock-18 | Water Elemental (Field-Tested)",
"M4A1-S | Chantico's Fire (Field-Tested)",
"M4A1-S | Cyrex (Field-Tested)",
"M4A1-S | Golden Coil (Field-Tested)",
"M4A1-S | Guardian (Field-Tested)",
"M4A1-S | Hyper Beast (Field-Tested)",
"M4A1-S | Imminent Danger (Field-Tested)",
"M4A1-S | Mecha Industries (Field-Tested)",
"M4A1-S | Player Two (Field-Tested)",
"M4A1-S | Printstream (Field-Tested)",
"M4A1-S | Welcome to the Jungle (Field-Tested)",
"M4A4 | Asiimov (Field-Tested)",
"M4A4 | Bullet Rain (Field-Tested)",
"M4A4 | Buzz Kill (Field-Tested)",
"M4A4 | Howl (Factory New)",
"M4A4 | In Living Color (Field-Tested)",
"M4A4 | Neo-Noir (Field-Tested)",
"M4A4 | Royal Paladin (Field-Tested)",
"M4A4 | The Battlestar (Field-Tested)",
"M4A4 | The Coalition (Field-Tested)",
"M4A4 | The Emperor (Field-Tested)",
"M4A4 | X-Ray (Field-Tested)",
"MAC-10 | Neon Rider (Field-Tested)",
"MAC-10 | Stalker (Field-Tested)",
"MP5-SD | Gauss (Field-Tested)",
"MP5-SD | Kitbash (Field-Tested)",
"MP5-SD | Phosphor (Field-Tested)",
"MP7 | Bloodsport (Field-Tested)",
"MP7 | Cirrus (Field-Tested)",
"MP7 | Nemesis (Field-Tested)",
"MP9 | Food Chain (Field-Tested)",
"MP9 | Ruby Poison Dart (Field-Tested)",
"MP9 | Stained Glass (Field-Tested)",
"MP9 | Starlight Protector (Field-Tested)",
"P2000 | Fire Elemental (Field-Tested)",
"P250 | Sand Dune (Field-Tested)",
"P250 | See Ya Later (Field-Tested)",
"P90 | Asiimov (Field-Tested)",
"P90 | Death by Kitty (Field-Tested)",
"PP-Bizon | Fuel Rod (Field-Tested)",
"PP-Bizon | Judgement of Anubis (Field-Tested)",
"PP-Bizon | Osiris (Field-Tested)",
"R8 Revolver | Bone Mask (Field-Tested)",
"R8 Revolver | Fade (Field-Tested)",
"R8 Revolver | Reboot (Field-Tested)",
"Sawed-Off | The Kraken (Field-Tested)",
"SG 553 | Colony IV (Field-Tested)",
"SG 553 | Integrale (Field-Tested)",
"SG 553 | Tiger Moth (Field-Tested)",
"SSG 08 | Blood in the Water (Field-Tested)",
"SSG 08 | Dragonfire (Field-Tested)",
"Tec-9 | Avalanche (Field-Tested)",
"Tec-9 | Fuel Injector (Field-Tested)",
"Tec-9 | Nuclear Threat (Field-Tested)",
"USP-S | Kill Confirmed (Field-Tested)",
"USP-S | Neo-Noir (Field-Tested)",
"USP-S | Printstream (Field-Tested)",
"Kilowatt Case",
"Revolution Case",
"USP-S | The Traitor (Field-Tested)"

    
]

ITEMS_CS = [

]

ITEMS_DOTA = [
]

ITEMS_TF2 = [

]

STEAM_LOGIN_SECURE = os.getenv("STEAM_LOGIN_SECURE", "").strip()


SESSIONID = os.getenv("sessionid", "").strip()
# -----------------
# Helpers
# -----------------
def ensure_dir(path: str) -> None:
    """
    Create the directory for the CSV files if it doesnt exist.
    Args:
        path: Path of the directory
    """
    os.makedirs(path, exist_ok=True)

def rate_limit_sleep() -> None:
    """
    Sets the requests timelimit.
    """
    delay = max(60.0 / float(REQUESTS_PER_MINUTE), 0.05)
    time.sleep(delay)

def market_hash_quote(name: str) -> str:
    """
    URL-encode the hash names from the items.
    Args:
        name: the hash name you want to encode
    Returns:
        str: the encoded string
    """
    return urllib.parse.quote(name, safe='')

def parse_history_timestamp(ts: str) -> Optional[datetime]:
    """
    Parse Steam history timestamps with multiple formats.
    Args:
        ts: The timestamp you want to parse
    Returns:
        datetime: Returns the transformed datetime
    """
    if not isinstance(ts, str):
        return None
    ts = ts.strip()
    if ts.endswith("+0"):
        ts = ts[:-2].strip()
    ts = ts.replace("  ", " ")
    if ts.endswith(":"):
        ts = ts[:-1]
    for fmt in ("%b %d %Y %H", "%b %d %Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except Exception:
            continue
    return None

def steam_get(url: str, session: Optional[requests.Session] = None, **kwargs) -> requests.Response:
    """
    Sets headers and the Cookie for the pricehistory api and then request it.
    Args:
        url: The url with the hashname
        session: Optional session for connection pooling
        **kwargs: Possibility to add more parameters to the request
    Returns:
        requests.response: the request if it was successful
    Raises:
        RuntimeError: if the request was not successful

    """
    sess = session or requests.Session()
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", "Mozilla/5.0 SteamMarketData/2.1")
    headers.setdefault("Accept", "application/json, text/javascript, */*; q=0.01")
    headers.setdefault("Referer", "https://steamcommunity.com/market/")
    headers.setdefault("X-Requested-With", "XMLHttpRequest")
    cookies = kwargs.pop("cookies", {})
    if STEAM_LOGIN_SECURE:
        cookies["steamLoginSecure"] = STEAM_LOGIN_SECURE
    if SESSIONID:    
        cookies["sessionid"] = SESSIONID

    attempt = 0
    last_exc: Optional[Exception] = None
    while attempt < MAX_RETRIES:
        try:
            resp = sess.get(url, headers=headers, cookies=cookies, timeout=30, **kwargs)
            if resp.status_code in (400, 403, 429, 502, 503):
                raise requests.HTTPError(f"{resp.status_code} for {url}", response=resp)
            resp.raise_for_status()
            rate_limit_sleep()
            return resp
        except Exception as e:
            last_exc = e
            attempt += 1
            time.sleep(RETRY_BACKOFF ** attempt)
    raise RuntimeError(f"Steam GET failed: {last_exc}")

def build_pricehistory_urls(appid: int, currency: int, country: str, item_name: str) -> List[str]:
    """
    Build a list of urls for the pricehistory request.
    Args:
        appid: the market you want to request (730 for CSGO/CS2)
        currency: the currency which you want (3 = €)
        country: The country you want to request
        item_name: The specific hash name from the item you want to request

    Returns:
        list: a list of urls from all the items you want to request

    """
    qname = market_hash_quote(item_name)
    base = f"https://steamcommunity.com/market/pricehistory/?appid={appid}&market_hash_name={qname}"
    return [
      base + f"&country={country}&currency={currency}",
      base + f"&currency={currency}",
      base
    ]

# -----------------
# Fetch functions
# -----------------

def fetch_pricehistory(appid: int, currency: int, country: str, item_name: str, session: Optional[requests.Session] = None) -> pd.DataFrame:
    """
    Fetch and transform the requested data per item from a JSON into a dataframe.

    Args:
        appid: the market you want to request (730 for CSGO/CS2)
        currency: the currency which you want (3 = €)
        country: The country you want to request
        item_name: The specific hash name from the item you want to request
        session: Optional session for re-use

    Returns:
        pd.DataFrame: data with the columns:
            - timestamp (datetime)
            - price_mean (float)
            - price_median (float)
            - volume_sum (float)

    Raises:
        RuntimeError: If no attempt is successful

    """
    last_err: Optional[Exception] = None
    for url in build_pricehistory_urls(appid, currency, country, item_name):
        try:
            headers = {"Referer": f"https://steamcommunity.com/market/listings/{appid}/{market_hash_quote(item_name)}"}
            resp = steam_get(url, session=session, headers=headers)
            data = resp.json()
            if not data.get("success"):
                continue
            rows = data.get("prices", [])
            df = pd.DataFrame(rows, columns=["timestamp_raw", "price", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp_raw"].apply(parse_history_timestamp))
            df = df.dropna(subset=["timestamp"]).copy()
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
            df = df.dropna(subset=["price", "volume"]).copy()
            if df.empty:
                continue
            # Aggregate daily
            df = df.set_index("timestamp").sort_index()
            daily = df.resample("D").agg(
                price_mean=("price", "mean"),
                price_median=("price", "median"),
                volume_sum=("volume", "sum")
            ).reset_index()
            return daily
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch price history for '{item_name}'. Last error: {last_err}")

# -----------------
# Main
# -----------------
def main():
    """
    Fetch price histories for the items and write them into a CSV file.
    """
    ensure_dir("data")
    session = requests.Session()

    for item in ITEMS:

        print(f"[+] Fetching price history for: {item}")
        df = fetch_pricehistory(APPID_DEFAULT, CURRENCY, COUNTRY, item, session=session)

        safe_name = item.replace(" ", "_").replace("|", "").replace("/", "-")
        csv_path = os.path.join("data", f"{safe_name}_history.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"    Saved history to: {csv_path}")
        
    for item in ITEMS_CS:

        print(f"[+] Fetching price history for: {item}")
        df = fetch_pricehistory(APPID_CS, CURRENCY, COUNTRY, item, session=session)

        safe_name = item.replace(" ", "_").replace("|", "").replace("/", "-")
        csv_path = os.path.join("data", f"{GAME_PREFIX_CS}{safe_name}_history.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"    Saved history to: {csv_path}")

    for item in ITEMS_DOTA:

        print(f"[+] Fetching price history for: {item}")
        df = fetch_pricehistory(APPID_DOTA, CURRENCY, COUNTRY, item, session=session)

        safe_name = item.replace(" ", "_").replace("|", "").replace("/", "-")
        csv_path = os.path.join("data", f"{GAME_PREFIX_DOTA}{safe_name}_history.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"    Saved history to: {csv_path}")
        
    for item in ITEMS_TF2:

        print(f"[+] Fetching price history for: {item}")
        df = fetch_pricehistory(APPID_TF2, CURRENCY, COUNTRY, item, session=session)

        safe_name = item.replace(" ", "_").replace("|", "").replace("/", "-")
        csv_path = os.path.join("data", f"{GAME_PREFIX_TF2}{safe_name}_history.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"    Saved history to: {csv_path}")

if __name__ == "__main__":
    main()
