# Release Notes for v0.19.5 (2026-08-10)

A fix and a big expansion of the long-press popups: they used to stop working after you changed views, and now they not only keep working everywhere but also cover climate and fan controls, not just lights and covers.

- **Long-press popups no longer break after navigating:** Previously, switching between views made the brightness and shade popups stop appearing until you reloaded the page. They now keep working on every view, no matter how you got there.
- **Control fans by holding:** Hold a fan tile or row for half a second and a speed slider pops up, pre-filled with the fan's current speed. Tap the fan icon to turn it off (and tap again to turn it back on at the last speed).
- **New climate popup:** Hold a thermostat tile or row and a popup shows the current room temperature with your target temperature right below it. Use the + and − buttons to nudge the setpoint in half-degree steps, and tap a mode button (Off, Heat, Cool, Auto, etc.) to switch the system. Only the modes your thermostat actually supports are shown.
- **Consistent everywhere:** The popups work on both tile cards and entity rows, and behave the same across all themes.

# Release Notes for v0.19.4 (2026-08-10)

A bug fix: the press-and-hold brightness and shade-position popups (shown by holding a light or cover tile) were never appearing, even though the feature was documented. LightDash was loading the scripts and styles for these popups, but the popup itself was missing from the package, so nothing was ever shown on screen.

- **Long-press dimmer popup now works:** Hold a light (or fan) tile or row for half a second and the brightness slider pops up, with the current brightness level, ready to drag.
- **Long-press cover popup now works:** Hold a cover tile or row and the position slider pops up with up/stop/down buttons, pre-filled with the cover's current position.
- **Nothing else changed** — the popups hide themselves when you press the ✕, and work the same way they always should have.

# Release Notes for v0.19.2 (2026-08-09)

A small quality-of-life change: you can now turn off the on/off toggle switches on an Entities card. LightDash adds a toggle to every light, switch, fan and input_boolean row so you can flip them on or off from the card. If you prefer a cleaner, read-only list — or just don't want a stray tap to turn something on — set `lightdash.show_toggle: false` on the card to hide all the toggles on it, or on a single row to hide just that one.

