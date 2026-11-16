import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy import or_, select

from db import Base, Phone, PhoneFeature, Price, SessionLocal, Specification, engine

BASE = "https://www.gsmarena.com/"
BRAND_URL = BASE + "samsung-phones-9.php"
RAW_DIR = Path("data/raw")
DELAY_SECONDS = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StudentProjectBot/1.0; coursework project, 20s delay between requests)"}
KNOWN_URLS = {
    "Galaxy S23":       "https://www.gsmarena.com/samsung_galaxy_s23-12082.php",
    "Galaxy S23+":      "https://www.gsmarena.com/samsung_galaxy_s23+-12083.php",
    "Galaxy S23 FE":    "https://www.gsmarena.com/samsung_galaxy_s23_fe-12520.php",
    "Galaxy S24":       "https://www.gsmarena.com/samsung_galaxy_s24-12773.php",
    "Galaxy S25":       "https://www.gsmarena.com/samsung_galaxy_s25-13610.php",
    "Galaxy S25 Ultra": "https://www.gsmarena.com/samsung_galaxy_s25_ultra-13322.php",
    "Galaxy S26":       "https://www.gsmarena.com/samsung_galaxy_s26_5g-14456.php",
    "Galaxy S26 Ultra": "https://www.gsmarena.com/samsung_galaxy_s26_ultra_5g-14320.php",
    "Galaxy A36":       "https://www.gsmarena.com/samsung_galaxy_a36-13497.php",
    "Galaxy A26":       "https://www.gsmarena.com/samsung_galaxy_a26-13679.php",
    "Galaxy A57":       "https://www.gsmarena.com/samsung_galaxy_a57_5g-14379.php",
    "Galaxy A17":       "https://www.gsmarena.com/samsung_galaxy_a17_5g-14041.php",
    "Galaxy S22 5G":    "https://www.gsmarena.com/samsung_galaxy_s22_5g-11253.php",
}


class Blocked(Exception):
    pass


CURRENCIES = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}
VARIANT = re.compile(r"\d+\s*(GB|TB)", re.I)


