---
name: pokemon-tcg-api
description: Query Pokémon TCG card and set data. Use when searching for Pokémon cards, looking up set/series info, checking market prices, evaluating deck legality, or building any feature that needs TCG card data.
---

# Pokémon TCG API

## Tool Priority

1. **Use the `ptcg-mcp` MCP tools first** (`pokemon-card-search`, `pokemon-card-price`) — they're available in this project and use the official Pokemon TCG API (pokemontcg.io). No API key needed.
2. **Fall back to TCGDex via Bash + curl** if the MCP tools are unavailable or don't return results.

## API Sources

| Source | How to use | Provides |
|--------|-----------|----------|
| **pokemontcg.io** (primary) | MCP tools `pokemon-card-search` / `pokemon-card-price` | Cards, subtypes, legality, TCGPlayer/Cardmarket prices, images |
| **TCGDex** (fallback) | `curl https://api.tcgdex.net/v2/en` | Cards, sets, series, attacks, abilities, prices (USD+EUR), legality, images |

---

## Tool Usage — ALWAYS use Bash + curl

```bash
curl -s --connect-timeout 10 --max-time 30 --retry 3 --retry-delay 2 --retry-all-errors \
  "https://api.tcgdex.net/v2/en/cards?name=charizard" | python3 -m json.tool
```

- Use `curl` via Bash — **never** use WebFetch (it mangles JSON)
- Pipe through `python3 -m json.tool` for readable output, or `jq` if available
- No API key needed — TCGDex is free and unauthenticated
- **The API is intermittently slow** — responses can take 15–25s. Always use `--max-time 30` and `--retry 3`
- `--connect-timeout 10` catches TCP hangs fast; `--max-time 30` allows slow-but-live responses to complete
- Parallel requests are fine — TCGDex handles concurrency well

---

## Endpoints

### Cards

```
GET /v2/en/cards                    # Search/list cards (returns CardBrief[])
GET /v2/en/cards/{id}               # Get full card (e.g. "swsh3-136")
GET /v2/en/sets/{setId}/{localId}   # Get card by set + local number
```

### Sets & Series

```
GET /v2/en/sets                     # List all sets
GET /v2/en/sets/{setId}             # Get set + card list
GET /v2/en/series                   # List all series
GET /v2/en/series/{serieId}         # Get series + sets
```

### Lookup Endpoints (return string/number arrays)

```
GET /v2/en/types                    # Energy types
GET /v2/en/hps                      # All HP values
GET /v2/en/rarities                 # Rarity names
GET /v2/en/illustrators             # Artist names
GET /v2/en/categories               # Pokemon | Trainer | Energy
GET /v2/en/stages                   # Basic, Stage1, Stage2, etc.
GET /v2/en/suffixes                 # EX, GX, V, VMAX, ex, etc.
GET /v2/en/regulationmarks          # Regulation mark letters
GET /v2/en/retreats                 # Retreat cost values
GET /v2/en/trainertypes             # Item, Supporter, Stadium, Tool
GET /v2/en/energytypes              # Basic, Special
GET /v2/en/variants                 # normal, holo, reverse, etc.
GET /v2/en/dexids                   # Pokédex numbers
```

---

## Filtering, Sorting & Pagination

All list endpoints (`/cards`, `/sets`, `/series`) support query params.

### Filter Operators

Append filters as query params. Default match is **case-insensitive contains**.

| Operator | Prefix | Example | Meaning |
|----------|--------|---------|---------|
| Contains (default) | *(none)* or `like:` | `name=pika` | Name contains "pika" |
| Not contains | `not:` or `notlike:` | `name=not:fu` | Name doesn't contain "fu" |
| Exact match | `eq:` | `name=eq:Furret` | Exact name "Furret" |
| Exact non-match | `neq:` | `name=neq:Furret` | Not exactly "Furret" |
| Greater or equal | `gte:` | `hp=gte:200` | HP >= 200 |
| Less or equal | `lte:` | `hp=lte:100` | HP <= 100 |
| Greater than | `gt:` | `hp=gt:150` | HP > 150 |
| Less than | `lt:` | `hp=lt:60` | HP < 60 |
| Is null | `null:` | `effect=null:` | No effect text |
| Not null | `notnull:` | `effect=notnull:` | Has effect text |

**Wildcards:** `name=*chu` (ends with), `name=fu*` (starts with)

**Multiple values (OR):** `name=eq:Furret|Pikachu`

**Multiple filters (AND):** `name=pika&types=Lightning&hp=gte:60`

### Sorting