- **Hide toggle switches on Entities cards:** Add `lightdash: { show_toggle: false }` to any Entities card and every row's toggle switch disappears, and tapping a row no longer flips the entity either. The rows still show the entity's name, icon and current state.
- **Hide a single toggle:** Put `lightdash: { show_toggle: false }` on just one entity row (e.g. an always-on light you don't want to switch off by accident) while the rest of the card keeps its toggles.

# Release Notes for v0.18.1 (2026-06-28) — v0.19.1 (alarm panel)

A batch of layout fixes, preview improvements, and a new alarm control panel card: the fixed-grid view keeps cards from being squashed, weather cards show up in previews, a draggable divider lets you resize the config panes, and you can now arm and disarm your Alarmo security system directly from a LightDash dashboard.

- **New card type: `alarm-panel`:** Add `type: alarm-panel` with an `entity: alarm_control_panel.alarmo` to get a full-featured alarm control panel. Shows a state badge with colour-coded icon and status label, arm mode buttons (Away/Home/Night/Vacation/Custom), disarm button, an optional numeric keypad for code entry, and arming options (skip exit delay, bypass open sensors). Action buttons call Alarmo's `arm` and `disarm` services directly.
- **Diagnostic messages on the card:** When sensors trigger the alarm or are blocking an arm attempt, their names and states appear as pills directly on the card. If sensors were bypassed when arming, a persistent warning shows which ones are bypassed.
- **Customise appearance:** Use the `states` config key to hide arm mode buttons, rename button labels, override icons or state colours, and reorder buttons — same customisation as the original alarmo-card.
- **Fixed-grid uses absolute positioning:** When both `container_width` and `container_height` are set, cards in a fixed-grid view are placed with absolute positioning instead of CSS Grid. This means each card sizes naturally — no more cramped rows when a tile has inline controls like numeric input.
- **Weather cards render in the config preview:** The config preview now injects realistic dummy weather data so weather-forecast cards show their current conditions and 5-day forecast without a live Home Assistant connection.
- **Cleaner preview without HTMX errors:** The preview iframe no longer loads HTMX at all, eliminating the `Failed to construct 'URL'` browser console error.
- **Draggable editor/preview divider:** Drag the divider between the config editor and the preview pane left or right to give more space to whichever side you're working on.
- **Weather condition names fixed:** Conditions like `partlycloudy` now display as "Partly cloudy" instead of the raw Home Assistant state string.
- **Dimmer and cover popup crashes fixed:** JavaScript now safely checks for the modal element before attaching event listeners.
- **Fixed-grid cells fill their row height:** Cards now get an explicit `height` that matches their grid cell size.
- **Fridge config — today-card height tuned:** The agenda card now uses `height: 345` with its grid span reduced to 4 rows.
- **Alarm panel lives in real time:** The card now auto-updates when the alarm state changes externally — if someone arms the alarm from a keypad or the HA app, the card refreshes automatically via SSE.
- **Refined alarm panel design:** Larger centred state badge with a subtle coloured glow, a proper 3-column numpad (1-9 + 0/backspace/clear), dot indicators for entered codes, and rounded pill-shaped action buttons — all respecting your chosen theme's `--radius`, `--card-bg`, and `--control-bg` variables.

# Release Notes for v0.18.0 (2026-06-28)

The `fixed-grid` view type gives you pixel-perfect control over your dashboard layout. Instead of the auto-flowing section grid, you declare exactly how many rows and columns your view has, then place each card at a specific position by origin and span.

- **New view type: `type: fixed-grid`:** Define a grid at the view level with `grid.rows` and `grid.columns`, then position every card with `grid_layout` (`x`, `y`, `width`, `height`). Coordinates are 0-indexed from top-left — `x: 0, y: 0, width: 6, height: 2` means "starts in the top-left cell and spans 6 columns by 2 rows".
- **Works with or without a container height:** If you set `container_height`, rows distribute evenly within that space. Without it, the grid uses its own aspect-ratio to size itself — great for dashboards that should fit any display height.
- **Auto-place for loose cards:** Any card without a `grid_layout` is auto-placed into the next available cell by CSS Grid. No need to position every single card manually.
- **Consistent gap:** Cards in a fixed grid respect the same 8px gap as section-based views.

# Release Notes for v0.17.0 (2026-06-12)

Adds a compact agenda card that shows what's on your calendars today — and several data-fetching improvements that lay the groundwork for richer cards in future releases.

- **New card type: `custom:today-card`:** Shows a day-by-day agenda from one or more Home Assistant `calendar.*` entities. Each event is colour-coded by calendar (configured per-entity or auto-assigned), with visual states for current ("Now" pill), past (dimmed), future, all-day (hatched indicator), and multi-day events (with day count like "1/3").
- **Works offline or in preview mode:** If the addon can't reach Home Assistant, or if your calendar entities don't exist yet, the card renders with realistic dummy events so you can see exactly how it will look when live — no config changes needed.
- **Optional height control:** Add `height: 300` to fix the card height with scrolling for excess events. Defaults to auto-height when omitted.
- **Grid column fix for custom cards:** Custom cards like `custom:today-card` now correctly respect `grid_options.columns` from your YAML config, so they sit at the right width in multi-column grid sections.
- **Internal:** New calendar data cache with 5-minute TTL, `CalendarCache` and `get_events()` fetch module, and dummy data generator for reliable previews.

# Release Notes for v0.16.2 (2026-06-10)

One more stability fix for the config page.

- **Config page 500 error fixed:** The config page no longer crashes when you try to add or rename a dashboard. Two JavaScript regex patterns used bare `$` characters that conflicted with Python's `string.Template` parser, causing a server-side 500 error.

---

# Release Notes for v0.16.1 (2026-06-10)

Weather forecast cards are now powered by the Home Assistant WebSocket API, bringing live forecast data to your dashboards with automatic background refreshes and a handful of stability fixes.

- **Live weather forecast via WebSocket:** Weather-forecast cards now fetch forecast data directly from Home Assistant's `weather.get_forecasts` service using the WebSocket API, instead of relying on entity attributes. This means forecast data is always fresh and works with all weather integrations — no more empty forecast sections.
- **Lazy-loaded forecasts:** On page load, the current weather appears instantly while the forecast section loads in the background. No delay in seeing the current conditions.
- **Auto-refreshing forecast cards:** When the weather entity updates (e.g. new forecast data arrives), the card re-renders itself automatically. No page refresh needed.
- **30-minute forecast cache:** Forecast data is cached for 30 minutes so repeated page loads or multi-dashboard setups don't hammer the WebSocket API. Cache is invalidated automatically on weather entity state changes.
- **Smart fallback:** If the WebSocket call fails or the addon is offline, the card falls back to reading forecast data from the entity's `attributes.forecast` — existing dashboards keep working with no config changes.
- **Forecast polling loop fixed:** The weather forecast card no longer re-fetches forecast data in an infinite loop. On the initial page load, the forecast fetches once in the background, then stays stable until a weather state change triggers a refresh.
- **Long-press dimmer crash fixed:** Opening a dashboard with any light tile or light entity row no longer crashes the server with a `KeyError`. The dimmer popup now works as expected.
- **Cover popup crash fixed:** The long-press cover position modal no longer crashes with a `KeyError` when auto-close is enabled.
- **Full-page swap on state update fixed:** When an entity (like a cover) changes state, the live update no longer replaces the entire page body with just the state string (e.g. "open" or "opening").
- **Internal rendering engine refactored:** The HTML and JavaScript that makes up every page is now kept in separate template files instead of being built with inline Python string concatenation. You won't notice any difference as a user — response times are unchanged — but future development will be much faster and less error-prone.
- **Clock updates moved to a shared script:** The JavaScript that updates the clock on-screen is now loaded from a static file rather than inserted into every page, making pages slightly smaller and clock behaviour easier to tweak.

---

# Release Notes for v0.14.0 (2026-06-06)

Badges add compact context-aware controls to the top of any view — entity state at a glance, quick navigation, and conditional pills that appear and disappear based on what's happening in your home.

- **Entity badges:** Add `type: entity` badges to any view and see the entity icon, name, and live state in a compact pill. Tap a light, switch, or binary sensor badge to toggle it on or off — state updates arrive in real time.
- **Shortcut badges:** `type: shortcut` badges let you navigate to another view or open an external URL with a single tap. Perfect for quick links between dashboards or jumping to your Home Assistant frontend.
- **Entity-filter badges:** `type: entity-filter` badges only show when their conditions are met — for example, a "Roof open" badge that appears only when `cover.kitchen_roof` is in the `open` state. The badge re-evaluates via SSE so it appears and disappears dynamically.
- **Badges in example configs:** `living_room.yaml` now has entity badges for the porch and entryway lights plus a shortcut to "Other Rooms". `kitchen.yaml` has entity badges for kitchen lights and a filter badge for the roof.

---

# Release Notes for v0.13.4 (2026-06-06)

Favourite brightness shortcuts let you tap preset values in the dimmer and cover modals, so you don't always have to drag the slider.

- **Favourite values for light and cover:** You can now set `favourite_values` under `lightdash:` on any light tile, cover tile, or entity row — for example `[25, 50, 75, 100]`. Up to 4 values, each between 0 and 100. When you long-press to open the dimmer or cover modal, your presets appear as tap-able buttons on the left side. Tap one and the brightness or position is set immediately.
- **Browser JS syntax error fixed:** The generated JavaScript had a brace/paren ordering issue in the favourite-buttons code, causing `Uncaught SyntaxError: Unexpected token ')'` in the browser console and preventing the modals from working. Closing brackets are now in the correct order.

---

# Release Notes for v0.13.3 (2026-06-06)

Light and cover long-press modals now work with mouse clicks, making them testable on desktop browsers without touch emulation.

- **Mouse support for long-press modals:** The light dimmer and cover position modals now respond to `mousedown`/`mousemove`/`mouseup` events alongside the existing touch events. Hold-click on any light tile or cover tile to open the modal, then drag the slider with your mouse. This makes testing possible with browser automation tools like Playwright without enabling touch emulation.

---

# Release Notes for v0.13.2 (2026-06-06)

Clock auto-sizing gets more precise with percentage control and keeps text fitted as time ticks.

- **Fit-text with fine-tuning:** `clock_size: fit` and `date_fontsize: fit` now accept a percentage suffix like `"fit 75%"` — auto-sizes text to fill the card width, then scales down to the specified percentage. Perfect when full-width is too wide.
- **Text stays fitted as clock ticks:** The auto-sizing recalibrates every time the clock updates, so the time and date always fill the available width — even when the text length changes (e.g., seconds appearing).

---

# Release Notes for v0.13.1 (2026-06-06)

Clock cards are more flexible with resizable text and an optional date line.

- **Clock size control:** `clock_size` now accepts percentage strings like `"150%"` to scale the time text, or `"fit"` to auto-size text to fill the card width — alongside the existing `small`, `medium`, and `large`.
- **Date line on clock cards:** Set `date_show: true` under a `lightdash` subsection to show the current date below the time. Choose between `default` (long date), `iso` (YYYY-MM-DD), or `locale` (localised short date). The date has its own `date_fontsize` option, so the time and date can size independently.
- **Button cards for service calls:** The `button` card works without an `entity` field — perfect for triggering arbitrary HA services with `tap_action`, `target`, and `data`.

---

# Release Notes for v0.12.4 (2026-06-06)

Lots of new features have landed! Here's what's new:

- **Weather forecast card:** Add a `type: weather-forecast` card to any dashboard and see current conditions plus upcoming weather. Choose daily (shows weekday, icon, and high/low range), hourly (shows time, icon, and temperature), or twice-daily. You can pick what shows under the current temperature — high/low, precipitation, or humidity — and limit how many forecast items appear.
- **Forecast from a separate sensor:** Some weather integrations (like Pirate Weather) don't put forecast data in the entity itself. You can point `forecast_entity` at a template sensor that does have forecast data, while the main `entity` still drives current conditions.
- **Light dimmer on long-press:** Hold your finger on any light tile or light entity row and a brightness slider pops up. Drag up or down to set brightness — your finger lifts and it's sent to Home Assistant. Tap the light icon to switch on or off (turning back on remembers your last brightness).
- **Cover position on long-press:** Hold your finger on any cover tile or cover entity row and a position slider appears, alongside dedicated open, stop, and close buttons. Drag to any position, or tap the arrow buttons for full open or close.
- **Auto-revert to home screen:** Set `auto_revert_seconds` under the `lightdash:` section and your dashboard will automatically return to the first view after a period of inactivity — perfect for wall-mounted tablets that should always show the main screen.
- **Auto-close popups:** Set `auto_close_modal_seconds` and the dimmer and cover modals will dismiss themselves after a few seconds of inactivity, keeping your display clean.
- **Pick a theme:** Add `theme: name` under `lightdash:` to choose from 10 visual styles — `ha-dark`, `daylight`, `glass`, `hearth`, `ink`, `sage`, `soft`, `bauhaus`, `terminal`, or the base `style`. Everything changes together: colours, fonts, spacing, and control styles.
- **Hide entity icons:** Set `icon: none` on any entity row in an entities card and the icon disappears — the name and state shift left for a clean, compact, text-only look.
- **Accessibility improvements:** Weather condition names and cover control buttons now have proper `aria-label` attributes for screen readers.