def fetch(url):
    """Return (html, fetched_at). A saved copy in data/raw is reused, so pages are downloaded once."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / (Path(urlparse(url).path).stem + ".html")
    if not path.exists():
        blocked = False
        for attempt in range(1, 6):
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
            except requests.RequestException as exc:
                print(f"  network error ({type(exc).__name__}), retry {attempt}/5")
                time.sleep(10)
                continue
            if r.status_code == 200:
                path.write_text(r.text, encoding="utf-8")
                time.sleep(DELAY_SECONDS)
                break
            if r.status_code in (429, 503):
                blocked = True
                retry_after = r.headers.get("Retry-After", "")
                wait = int(retry_after) if retry_after.isdigit() else 60 * 2 ** (attempt - 1)
                if wait > 600:
                    raise Blocked(f"HTTP {r.status_code}, Retry-After={wait}s for {url}")
                print(f"  HTTP {r.status_code} (too many requests), waiting {wait}s, attempt {attempt}/5")
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {r.status_code} for {url}")
        else:
            if blocked:
                raise Blocked(f"GSMArena kept refusing requests (HTTP 429/503) for {url}")
            raise RuntimeError(f"could not fetch {url}")
    fetched_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return path.read_text(encoding="utf-8"), fetched_at


def norm(name):
    return re.sub(r"\s+", " ", name.lower().replace("samsung", "")).strip()


def find_phone_urls(targets, max_pages=35):
    wanted = {}
    for t in targets:
        wanted[norm(t)] = t
        wanted[norm(t) + " 5g"] = t
    found = {}
    url = BRAND_URL
    for page in range(1, max_pages + 1):
        html, _ = fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("div.makers ul li a"):
            strong = a.select_one("strong")
            if strong and a.get("href"):
                target = wanted.get(norm(strong.get_text(" ", strip=True)))
                if target and target not in found:
                    found[target] = urljoin(BASE, a["href"])
        print(f"  listing page {page}: {len(found)} of {len(targets)} phones found")
        if len(found) == len(targets):
            break
        nxt = next((a for a in soup.select("a.prevnextbutton") if "next" in (a.get("title") or "").lower()), None)
        if not nxt or not nxt.get("href"):
            break
        url = urljoin(BASE, nxt["href"])
    return found


def clean(text):
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def parse_spec_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("h1.specs-phone-name-title")
    if not title:
        raise ValueError("phone title not found (page layout changed or request blocked)")
    img = soup.select_one("div.specs-photo-main img")
    id_match = re.search(r"-(\d+)\.php$", urlparse(url).path)
    rows = []
    for table in soup.select("#specs-list table"):
        th = table.find("th")
        category = clean(th.get_text(" ")) if th else ""
        for tr in table.select("tr"):
            nfo = tr.select_one("td.nfo")
            if not nfo:
                continue
            ttl = tr.select_one("td.ttl")
            rows.append({
                "category": category,
                "label": (clean(ttl.get_text(" ")) if ttl else "") or "Other",
                "value": clean(nfo.get_text(" ")),
                "code": nfo.get("data-spec"),
            })
    return {
        "name": clean(title.get_text(" ")),
        "gsmarena_id": int(id_match.group(1)) if id_match else None,
        "url": url,
        "image_url": img["src"] if img and img.get("src") else None,
        "rows": rows,
    }


def num(pattern, text, cast=float):
    m = re.search(pattern, text or "", re.I)
    return cast(m.group(1).replace(",", "")) if m else None


def hours(text):
    m = re.search(r"(\d+):(\d+)\s*h", text or "")
    if m:
        return round(int(m.group(1)) + int(m.group(2)) / 60, 2)
    return num(r"(\d+(?:\.\d+)?)\s*h", text)


def extract_features(rows):
    code = {r["code"]: r["value"] for r in rows if r["code"]}

    def by_label(category, label):
        return next((r["value"] for r in rows if r["category"] == category and r["label"] == label), "")

    memory = code.get("internalmemory", "")
    sizes = sorted({int(n) * (1024 if u.upper() == "TB" else 1)
                    for n, u in re.findall(r"(\d+)\s*(GB|TB)\s+\d+\s*GB\s+RAM", memory, re.I)})
    rams = [int(x) for x in re.findall(r"(\d+)\s*GB\s+RAM", memory, re.I)]
    charging = by_label("Battery", "Charging")
    return {
        "release_year": num(r"(20\d\d)", code.get("year"), int),
        "os": (code.get("os") or "")[:200] or None,
        "chipset": (code.get("chipset") or "")[:200] or None,
        "display_size_in": num(r"([\d.]+)\s*inches", code.get("displaysize")),
        "display_type": (code.get("displaytype") or "")[:200] or None,
        "resolution": (code.get("displayresolution") or by_label("Display", "Resolution"))[:120] or None,
        "ram_gb": max(rams) if rams else None,
        "storage_options": ", ".join(f"{g}GB" if g < 1024 else f"{g // 1024}TB" for g in sizes) or None,
        "main_camera_mp": num(r"([\d.]+)\s*MP", code.get("cam1modules")),
        "selfie_camera_mp": num(r"([\d.]+)\s*MP", code.get("cam2modules")),
        "weight_g": num(r"([\d.]+)\s*g\b", code.get("weight")),
        "battery_mah": num(r"(\d{3,5})\s*mAh", code.get("batdescription1"), int),
        "charging_w": num(r"(\d+)\s*W\s*wired", charging, int) or num(r"(\d+)\s*W", charging, int),
        "active_use_score_h": hours(code.get("batlife2")),
        "endurance_rating_h": hours(code.get("batlife")),
    }


def money(text):
    out = []
    for sym, amt in re.findall(r"([$€£₹])\s*([\d,]+(?:\.\d+)?)", text or ""):
        out.append((CURRENCIES[sym], float(amt.replace(",", "")), f"{sym} {amt}"))
    for amt, cur in re.findall(r"([\d,]+(?:\.\d+)?)\s*(EUR|USD|GBP|INR)\b", text or ""):
        out.append((cur, float(amt.replace(",", "")), f"{amt} {cur}"))
    return out


def price_page_url(html, spec_url):
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True).lower() == "prices" and "-price-" in a["href"]:
            return urljoin(spec_url, a["href"])
    return None


def parse_price_page(html):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for table in soup.select("table"):
        trs = table.select("tr")
        if not trs:
            continue
        header = [clean(c.get_text(" ")) for c in trs[0].find_all(["th", "td"])]
        if not any(VARIANT.search(h) for h in header):
            continue
        for tr in trs[1:]:
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            img = cells[0].find("img")
            store = (img.get("alt") if img and img.get("alt") else clean(cells[0].get_text(" "))) or None
            for i, cell in enumerate(cells[1:], start=1):
                if i >= len(header):
                    break
                for cur, amt, raw in money(clean(cell.get_text(" "))):
                    out.append({"store": store, "variant": header[i], "currency": cur, "amount": amt, "raw": raw})
    return out


def save_phone(session, spec, spec_time, page_prices, price_time):
    conditions = [Phone.name == spec["name"]]
    if spec["gsmarena_id"] is not None:
        conditions.append(Phone.gsmarena_id == spec["gsmarena_id"])
    for old in session.scalars(select(Phone).where(or_(*conditions))).all():
        session.delete(old)
    session.flush()

    price_text = next((r["value"] for r in spec["rows"] if r["code"] == "price"), "")
    prices = [Price(amount=a, currency=c, source="spec_page", raw_text=raw, scraped_at=spec_time)
              for c, a, raw in money(price_text)]
    prices += [Price(amount=p["amount"], currency=p["currency"], variant=p["variant"], store=p["store"],
                     source="price_page", raw_text=p["raw"], scraped_at=price_time)
               for p in page_prices]
    features = extract_features(spec["rows"])
    session.add(Phone(
        name=spec["name"], gsmarena_id=spec["gsmarena_id"], url=spec["url"], image_url=spec["image_url"],
        scraped_at=spec_time,
        specifications=[Specification(category=r["category"], label=r["label"], value=r["value"]) for r in spec["rows"]],
        features=PhoneFeature(**features),
        prices=prices,
    ))
    session.flush()
    return len(spec["rows"]), len(prices), [k for k, v in features.items() if v is None]


def run(targets=None):
    Base.metadata.create_all(engine)
    urls = {n: KNOWN_URLS[n] for n in (targets or KNOWN_URLS) if n in KNOWN_URLS}
    print(f"Queued {len(urls)} phones.")
    ok, failed = 0, []
    for target, url in urls.items():
        try:
            html, spec_time = fetch(url)
            spec = parse_spec_page(html, url)
            page_prices, price_time = [], spec_time
            link = price_page_url(html, url)
            if link:
                try:
                    phtml, price_time = fetch(link)
                    page_prices = parse_price_page(phtml)
                except Exception as exc:
                    print(f"  price page failed for {target}: {exc}")
            with SessionLocal() as session:
                n_specs, n_prices, missing = save_phone(session, spec, spec_time, page_prices, price_time)
                session.commit()
            print(f"OK {spec['name']} | spec rows {n_specs} | prices {n_prices} | empty features: {missing or 'none'}")
            ok += 1
        except Blocked as exc:
            print(f"\nSTOPPED: {exc}\nPhones saved so far are kept. Wait a while, then run the scraper again.")
            break
        except Exception as exc:
            print(f"FAILED {target}: {exc}")
            failed.append(target)
    print(f"\nDone. Saved {ok} of {len(urls)} phones. Failed: {failed or 'none'}")


if __name__ == "__main__":
    run()
