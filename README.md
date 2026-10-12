# Amazon Price Tracker (Python + Node)

![ScrapeAtlas](assets/scrapeatlas_logo.png)

A tiny tool that searches Amazon for a keyword (or watches a list of ASINs) and appends
price snapshots to a CSV, so you can build a price history over time with cron.

Scraping Amazon directly means CAPTCHAs, rotating proxies and broken selectors. This example
uses the [ScrapeAtlas](https://scrapeatlas.com) public-data API instead, which returns
structured JSON (`price.current`, `price.original`, `rating.average`, ...). New accounts get
100 free credits; one successful request = 1 credit, failed requests are free.

## Quick start
```bash
pip install -r core/requirements.txt
export SCRAPEATLAS_API_KEY=sa_live_...      # Dashboard -> API keys
python core/price_tracker.py --query "wireless earbuds" --pages 1
python core/price_tracker.py --asin B09DT48V16 --country US
node core/price_tracker.mjs "mechanical keyboard"
```
Run it daily (`0 8 * * * python price_tracker.py --asin ...`) and `prices.csv` becomes your price history.

## Endpoints used
| Method | Path | Params |
|---|---|---|
| GET | `/v1/amazon/product-search` | `query` (req), `country`, `cursor`, `page` |
| GET | `/v1/amazon/product` | `asin` (req), `country` |

Auth: `x-api-key` header. Pagination: pass `pagination.next_cursor` back as `cursor`
(each page is a separate request). Full reference: <https://scrapeatlas.com/docs/>.

## Notes
- Check `status`: `partial` = usable data with some fields missing (see `coverage.warnings`).
- Call the API from a server or script, not browser JS: CORS only allows scrapeatlas.com, and
  you shouldn't ship an API key to the front end.
- Only public, logged-out data. Respect Amazon's terms and your local laws.

MIT licensed.
