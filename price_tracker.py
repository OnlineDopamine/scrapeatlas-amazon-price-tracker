"""Amazon price tracker: search a keyword or watch ASINs, append snapshots to CSV.

Uses the ScrapeAtlas API (https://scrapeatlas.com). Set SCRAPEATLAS_API_KEY.
"""
import argparse, csv, datetime as dt, os, sys, time
import requests

API = "https://api.scrapeatlas.com/v1/amazon"
KEY = os.environ.get("SCRAPEATLAS_API_KEY")
FIELDS = ["fetched_at", "asin", "title", "price", "list_price", "currency",
          "rating", "ratings_count", "availability", "url"]

def call(path, **params):
    if not KEY:
        sys.exit("Set SCRAPEATLAS_API_KEY (free key at https://scrapeatlas.com)")
    for attempt in range(3):
        r = requests.get(f"{API}/{path}", params=params,
                         headers={"x-api-key": KEY}, timeout=90)
        if r.status_code in (429, 503):
            time.sleep(int(r.headers.get("retry-after", 5)))
            continue
        data = r.json()
        if not data.get("success"):
            f = data.get("failure", {})
            raise RuntimeError(f"{f.get('code')}: {f.get('message')} (requestId {data.get('requestId')})")
        return data
    raise RuntimeError("rate limited, try again later")

def row(p, fetched_at):
    price, rating = p.get("price") or {}, p.get("rating") or {}
    return {"fetched_at": fetched_at, "asin": p.get("id"), "title": p.get("title"),
            "price": price.get("current"), "list_price": price.get("original"),
            "currency": price.get("currency"), "rating": rating.get("average"),
            "ratings_count": rating.get("count"), "availability": p.get("availability"),
            "url": p.get("url")}

def search(query, country="US", pages=1):
    out, cursor = [], None
    for _ in range(pages):  # each page is one charged request
        params = {"query": query, "country": country}
        if cursor: params["cursor"] = cursor
        d = call("product-search", **params)
        out += [row(i["product"], d["fetchedAt"]) for i in d.get("items", [])]
        pag = d.get("pagination") or {}
        if not pag.get("has_more"): break
        cursor = pag.get("next_cursor")
    return out

def products(asins, country="US"):
    return [row((d := call("product", asin=a, country=country))["product"], d["fetchedAt"])
            for a in asins]

def save(rows, path):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        if new: w.writeheader()
        w.writerows(rows)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query"); ap.add_argument("--asin", nargs="*", default=[])
    ap.add_argument("--country", default="US"); ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--out", default="prices.csv")
    a = ap.parse_args()
    rows = search(a.query, a.country, a.pages) if a.query else products(a.asin, a.country)
    save(rows, a.out)
    for r in rows:
        print(f"{r['asin']}  {r['currency'] or ''} {r['price']}  (was {r['list_price']})  {r['title'][:60] if r['title'] else ''}")
    print(f"\nAppended {len(rows)} rows to {a.out} at {dt.datetime.now():%Y-%m-%d %H:%M}")
