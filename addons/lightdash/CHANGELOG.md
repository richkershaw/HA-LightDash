# Changelog

## v0.19.5 (2026-08-10)
- **Fixed:** Long-press modals now keep working after navigating between views. View navigation is done with an htmx body swap, but the modal scripts only ran on the initial `DOMContentLoaded` and held stale element references, so after the first navigation the modal silently stopped appearing.
- **Changed:** `dimmer.js` and `cover.js` rewritten to use document-level event delegation with lazy element lookup. They wire up once and work on every view, and the scripts now render in the view body so htmx re-evaluates them on each swap (a window flag keeps them from wiring twice). `_view_needs_light_dimmer` generalized to `_view_needs_level_modal`.
- **Added:** Long-press support for **fan** entities — the same brightness-style modal now controls fan speed (`fan.set_percentage`), with an on/off toggle via the icon and a distinct fill colour.
- **Added:** Long-press **climate modal** (`climate_modal.html` + `climate.js`) — shows current vs target temperature with +/− buttons (`climate.set_temperature`) and HVAC mode buttons built from the entity's `hvac_modes` attribute (`climate.set_hvac_mode`).
- **Added:** `data-fan-entity` / `data-climate-entity` attributes on tiles and entity rows; `_view_needs_climate_modal` gating.
- **Changed:** Climate modal CSS and `dimmer-fade`/`dimmer-pop` keyframes added to the base `style.css` (previously only present in the `ha-dark` theme).

## v0.19.4 (2026-08-10)
- **Fixed:** Long-press dimmer and cover modals now actually display. The modal popups were never shown because the modal HTML markup (`dimmer_modal.html`, `cover_modal.html`) was missing from the repository, so the view only got the dimmer/cover JavaScript and CSS — which bailed out because the `#dimmer-modal` / `#cover-modal` elements it drives did not exist.
- **Added:** `app/templates/dimmer_modal.html` and `app/templates/cover_modal.html` — the long-press popups with their full set of elements the existing `dimmer.js` / `cover.js` scripts expect (track, fill, name, percentage, close button, and up/stop/down controls for covers). Hidden by default, shown on a half-second press-and-hold on a light, fan, or cover tile/row.

