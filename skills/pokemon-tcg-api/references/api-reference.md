# TCGDex API — Extended Reference

## Pricing (embedded in card detail responses)

### tcgplayer (USD)

Variant keys vary by card: `holofoil`, `reverse-holofoil`, `normal`, `1stEditionHolofoil`, `1stEditionNormal`

```json
{
  "updated": "2026-03-19T20:05:31.000Z",
  "unit": "USD",
  "holofoil": {
    "productId": 232463,
    "lowPrice": 0.02,
    "midPrice": 0.25,
    "highPrice": 10.24,
    "marketPrice": 0.22,
    "directLowPrice": 0.21
  }
}
```

### cardmarket (EUR)

```json
{
  "updated": "2026-03-20T01:46:44.000Z",
  "unit": "EUR",
  "avg": 0.16,
  "low": 0.02,
  "trend": 0.16,
  "avg1": 0.05,
  "avg7": 0.11,
  "avg30": 0.21,
  "avg-holo": 0.39,
  "low-holo": 0.04,
  "trend-holo": 0.39,
  "avg1-holo": 0.1,
  "avg7-holo": 0.33,
  "avg30-holo": 0.34
}
```

---

## Filter Operator Quick Reference

| Operator | Prefix | Example |
|----------|--------|---------|
| Contains (default) | *(none)* | `name=pika` |
| Not contains | `not:` | `name=not:fu` |
| Exact match | `eq:` | `name=eq:Furret` |
| Exact non-match | `neq:` | `name=neq:Furret` |
| >= | `gte:` | `hp=gte:200` |
| <= | `lte:` | `hp=lte:100` |
| > | `gt:` | `hp=gt:150` |
| < | `lt:` | `hp=lt:60` |
| Is null | `null:` | `effect=null:` |
| Not null | `notnull:` | `effect=notnull:` |
| OR | pipe | `name=eq:Furret\|Pikachu` |
| Wildcard | `*` | `name=*chu` or `name=fu*` |

## Sorting & Pagination

```
?sort:field=name&sort:order=DESC
?pagination:page=1&pagination:itemsPerPage=50
```

## All Endpoints

```
# Cards
GET /v2/en/cards                       # Search (CardBrief[])
GET /v2/en/cards/{id}                  # Full card detail
GET /v2/en/sets/{setId}/{localId}      # Card by set + local ID

# Sets & Series
GET /v2/en/sets                        # All sets
GET /v2/en/sets/{setId}                # Set detail + cards
GET /v2/en/series                      # All series
GET /v2/en/series/{serieId}            # Series detail + sets

# Lookup
GET /v2/en/types
GET /v2/en/hps
GET /v2/en/rarities
GET /v2/en/illustrators
GET /v2/en/categories
GET /v2/en/stages
GET /v2/en/suffixes
GET /v2/en/regulationmarks
GET /v2/en/retreats
GET /v2/en/trainertypes
GET /v2/en/energytypes
GET /v2/en/variants
GET /v2/en/dexids
```