```
?sort:field=name&sort:order=ASC     # Sort by name ascending
?sort:field=hp&sort:order=DESC      # Sort by HP descending
```

Default sort: releaseDate > localId > id

### Pagination

```
?pagination:page=1&pagination:itemsPerPage=50
```

Default: 100 items per page when pagination is active.

---

## Response Schemas

### CardBrief (from list/search endpoints)

```json
{
  "id": "swsh4.5-33",
  "localId": "33",
  "name": "Luxray",
  "image": "https://assets.tcgdex.net/en/swsh/swsh4.5/33"
}
```

### Card (from detail endpoint)

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Global ID e.g. `swsh3-136` |
| `localId` | string | Number within set |
| `name` | string | Card name |
| `category` | string | `"Pokemon"`, `"Trainer"`, `"Energy"` |
| `hp` | int | Hit points |
| `types` | string[] | Energy types e.g. `["Lightning"]` |
| `stage` | string | `"Basic"`, `"Stage1"`, `"Stage2"`, `"MEGA"`, etc. |
| `evolveFrom` | string | Previous evolution name |
| `attacks` | Attack[] | `{cost: string[], name: string, effect?: string, damage: string\|int}` |
| `abilities` | Ability[] | `{type: string, name: string, effect: string}` |
| `weaknesses` | Weakness[] | `{type: string, value: string}` |
| `retreat` | int | Retreat cost |
| `rarity` | string | Rarity classification |
| `regulationMark` | string | Format regulation letter |
| `illustrator` | string | Artist name |
| `description` | string | Flavor text |
| `dexId` | int[] | Pokédex numbers |
| `image` | string | Image URL (append `/high.png` for hi-res) |
| `set` | SetBrief | `{id, name, logo, symbol, cardCount}` |
| `variants` | object | `{normal, holo, reverse, firstEdition, wPromo}` booleans |
| `legal` | object | `{standard: bool, expanded: bool}` |
| `pricing` | object | See Pricing section below |

### Pricing (embedded in Card detail)

```json
"pricing": {
  "tcgplayer": {
    "updated": "2026-03-19T20:05:31.000Z",
    "unit": "USD",
    "holofoil": {
      "lowPrice": 0.02, "midPrice": 0.25, "highPrice": 10.24,
      "marketPrice": 0.22, "directLowPrice": 0.21
    },
    "reverse-holofoil": { ... }
  },
  "cardmarket": {
    "updated": "2026-03-20T01:46:44.000Z",
    "unit": "EUR",
    "avg": 0.16, "low": 0.02, "trend": 0.16,
    "avg1": 0.05, "avg7": 0.11, "avg30": 0.21,
    "avg-holo": 0.39, "low-holo": 0.04, "trend-holo": 0.39
  }
}
```

---

## Common Search Patterns

Define a helper alias for brevity (or inline the flags each time):

```bash
# Recommended curl flags — always use these
CURL="curl -s --connect-timeout 10 --max-time 30 --retry 3 --retry-delay 2 --retry-all-errors"

# Lightning Pokémon with HP >= 130 (non-ex single-prize attackers)
$CURL "https://api.tcgdex.net/v2/en/cards?types=Lightning&hp=gte:130&category=Pokemon&suffix=null:" | python3 -m json.tool

# All Mega evolution cards
$CURL "https://api.tcgdex.net/v2/en/cards?stage=MEGA" | python3 -m json.tool

# Cards by name
$CURL "https://api.tcgdex.net/v2/en/cards?name=manectric" | python3 -m json.tool

# Trainer Items with "bench" in name
$CURL "https://api.tcgdex.net/v2/en/cards?category=Trainer&trainerType=Item&name=bench" | python3 -m json.tool

# Cards from a specific set
$CURL "https://api.tcgdex.net/v2/en/cards?set=Phantom%20Forces" | python3 -m json.tool

# Full card detail by ID
$CURL "https://api.tcgdex.net/v2/en/cards/swsh4.5-33" | python3 -m json.tool

# Expanded-legal cards only (check legal field on individual cards)
# Note: legal field is only on full card objects, not CardBrief

# Parallel fetches for multiple cards (background jobs)
$CURL "https://api.tcgdex.net/v2/en/cards/swsh4-1" > /tmp/card1.json &
$CURL "https://api.tcgdex.net/v2/en/cards/swsh4-2" > /tmp/card2.json &
wait  # wait for all background jobs
```

## Tips

- **Search returns CardBrief** (id, name, localId, image only). To get attacks/HP/abilities, fetch the full card by ID.
- **Filter by suffix** to find ex/EX/V/VMAX etc.: `suffix=ex` or `suffix=null:` for non-suffix (single-prize) cards.
- **Language swap:** Replace `/en/` with `/fr/`, `/ja/`, `/pt/`, etc. for localized data.
- **Images:** Card image URL + `/high.png` for hi-res, `/low.webp` for thumbnails.

