# SAGE MCP server — behavior change, 2026-08-28

**Deployed and live** at `https://sagemcp-production.up.railway.app/mcp`
(commits `2af7735`, `dccb857`). No action required from you unless you read
`onHand` — see "Do I need to change anything?" at the bottom.

**Reconnect your MCP client** to pick this up cleanly.

---

## What was broken

SAGE sends `""` (empty string) on optional numeric fields to mean "we have no
figure." The server declared those as plain `int`, so Pydantic tried to parse
the empty string and raised — and because the failure happened at the response
level, **one blank field killed the entire response**, pricing included.

`get_product_detail` returned this instead of a product:

```
1 validation error for ProductDetailResponse
product.onHand
  Input should be a valid integer, unable to parse string as an integer
  [type=int_parsing, input_value='', input_type=str]
```

This was not rare and not cosmetic. Any supplier that publishes pricing but no
stock figure hit it. Two confirmed live: prodEId `325484683` (Bath Promotions
candle) and `796511591` (Vivid Giftworks reed diffuser) — both publish six full
pricing tiers with net cost, and both returned nothing but the error above.

**The dangerous part was downstream.** A total parse failure is
indistinguishable from "this supplier publishes no net cost." In the KB, the
error was caught, degraded to zero price breaks, and the item was marked
`needs_cost` — so a rep saw "No cost found, enter one below" and hand-typed a
price the API had published all along. If your agent has any
`try/catch → treat as no data` path around a SAGE call, assume it was silently
doing the same thing.

## What changed

Every integer field in the response models was audited. Blank values now
normalize instead of raising:

| Field kind | Behavior on `""` | Examples |
|---|---|---|
| Measured values | → `null` | `onHand`, `onOrder`, `refreshLeadDays`, `warehouseId`, `sageNum`, search-hit `suppId` |
| Flags and ids | → their default (`0`, or `1` for `active`) | `hasLogo`, `suppId`, `totalFound`, `verified`, `discontinued`, `active` |
| Required identifiers | still raise | `prodEId`, category `id` |

Garbage still fails. Only whitespace-only strings normalize — `"abc"` raises a
validation error exactly as before. This is not a general "coerce anything"
escape hatch.

## The one contract change that affects you

**`onHand` and `onOrder` can now be `null`.** They were previously typed `int`.
This applies to `get_product_detail` (`product.onHand`, and per-variant
`product.skus[].onHand` / `.onOrder`) and to `check_inventory`
(`products[].onHand`).

Note the server publishes no `outputSchema`, so you won't see this in
`tools/list` — you'll meet it at runtime in the JSON.

### `null` is not zero. This distinction is the entire point.

- `onHand: null` → **SAGE published no figure. Stock is UNKNOWN.**
- `onHand: 0` → **SAGE published a figure and it is zero. Genuinely out of stock.**

Collapsing these is how "we don't know" becomes a false "it's out of stock" —
which is a claim you'd be making to a client on DGW's behalf. Do not write
`onHand || 0`, `onHand ?? 0`, or `int(onHand or 0)`. Do not derive "unlimited
stock" (`onHand >= 999999999`) from a `null`; absence of a figure is not a
claim of unlimited stock.

**Say "stock not published by this supplier," never "out of stock," when it's
`null`.**

### Real payloads, live today

A product with stock — unchanged from before:

```json
{ "prodEId": 105917761, "onHand": 45247,
  "skus": [ { "onHand": 3783, "onOrder": 0 }, ... ] }
```

A product without a published figure — this used to be a hard error:

```json
{ "prodEId": 325484683, "spc": "QGFVB-QRXHQ",
  "prName": "14 oz. Black Luxury Candle with Gift Box - Engraved",
  "onHand": null, "skus": [],
  "qty": ["50","100","250","500","1000","2500"],
  "prc": ["36.00","34.00","33.75","33.50","33.25","33.00"],
  "net": ["21.60","20.40","20.25","20.10","19.95","19.80"] }
```

Pricing was always there. The server was losing it.

`check_inventory` on that same product gives you a second, independent signal —
`ok: false` means this supplier doesn't feed inventory at all:

```json
{ "ok": false, "products": [ { "prodEId": 325484683, "ok": false,
    "onHand": null, "skus": [], "lastUpdated": "" } ] }
```

## Do I need to change anything?

**If you don't read `onHand`:** no. Pricing, search, categories, and images are
unchanged — you just stop getting spurious errors on affected products.

**If you read `onHand`:** check three things.

1. **Null-coalescing to zero.** Any `?? 0` / `|| 0` / `or 0` on a stock value
   now converts "unknown" into a false out-of-stock claim. Handle `null` as its
   own case.
2. **Arithmetic and comparisons.** `onHand > 500` is `false` for `null` in JS
   and raises `TypeError` in Python. Guard before comparing.
3. **User-facing copy.** If a template renders stock, make sure `null` produces
   "stock not published" rather than "0 in stock."

**If your agent caches SAGE detail responses:** consider invalidating. Anything
cached as a failure for an affected product is wrong now — the data is
available.

## Related

`dgw_agents` already carries this same fix in its own direct SAGE client
(`src/dgw_agents/capabilities/sage.py`, fixed 2026-08-27) — that's where this
pattern was ported from. If you're in that repo, you already have it; the two
implementations are kept in sync **by hand, not by a shared package**, so if
you change SAGE models in either repo, check the other.

Verified before writing this: 141 unit tests pass, pyright strict clean, and
both repro prodEIds return all six pricing tiers through the deployed server.
