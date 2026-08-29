# sage_mcp_fastapi

FastMCP server wrapping the SAGE Connect promo-products API. Deployed on
Railway (`https://sagemcp-production.up.railway.app`); pushes to `main`
auto-deploy. Verify with `GET /health` and a live `tools/call` after deploys.

## Commands

- Tests: `uv run pytest -m "not integration"` (integration tests need
  `SAGE_ACCT_ID`/`SAGE_AUTH_KEY` env vars)
- Types: `uv run pyright` (strict; keep at 0 errors)
- Lint: `uv run ruff check src tests`
- Local server: `uv run --env-file .env uvicorn sage_mcp.server:app`

## Hard-won constraints — do not relearn these live

The SAGE API diverges from its own docs (PDFs in
`../sage-connect-remote-mcp/examples/`). The divergences are encoded in
`src/sage_mcp/types/` and `tests/conftest.py` — **fixtures mirror the real
wire format; never "simplify" them back to the documented one.** Highlights:

- Search pagination is `maxRecs`/`startNum`/`maxTotalItems` (default 1000 ≈
  1MB — always cap). `limit`/`pageSize`/`orderBy` don't exist upstream.
- Extra return fields come back UPPERCASE except `suppID`/`line`.
- Errors: lowercase `errNum`/`errMsg`, sometimes numeric strings, HTTP 200.
- Service 107 productId = 9-digit prodEId minus its 2-digit prefix; some
  records emit malformed JSON (see `_parse_response_json` + tool isolation).
- Service 105 detail already embeds live inventory.
- **Optional numerics arrive as `""` when SAGE has no figure** — a bare `int`
  raises `int_parsing` and one blank kills the whole response (cost this a
  live outage 2026-08-28). Never declare a new SAGE int as bare `int`: use
  `BlankAsNone` (measured values — `None` = no figure, `0` = known-empty,
  never collapse them) or `BlankAsZero`/`BlankAsOne` (flags/ids). Required
  ids stay bare `int`. See the `types/responses.py` module docstring.

## Consumers

`docs/CONSUMER_NOTICE_2026-08-28_blank_numerics.md` is the hand-off written for
agents/apps that call this server — what the `onHand: null` contract change
means and what to check on their side. Hand it over when someone asks why a
SAGE field changed shape. Known consumers: the KB's sourcing grid + presentation
cost resolution (`dgw_knowledgebase/app/lib/sage.ts`), `check_price`,
`check_inventory`, product_source's grid search.

## Compatibility

`search_products` keeps deprecated `page_size`/`page_number` aliases —
product_source's grid search sends `page_size: 250`. Don't remove them
without checking consumers. Cap is 250/page.

The repo `.env` SAGE credentials are stale (10008); Railway holds working
ones. For live checks, hit the deployed `/mcp` endpoint instead.