---

## Standard 2026 Rotation (effective April 10, 2026)

**Legal regulation marks: H, I, J** — Reg G and older are OUT.

The rotation went live for in-person Play! Pokémon events on **April 10, 2026** (Pokémon TCG Live updated March 26). It coincided with the release of the **Perfect Order** expansion (sv10.5).

> **API lag warning:** The TCGDex API may still show `standard: true` for Reg G cards and may not yet have correct regulation marks for the newest Perfect Order reprints. Always cross-reference with the official Pokémon website for final legality. Treat any card with `regulationMark: G` as rotated regardless of the `standard` field.

> **"Trick" reprint warning:** Shiny Treasure ex / Paldean Fates cards look newer but most kept their original **G** regulation mark and are NOT legal. Always check the physical card's bottom-left corner: G = out, H/I/J = legal.

---

### ❌ Departed — no legal reprints (rotated out)

**Pokémon:**

| Card | What was lost |
|---|---|
| Gardevoir ex | "Psychic Embrace" engine gone |
| Charizard ex (Obsidian Flames) | "Infernal Reign" gone |
| Pidgeot ex | "Quick Search" gone — consistency hit for many decks |
| Baxcalibur | "Super Cold" Water acceleration gone |
| Mew ex | "Restart" + "Genome Hack" utility gone |
| Squawkabilly ex | Turn 1 "Squawk and Seize" gone |

**Trainers & Energy:**

| Card | Impact |
|---|---|
| Iono | Biggest loss — dominant hand disruption + late-game comeback |
| Nest Ball | Major consistency hit for Basic-heavy decks — no legal reprint |
| Arven | Decks using TMs and Rare Candy via Arven restructuring |
| Battle VIP Pass | Already gone earlier; spiritual successors also squeezed |
| Reversal Energy | Massive hit to comeback decks (Luxray, single-prize archetypes) |
| Jet Energy | Movement much harder without this |
| Earthen Vessel | Energy search significantly weakened — no legal reprint |
| Pal Pad | No legal reprint |
| Counter Catcher | Gone |

---

### ✅ Survivors — reprinted with H, I, or J marks

Even if your physical card has a G mark, you can use it if a newer legal version exists.

| Card | Legal reprint ID | Reg | Notes |
|---|---|---|---|
| Ultra Ball | me01-131 | I | API-verified |
| Boss's Orders | me01-114 / me02.5-183 | I | API-verified |
| Switch | me01-130 / me02-123 | I | API-verified |
| Rare Candy | me01-175 | I | API-verified |
| Night Stretcher | sv06.5-061 / me01-173 | H | API-verified |
| Buddy-Buddy Poffin | sv05-144 / sv08.5-101 / me01-167 | H | API-verified |
| Energy Retrieval | sv10.5w-082 | I | API-verified |
| Professor's Research | sv10.5 reprint | I/J | Official source — API may show Reg G due to lag |
| Super Rod | Recent reprint | H/I | Official source — API may show Reg G due to lag |

---

### Key new cards filling old roles

| Old card | New replacement | Set ID | Reg |
|---|---|---|---|
| Iono / Prof Research (draw) | Lillie's Determination (shuffle → draw 6, or 8 with 6 prizes) | me01-119 | I |
| Iono (T1 draw) | Carmine (discard hand → draw 5, usable T1 going first) | sv06-145 | H |
| Iono (disruption) | Unfair Stamp (ACE SPEC — after KO, both shuffle + redraw) | sv06-165 | H |
| Nest Ball | Dusk Ball (bottom 7 → take a Pokémon) | sv08-175 | H |
| Nest Ball / search | Pokégear 3.0 (top 7 → take a Supporter) | sv10.5b-084 | I |
| Nest Ball / search | Master Ball (ACE SPEC — search any Pokémon, free) | sv05-153 | H |
| Earthen Vessel | Crispin (Supporter: search 2 energy, attach 1) | sv07-133 | H |
| Arven / Boss's Orders | Boss's Orders reprint | me01-114 | I |

---

### ACE SPEC landscape post-rotation

Only 1 ACE SPEC per deck. Top options:
- **Unfair Stamp** (sv06-165, Reg H): After one of your Pokémon is KO'd, both players shuffle hand + redraw. Best late-game disruption now that Iono is gone. Widely considered the best ACE SPEC post-rotation.
- **Master Ball** (sv05-153, Reg H): Search any Pokémon from deck, no discard cost. Premium in lists hurt by Nest Ball loss.
- **Prime Catcher** (sv08.5-119, Reg H): Gust + pivot in one item.