## v0.19.2 (2026-08-09)
- **Added:** `lightdash.show_toggle` option for `entities` cards — set `show_toggle: false` on the card to hide all row toggle switches, or on an individual row to hide just that toggle. When opted out, the row no longer responds to click-to-toggle either, and the toggle sync script (`st()`) is not injected when no toggles remain in a view.
- **Changed:** `_render_entities` gates both `_render_entity_toggle` and the row-level click-to-toggle `hx-*` attributes on the new `show_toggle` flag (card-level, overridable per-entity via the row's own `lightdash` block).
- **Changed:** `_view_needs_toggle_sync` now skips entities cards/rows that opt out via `show_toggle: false`.

## v0.19.1 (2026-06-28)
- **Changed:** Alarm panel CSS redesigned — uses theme CSS variables (`--radius`, `--radius-sm`, `--card-bg`, `--card-border`, `--control-bg`, `--control-border`, `--divider`, `--text-faint`, `--accent`) throughout. Centred header with large icon badge (64px) and soft state-colour glow via `drop-shadow` + `color-mix`. Keypad now 3-column classic numpad layout (1-9 + 0/backspace/clear). Action buttons use `--radius-sm` and `--control-border`.
- **Changed:** Alarm panel header simplified — removed `alarm-info` wrapper, state colour now injected as `--alarm-color` CSS custom property on `.alarm-card`, inherited by badge, state label, disarm button, dot indicators, and code input focus ring.
- **Changed:** Code display replaced with individual dot indicators (`.alarm-code-dots` → `.alarm-code-dot.filled`) instead of a single text span. Text password input hidden when keypad is shown.
- **Added:** Alarm state icons prefetched via `_prefetch_icons` — all state icons (shield-off, shield-home, shield-lock, shield-moon, shield-airplane, shield-check, bell-ring, shield-sync, shield-alert) and keypad icons (backspace-outline, close, alert) added to prefetch set.
- **Added:** SSE auto-refresh — wrapper `<div class="alarm-panel-wrap">` with `hx-get="/api/alarm-card/..." hx-trigger="sse:entity_{sanitized_eid}"` listens for entity state changes and fetches fresh card HTML. `GET /api/alarm-card/{dashboard}/{view_path:path}?entity=xx` endpoint re-renders card with fresh HA state.
- **Added:** Alarm panel card added to showcase Controls view with custom button labels.

## v0.19.0 (2026-06-28)
- **Added:** `alarm-panel` card type — full-featured alarm control panel for Alarmo integration. Displays state badge (icon+color+label per state), arm/disarm action buttons, numeric keypad for code entry, arming options (skip exit delay, bypass open sensors), and diagnostic messages (triggered sensors, blocking sensors, bypassed sensors).
- **Added:** `_render_alarm_panel` renderer function in `app/renderer.py` — registered as `alarm-panel` card type with state-aware rendering, configurable state labels/colors/button icons/button order via `states` config key.
- **Added:** `POST /api/alarm-action/{dashboard}/{view_path}` endpoint — accepts `entity_id`, `action` (arm mode or disarm), `code`, `skip_delay`, `force`; calls `alarmo.arm` / `alarmo.disarm` via REST; re-fetches entity state and returns re-rendered card HTML for HTMX swap.
- **Added:** `alarm_panel.js` template — client-side keypad digit entry, code display with dot masking, auto-clear after 120s inactivity, HTMX afterSwap re-initialization. Minimal ~35 lines of IIFE JS.
- **Added:** Alarm panel CSS — header badge, state label, action button grid, keypad grid, arming option checkboxes, sensor badge pills, diagnostic message banners with orange (warning) and blue (bypassed) theming.
- **Added:** `_view_needs_alarm_panel` helper — detects alarm-panel cards in views and injects `alarm_panel.js` template into `<head>`.
- **Added:** `_alarm_sensor_badges` and `_alarm_bypassed_badges` helpers — render sensor badge pills from entity `open_sensors` and `bypassed_sensors` attributes.

## v0.18.3 (2026-06-28)
- **Changed:** Fridge config — today-card gets explicit `height: 345` and grid height reduced from 5 to 4 rows (height fix now fills allocated space).

## v0.18.2 (2026-06-28)
- **Fixed:** Fixed-grid absolute-positioned cells now include `height` in their style — cards fill their allocated grid cell height instead of shrinkwrapping to content.

## v0.18.1 (2026-06-28)
- **Fixed:** Fixed-grid view uses absolute positioning when `container_width` + `container_height` are set — cards no longer force-squeeze into CSS Grid 1fr rows, letting tile content (numeric-input, etc.) size naturally.
- **Fixed:** Weather condition `partlycloudy` now displays as "Partly cloudy" instead of the raw HA state string — added `_CONDITION_DISPLAY` lookup map in `renderer.py`.
- **Fixed:** Weather forecast cards render forecast data in config preview mode — dummy entity states injected for weather entities absent from real HA connection.
- **Fixed:** Preview iframe (srcdoc) no longer spews HTMX `Failed to construct 'URL': Invalid URL` errors — HTMX scripts stripped from static preview HTML; `sse-connect`/`hx-ext` attributes also removed.
- **Fixed:** Null reference errors in dimmer and cover JS modals — added early `if(!m)return;` guards when modal elements are absent.
- **Fixed:** `closeBtn.addEventListener on null` error in dimmer/cover popup JS — guards added.
- **Fixed:** `max-width: none` on `.lv-view` when `container_width` is set — overrides CSS clamp that squeezed fixed-width containers.
- **Added:** Draggable divider between editor and preview panes in config screen — `grid-template-columns: 200px 1fr 8px 1fr` with mouse drag JS on divider element.
- **Added:** Preview viewport boundaries visually indicated — darker body background and dashed outline around `.lv-view` in config preview.
- **Added:** `numeric-input` feature support in entities card entity rows — when a dict entity has `features`, delegates to `_render_features` for inline controls.

## v0.18.0 (2026-06-28)
- **Added:** `fixed-grid` view type — declarative view-level row/column grid. View defines `grid.rows` and `grid.columns`. Each card specifies `grid_layout` with `x`, `y`, `width`, `height` (0-indexed from top-left). Cards without `grid_layout` auto-place. Supports `lightdash.container_height` for evenly-spaced rows or automatic aspect-ratio sizing.
- **Added:** `GridLayout` and `FixedGrid` dataclasses in `app/models.py`.
- **Added:** `_parse_fixed_grid_view` in `app/parser.py`.
- **Added:** `_render_fixed_grid` function in `app/renderer.py` — renders cards within a CSS Grid container with explicit `grid-column`/`grid-row` placement.
- **Added:** `.fixed-grid` CSS — `display: grid` with `repeat(var(--fg-cols), 1fr)`, 8px gap.

## v0.17.0 (2026-06-12)
- **Added:** `custom:today-card` card type — lightweight day-agenda card for `calendar.*` entities with past/current/future/all-day/multi-day event states, per-calendar colors, auto-palette fallback, configurable advance offset, time format, event limit, and `fallback_color`.
- **Added:** `app/calendar_events.py` — `CalendarCache` (TTL 300s), `get_events()` to fetch events from HA REST API, and `get_dummy_events()` for offline/preview fallback with realistic sample data.
- **Added:** `HAClient.get_calendar_events()` — calls `GET /api/calendars/{entity_id}` with start/end params.
- **Added:** Calendar data wiring in `main.py` — `CalendarCache` in lifespan, calendar entity discovery and fetch in `dashboard_view()`, dummy data injection when HA is offline or no real data exists.
- **Added:** `height` config option on `custom:today-card` — integer pixels (default 0 = auto). When set, card is fixed height with scrollable event list.
- **Added:** Showcase YAML — Agenda view with `custom:today-card`, badge shortcut to navigate to it.
- **Fixed:** `_map_today_card` now preserves `grid_options` from YAML config so the card respects grid column spans.
- **Fixed:** Preview mode (`_preview`) and config preview now generate dummy calendar data so the today-card renders events without a live HA connection.

## v0.16.2 (2026-06-10)
- **Fixed:** Config page 500 error — escaped bare `$` in JS regex `/^[a-zA-Z0-9_-]+$/` patterns within `config.html` `string.Template` to prevent `ValueError: Invalid placeholder`.

## v0.16.1 (2026-06-10)
- **Fixed:** `hx-trigger="load"` infinite polling on weather-forecast cards — `load` now only fires on the initial cold render. Once forecast data has been fetched via the HTMX endpoint, the returned card omits `load` from `hx-trigger`, breaking the request loop.

## v0.16.0 (2026-06-10)
- **Added:** `HAWebSocket` class in `sse_manager.py` — refactored the existing receive-only WS connection to support bidirectional request/response with message ID tracking and `asyncio.Future` resolution. Exposes `call_service(domain, service, data, *, return_response, target)`.
- **Added:** `app/weather.py` — `ForecastCache` with 30-min TTL and `get_forecast()` helper that reads from cache → WebSocket `call_service` → entity attributes fallback.
- **Added:** `GET /api/weather-forecast/{dashboard}/{view_path}` endpoint for HTMX lazy-loading weather-forecast cards via `hx-trigger="load"` and reactive refresh via `hx-trigger="sse:forecast_<entity>"`.
- **Added:** Background forecast refresh — when a weather entity state changes via the HA WebSocket, a background task fetches fresh forecast data (if cache is stale) and broadcasts an SSE event to trigger card re-renders.
- **Changed:** Weather-forecast card now accepts `forecast_data` via `_forecast_data` global, prioritized over `entity.attributes.forecast`. Card output includes HTMX lazy-load and SSE refresh attributes.
- **Fixed:** Template `$auto_close_resethideCover` parser error in `cover.js` — same `string.Template` delimiter fix as the dimmer template.

## v0.15.2 (2026-06-10)
- **Fixed:** Entity state SSE swaps no longer wipe the entire page body. Added `hx-target="this"` to entity state `<span>` elements so the htmx SSE extension targets the span itself instead of inheriting `hx-target="body"` from ancestor card containers.

## v0.15.1 (2026-06-10)
- **Fixed:** Template `$auto_close_resethideDimmer` parser error where `string.Template` merged the placeholder with adjacent text — added `{}` braces to delimit `$auto_close_reset` in `dimmer.js` template, fixing `KeyError` crash on views with light entities.

## v0.15.0 (2026-06-07)
- **Refactored:** Replaced all inline HTML/JS string concatenation in `renderer.py` and `main.py` with `string.Template` files loaded from `app/templates/`. Same zero-dependency runtime cost (`Template.substitute()` ≈ Python `+` concat), but the HTML/JS is now readable, editable, and maintainable in its own `.html` files instead of buried in Python string literals.
- **Extracted:** 7 HTML templates (`view.html`, `view_index.html`, `dashboard_index.html`, `dashboard_list.html`, `config.html`, `preview.html`, `error.html`) and 5 JS templates (`toggle_sync.js`, `slider_sync.js`, `dimmer.js`, `cover.js`, `auto_revert.js`) from inline code.
- **Added:** `app/constants.py` — shared `_SW_SCRIPT` constant, eliminating the identical duplicate between `renderer.py` and `main.py`.
- **Moved:** Clock JS (`uclk()`, interval, event listeners) from inline `render_view()` into `static/scripts.js` for reduced inline script size.

## v0.14.0 (2026-06-06)
- **Added:** Badges bar on views — three badge types: `entity` (icon+name+live state, tap toggles binary entities), `shortcut` (icon+label, navigate to view or open URL), and `entity-filter` (conditionally shown based on entity state, with static render-time evaluation)
- **Added:** Dynamic endpoint `GET /api/view/{dashboard}/{view_path}/badge/{idx}` for re-evaluating entity-filter badges on SSE trigger
- **Added:** Badge CSS base styles in `style.css` and colour overrides in all 10 theme files via CSS variables (`--control-bg`, `--control-text`, `--text-faint`)
- **Added:** 12 unit tests covering all badge types, edge cases (empty list, missing keys), and SSE trigger wiring
- **Added:** README section with YAML examples for all three badge types
- **Changed:** `_css_link()` now emits base `style.css` before theme CSS so theme overrides always apply
- **Changed:** Example configs (`living_room.yaml`, `kitchen.yaml`) populated with real badge configurations

## v0.13.4 (2026-06-06)
- **Added:** Favourite brightness/position shortcuts — configure up to 4 preset values per light or cover under `lightdash.favourite_values` (e.g. `[25, 50, 75, 100]`). Appears as tap-able buttons in the long-press dimmer/cover modal
- **Added:** 10 unit tests validating `favourite_values` parsing, max-4 truncation, bounds filtering, non-numeric rejection, and empty/missing key handling
- **Added:** README documentation with config examples and ASCII diagram for favourite values
- **Fixed:** JS syntax error in generated dimmer and cover modal code — closing brace/paren order was wrong, causing `Uncaught SyntaxError: Unexpected token ')'`

## v0.13.3 (2026-06-06)
- **Added:** Long-press modals (light dimmer and cover position) now respond to mouse events (`mousedown`/`mousemove`/`mouseup`) alongside the existing touch events — fully testable on desktop browsers

## v0.13.2 (2026-06-06)
- **Added:** `clock_size` and `date_fontsize` accept `"fit N%"` syntax — auto-size text to fill width then scale by percentage (e.g. `"fit 75%"`)
- **Added:** `icey_textFit()` re-triggers on every clock tick (`uclk`), so text re-fits when content length changes

## v0.13.1 (2026-06-06)
- **Added:** Clock `clock_size` now accepts `"fit"` (auto-size to fill width) and percentage strings like `"150%"` (merge of former separate `fontsize` parameter)
- **Added:** Clock date-line options (`date_show`, `date_format`, `date_fontsize`) are now nested under a `lightdash` sub-section to distinguish LightDash extensions from standard HA YAML
- **Added:** Automatic `scripts.js` inclusion and `icey_textFit()` initialisation when `clock_size: fit` or `lightdash.date_fontsize: fit` is used

## v0.12.4 (2026-06-06)
- **Fixed:** YAML editor inserted tab characters for indentation instead of spaces, causing parsing errors. Editor now uses 4-space indentation with `indentWithTabs: false`, and pasted content has tabs automatically converted to spaces.

## v0.12.2 (2026-06-06)
- **Fixed:** Broad `align-items: flex-start` replacement in v0.12.0 accidentally changed all CSS flex containers from `center` to `flex-start` — entities, tiles, glance, button, heading, dimmer, and clock cards all had their content top-aligned instead of centered. Reverted all to `center` except the intended `.weather-current` rule.

## v0.12.1 (2026-06-06)
- **Added:** `README.md` documentation for weather-forecast card, cover/light long-press modals, auto-revert and auto-close modal config options, theme support, and architecture notes

## v0.12.0 (2026-06-06)
- **Added:** `auto_revert_seconds` lightdash config option — automatically returns to the first dashboard view after a period of inactivity
- **Added:** `auto_close_modal_seconds` lightdash config option — automatically closes popup modals (dimmer and cover) after a period of inactivity
- **Added:** Long-press cover modal — long-press any cover tile or entity row to open a position slider with open/stop/close buttons alongside
- **Added:** `data-cover-entity` attribute on cover tile cards and entity rows for long-press targeting
- **Added:** `_view_needs_cover_modal()` helper for conditional cover modal injection
- **Added:** Cover modal CSS across all 10 theme files
- **Changed:** Dimmer modal now also respects `auto_close_modal_seconds` — resets the auto-close timer on slider drag, close button, and backdrop tap
- **Changed:** Cover inline control buttons (`cover-btn`) class no longer conflicts with modal buttons — test assertion tightened

## v0.11.0 (2026-06-05)
- **Added:** `weather-forecast` card type — displays current weather conditions (condition icon, temperature, extrema/precipitation/humidity) and forecast list (daily/hourly/twice_daily) from any HA `weather` entity
- **Added:** `forecast_count` config option — limits how many forecast items appear (default 5 daily / 12 hourly)
- **Added:** `round_temperature` config option — rounds all displayed temperatures to integers
- **Added:** `secondary_info_attribute` config option — controls what shows under the current temp (extrema / precipitation / humidity)
- **Added:** Views containing a weather card auto-refresh every 30 minutes via `<meta http-equiv="refresh">` to pick up updated forecast data
- **Added:** Weather condition icon mapping (15 HA condition strings → MDI icons) across all 10 theme CSS files
- **Added:** `_view_needs_weather_refresh()` helper for conditional meta refresh injection
- **Changed:** Version bump to 0.11.0 (minor feature release)

## v0.10.17 (2026-06-04)
- **Added:** `icon: none` support on entity items in entities cards — hides the icon, name/state align left naturally (no -offset needed)
- **Added:** `.entity-row.no-icon` CSS class across all 10 theme files for theme-level styling hooks

## v0.10.16 (2026-06-04)
- **Added:** Long-press dimmer modal on light entity tiles and entity rows — vertical brightness slider, icon tap toggles on/off, shows entity name and current brightness percent
- **Added:** CSS theme system — new `lightdash.theme` key in dashboard YAML selects a theme CSS file (default `ha-dark`); themes are drop-in replacements sharing identical class structure
- **Added:** 9 built-in themes: ha-dark, daylight, glass, hearth, ink, sage, soft, bauhaus, terminal
- **Changed:** `render_view_index()` signature updated to accept `Dashboard` object for theme-aware rendering
- **Changed:** Default CSS file is now `ha-dark.css` (was `style.css`)
- **Changed:** Dimmer modal — on/off button removed, icon click toggles instead (reduces modal height)
- **Changed:** Dimmer modal — spacing tightened (12px padding, 10px gap), track widened to 88px
- **Fixed:** `_url()` HTML escaping in dimmer JS — Python string concatenation no longer produces raw `_url(` literal in output
- **Fixed:** Dimmer JS runs inside `DOMContentLoaded` to avoid null element references from head-early execution

## v0.10.15 (2026-06-03)
- **Added:** Global exception handlers – `sys.excepthook` and asyncio loop exception handler (log at CRITICAL, catches crashes that would otherwise go silent)
- **Added:** Signal handlers for SIGTERM/SIGINT/SIGHUP — log signal receipt at WARNING
- **Changed:** Heartbeat first interval decreased from 300s to 60s for early memory capture

## v0.10.14 (2026-06-03)
- **Fixed:** OOM crash from unbounded SSE queues — each client queue capped at 256 messages, slow/disconnected clients dropped automatically
- **Added:** Periodic heartbeat log (every 5 min) with RSS, uptime, and SSE client count to detect memory growth before OOM

## v0.10.13 (2026-06-03)
- **Changed:** `RELEASE.md` consolidated — single section per release, no per-commit-version grouping; user-facing only

## v0.10.12 (2026-06-03)
- **Added:** Configurable error diagnostics toggle ("Send error logs back to developer for diagnostics") — addon config checkbox, defaults to off
- **Changed:** Sentry SDK init moved into `lifespan` so it reads configuration before activating
- **Added:** Translations entry for `diagnostics` config key

## v0.10.11 (2026-06-03)
- **Added:** Configurable log level via addon config dropdown (`log_level` — `DEBUG|INFO|WARNING|ERROR`, default `WARNING`)
- **Fixed:** Timestamp format now consistently applied to all loggers including uvicorn's own output
- **Fixed:** `app.sse_manager` no longer pinned to INFO — respects root log level

## v0.10.10 (2026-06-03)
- **Added:** `RELEASE.md` — user-friendly summary of changes since last release for populating release notes
- **Changed:** `AGENTS.md` updated to require `RELEASE.md` maintenance with each version bump

## v0.10.9 (2026-06-03)
- **Added:** Timestamps to all console log output — lines now prefixed with `2026-06-03 12:34:56` for easier chrono-debugging

## v0.10.8 (2026-06-03)
- **Fixed:** App crash/stop with no error in logs — removed uvicorn `--reload` flag (was silently restarting when Python wrote `__pycache__` files)
- **Fixed:** WebSocket events silently stop syncing — background listener now restarts on any unexpected exit
- **Added:** Process-exit logging and shutdown lifecycle logs to distinguish graceful shutdown from hard kill
- **Changed:** Max WebSocket reconnect delay reduced from 120s to 20s — faster recovery after network blips
- **Changed:** Health check grace period increased (20s start, 5 retries) for slower HA hardware

## v0.10.5 – v0.10.7 (2026-06-03)
- **Added:** Sentry error tracking — unhandled exceptions and crashes now capture stack traces automatically for both local dev and addon deployments

## v0.10.4 (2026-05-31)
- **Fixed:** External state changes (HA toggles) not updating the UI — SSE
  extension's `swap()` was silently a no-op because the entity-state span
  inherited `hx-swap="none"` from its parent `.entity-row` (needed for toggle
  actions). Fixed by always setting `hx-swap="innerHTML"` on every entity-state
  span, overriding ancestor inheritance.

## v0.10.3 (2026-05-31)
- **Fixed:** External state changes (e.g. toggling a light from HA directly) not
  reflected in frontend — `htmx:sseMessage` handler was reading
  `e.detail.elt` (always `undefined` because the detail is a raw SSE
  `MessageEvent`, not an HTMX event with an `elt` property). Changed to
  `e.target`, which is the element the event was dispatched on (the entity-state
  span).
- **Fixed:** `st()` moved before the guard in `htmx:sseMessage` handler so
  toggle sync runs even if the event target isn't an entity-state span.
- **Fixed:** Same `e.detail.elt` → `e.target` fix in the slider sync
  `htmx:sseMessage` handler (`ss()` function).

## v0.10.2 (2026-05-31)
- **Fixed:** Tile cards with `hide_state: true` (e.g. Porch, Entryway) showing no
  visual state change when toggled — always render hidden entity-state span for
  binary entities so SSE events have a DOM target for icon recoloring.
- **Fixed:** Click handler no longer returns early when toggle switch is absent
  (guard relaxed from `if(!t||!s)return` to `if(!s)return`).
- **Fixed:** `st()` function now toggles `entity-on`/`entity-off` classes even
  when no toggle switch is present, via `if(s)` guard.

## v0.10.1 (2026-05-31)
- **Fixed:** Clock function renamed from `uc()` to `uclk()` to avoid overwriting
  the icon color interpolation function `uc(s)` at global scope.

## v0.10.0 (2026-05-31)
- **Added:** Icon color interpolation — entity card icons now show an amber glow
  when on and dim grey when off, with smooth brightness-aware transitions.
- **Added:** `_icon_color_for_state()` server-side helper and `uc(s)` client-side
  function for real-time color updates via SSE.

## v0.9.2 (2026-05-31)
- **Added:** Diagnostic startup logs in `main.py` and `sse_manager.py`.
- **Changed:** SSE notify log promoted from DEBUG to INFO for operational
  observability.
- **Changed:** File-watcher poll interval increased from 2s to 10s.

## v0.9.1 (2026-05-31)
- **Fixed:** Toggle switches not syncing with entity state on initial page load
  after inline rendering change — `st()` now also runs on `DOMContentLoaded`.

## v0.9.0 (2026-05-31)
- **Optimization:** Removed `pydantic` and `python-dotenv` dependencies — smaller
  container, faster pip install, less memory at runtime.
- **Optimization:** Entity state values now rendered inline during page generation
  instead of 1 HTTP request per entity on page load — eliminates N round-trips
  per dashboard render.
- **Optimization:** Icon SVG cache capped at 200 entries — prevents unbounded
  memory growth across many dashboards.
- **Optimization:** Dashboard file watcher reduced from 2s to 10s polling —
  fewer filesystem hits on SD card storage.
- **Resilience:** HA WebSocket reconnection uses exponential backoff (5s → 120s)
  with random jitter — avoids thundering-herd on supervisor recovery.
- **Resilience:** HA WebSocket auth failures stop retrying instead of spinning
  forever against a hopeless connection.
- **Resilience:** Health endpoint now exposes WebSocket status and active SSE
  client count for easier monitoring.

## v0.8.1 (2026-05-29)
- **Fixed:** Clock cards displaying `--:--` after switching views — the update
  function now runs on every HTMX content swap, not just on page load.

## v0.8.0 (2026-05-29)
- **Experiment:** Tested moving inline HTML/JS into Jinja2 templates, but found it was
  far too slow for lower-CPU Home Assistant devices like the HA Yellow, and reverted to
  the less-clean but much higher performing approach retained, albeit with some flow improvements.

## v0.7.2 (2026-05-29)
- **Optimistic toggle updates** — switches now flip instantly when clicked, no
  waiting for confirmation from Home Assistant. The server confirms silently in
  the background and corrects if needed.
- **Loading pulse animation** — tiles, toggles, sliders, and buttons glow with a
  subtle blue pulse while the command is being sent to Home Assistant if the request takes 
  more than a second or so. Provides visual feedback during the round-trip.

## v0.7.1 (2026-05-29)
- **Fixed:** Inline feature layout for number entities — the up/value/down
  controls now sit flush to the right of the tile name as intended, rather than
  floating in the middle with extra padding.

## v0.7.0 (2026-05-29)
- **Fixed:** Dashboard file watching during startup (the `watch_task` coroutine
  was referenced but never created, preventing clean shutdown).
- **Fixed:** Route handlers no longer crash when escaping HTML output.
- **Added:** `markupsafe` to dependencies.