---

## Standard 2026 Meta Snapshot (April–May 2026)

Snapshot of the post-rotation meta after Perfect Order release. Use this as a starting point — **always re-verify with Limitless TCG before making deck recommendations** (see "Meta research workflow" below). Meta share % drifts week-to-week; archetype names and their core engines are more stable.

### Tier list (April–May 2026)

| Tier | Deck | ~Meta share | Engine |
|---|---|---|---|
| S | **Dragapult ex** | ~20–35% (clear #1) | Drakloak draw + Dragapult dual-target spread; pairs with Dusknoir or Blaziken |
| S | **Mega Lucario ex / Hariyama** | High (Japan top 3) | Stage 1 Mega, 340 HP, Fighting aggro w/ built-in disruption |
| A | **Teal Mask Ogerpon + Mega Meganium ex** | ~6%+ | Mega Meganium ability doubles Ogerpon damage |
| A | **Cynthia's Garchomp ex** | ~5% | High HP attacker + draw support |
| A | **Mega Starmie ex / Mega Froslass ex spread** | Strong (Japan) | Spread engine: Risky Ruins + Munkidori + Yveltal acceleration |
| A | **Rocket's Mewtwo ex (Destined Rivals box)** | ~7% | Toolbox: Mewtwo psychic, Spidops energy, Articuno wall |
| B | **Raging Bolt ex** | ~4–5% | Survivor from prior meta — still reliable |
| B | **N's Zoroark ex** | ~3–4% | Copy-attack engine + draw |
| B | **Crustle Mysterious Rock Inn** | ~10% | Stadium-based control |
| B | **Alakazam / Dudunsparce (single-prize)** | Niche | Best single-prize deck post-rotation |
| B | **Mega Absol ex box** | ~8% | Dark-type box variant |
| C | **Charizard ex / Noctowl** | Mixed | Fire aggro w/ draw — survives rotation |
| C | **Festival Lead (Dipplin/Thwackey)** | ~6% | Lead-disruption gimmick |

### Key meta-defining cards

#### Tech / counter cards (frequently teched in)

| Card | ID | Reg | Role |
|---|---|---|---|
| **Lillie's Clefairy ex** | sv09-056 | H | Anti-Dragon tech: bench damage + Dragons take Psychic weakness. Single-handedly suppresses Dragapult/Lucario in matchups |
| **Jellicent ex** | sv10.5w-045 | I | Item + Tool lock disruption — major disruption piece in current meta |
| **Team Rocket's Watchtower** | sv10-180 | H | Stadium that disables Colorless-type abilities (counters Cinccino, etc.) |
| **Munkidori** (Adrena-Brain) | sv06-095 | H | Move 1 damage counter from your Pokémon to opponent's anywhere — meta spread engine glue |
| **Risky Ruins** | me01-127 | I | Stadium: 30 damage to a benched non-rule-box each turn; passive board chip for spread decks |

#### Draw / consistency engines (replacing rotated Iono/Pidgeot)

| Card | ID | Reg | Role |
|---|---|---|---|
| **Meowth ex** (Last-Ditch Catch) | me03-062 | J | Take damage → search Supporter from deck. Direct Lumineon V replacement. Slots into majority of decks |
| **Hilda** | sv10.5w-084 | I | Supporter: search Special Energy + Evolution Pokémon. Earthen Vessel replacement; called "most powerful staple printed in 2025" |
| **Lillie's Determination** | me01-119 | I | Shuffle hand → draw 6 (or 8 with 6 prizes) — primary Prof Research replacement |
| **Carmine** | sv06-145 | H | Discard hand → draw 5; usable T1 going first, unlike Prof Research |
| **N's Zoroark ex** | sv09-098 | H | Ability copies attacks; doubles as draw engine via Trade |
| **Ethan's Adventure** | (sv-era H) | H | Search 3 Ethan's Pokémon + Basic Fire; powers single-prize Fire archetype |

#### Energy acceleration / search

| Card | ID | Reg | Role |
|---|---|---|---|
| **Crispin** | sv07-133 | H | Supporter: search 2 Special Energy, attach 1. Direct Earthen Vessel replacement |
| **Ignition Energy** | sv10.5w-086 / me02-124 | I/I | Provides 3 Colorless when on Evolution Pokémon. Double Turbo Energy replacement |
| **Telepathic Psychic Energy** | me03-088 | J | Special Psychic Energy that brings Clefairy/Spritzee from deck to bench when attached |
| **Prism Energy** | sv10.5b-086 | I | Counts as every type while attached to a Basic — multi-type enabler |
| **Yveltal** (Corrosive Winds) | sv06.5-035 | H | Spread Dark accelerator — used in Froslass/Yveltal control shells |

#### Mega Evolution ex headliners (from Perfect Order, set me03)

| Card | ID | Reg | Why it matters |
|---|---|---|---|
| **Mega Zygarde ex** | me03-047 | J | Basic Mega ex (no evolution required); Gaia Wave + Nullifying Zero, OHKOs other Mega ex with Core Memory + Premium Power Pro |
| **Mega Clefable ex** | me03-031 | J | Anti-Mega tech: Shooting Moons attack hits Psychic-weak Mega ex hard |
| **Mega Lucario ex** | me01-077 | I | Stage 1 Mega, 340 HP; built-in Boss's Orders effect; Fighting aggro core |
| **Mega Starmie ex** | (me-era I/J) | I/J | Water Mega: Jetting Blow (1-cost bench damage); spread/control core |
| **Mega Froslass ex** | me02.5-047 | I | Resentful Refrain: 50× cards in opponent's hand (unbounded scaling); pairs with Mega Starmie spread |
| **Mega Meganium ex** | me02.5-010 | I | Ability doubles damage of attached Pokémon's attack — engine for Ogerpon/Ethan's Fire |

#### Pokémon search (replacing Nest Ball)

| Card | ID | Reg | Role |
|---|---|---|---|
| **Master Ball** (ACE SPEC) | sv05-153 | H | Search any Pokémon, free; only 1 per deck |
| **Dusk Ball** | sv08-175 | H | Reveal bottom 7 → take a Pokémon |
| **Pokégear 3.0** | sv10.5b-084 | I | Top 7 → take a Supporter (consistency staple) |
| **Poké Pad** | me03-081 | J | Search non-rule-box Pokémon — single-prize tutor, important for Festival/Alakazam shells |

---

## Meta research workflow (do this before recommending a deck)

The meta drifts weekly. Memorized lists go stale. **Always re-validate with live tournament data** before finalizing a build or rating.

### Limitless TCG — primary source

| URL pattern | What you get |
|---|---|
| `limitlesstcg.com/decks` | Current archetype standings + meta share % |
| `limitlesstcg.com/decks/{archetype-id}` | Archetype overview, top finishers, variant breakdown |
| `play.limitlesstcg.com/decks/{archetype-name}?format=standard&rotation=2026&set=POR` | Best finishes by tournament + win rate, filtered to current rotation |
| `limitlesstcg.com/decks/list/jp/{id}` (JP) or `/decks/list/{id}` (intl) | Full 60-card decklist from a specific tournament |

### Workflow

1. **Pull 3+ recent winning lists** for the archetype (different tournaments, different players, ideally last 30–60 days). JP City League winners are best — Japan plays new sets first
2. **Identify the consistent core** — cards in all 3 lists with same/near-same counts = the actual engine
3. **Identify flex slots** — varying counts/choices across lists = tech room
4. **Use the most recent list as baseline** — older lists may carry outdated tech
5. **Compare audited deck vs winning lists card-by-card** — flag every divergence and articulate why your version is better, or default to the meta build

### Hard rules

- **A deck with no tournament wins gets a 4.5-star cap regardless of theoretical score** (see `pokemon-tcg/deck-evaluation-framework.md` for full validation cap table)
- **Theoretical 4.99 ≠ tournament-validated 4.95** — real-world results expose blind spots that scoring criteria miss (matchup math, hand disruption, opponent prep)
- If you can't find 3 winning lists for an archetype, treat it as untested rogue — not meta

### Other useful sources

| Source | When to use |
|---|---|
| Wargamer / pokemoncard.io | High-level archetype write-ups, post-rotation meta analysis |
| TCGplayer "Best Decks Right Now" articles | Monthly meta snapshots |
| pokemon.com strategy articles (e.g. Ellis Longhurst top 5) | Official-source card evaluations |
| pokescope.app blog | Set release deep-dives |

---

### How to verify legality quickly

```bash
curl -s --max-time 15 "https://api.tcgdex.net/v2/en/cards/{id}" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); \
  print(d['name'], '| reg:', d.get('regulationMark','?'), '| std:', d.get('legal',{}).get('standard'))"
```

**Standard 2026 = `regulationMark` in {H, I, J}.** Do not rely solely on `standard: true` — the API may lag on rotation updates. If reg mark is G, treat as rotated even if `standard: true`.
