LightDash
=========

A lightweight, self-contained dashboard renderer for Home Assistant. Instead of running HA's full Lovelace frontend, which is a struggle for low-power devices such as NSPanels and older Android tablets, LightDash is a focused alternative: support for tiles and built-in entities, intelligent mapping of some common custom cards to lightweight alternatives, and plain HTML + CSS with much of the interactivity shifted to the addon itself.

I orignally built LightDash to run on the NSPanel Pro in-wall touchscreens I have around my house, which are getting increasingly slow as the HA team add more dashboard capabilities. Wonderful for iPads, desktop browsing and recent smartphones, but almost unusable on the devices that sit in the gap between ESPHome and modern browsers.

LightDash is designed to handle copy-and-pasted YAML from existing dashboards with _minimal_ (not quite zero) adjustment - there's an edit-and-preview web UI accessible from the addon control panel, where you can tweak the YAML and see the results immediately before saving.

**Caveat 1:** I've focused on the cards I use in my own small-screen dashboards. I'd love for contributors to add support for their own layouts!

**Caveat 2:** Yep, I used OpenCode to build a lot of this. I'm a 25+ year software architect and developer, but this started as a one-day project. I'm pretty happy it's not filled with slop - I've reviewed it and it's passable - but I make no warranties about code quality this early in its life.

![LightDash](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-lightdash.png)

Installation
------------

### Add the Repository

1. Go to **Settings → Apps → Install app**
2. Click the **⋮** menu (top-right) and select **Repositories**
3. Paste `https://github.com/richkershaw/HA-LightDash`
4. Click **Add**

### Install LightDash

1. The **LightDash** add-on appears in the store
2. Click **Install** and wait for the download to complete
3. Go to the **Info** tab and click **Start**
4. Toggle **Show in sidebar** to add the LightDash item
4. Go to **LightDash** in the sidebar to start setting up dashboards

**No manual configuration needed.** Dashboards are managed through the
in-app editor (see [In-App Editor](#in-app-editor) below).


Accessing Dashboards
--------------------

LightDash serves dashboards via two methods. Both work simultaneously.

### Via the HA Sidebar (Ingress)

After starting the add-on, click the **Open Web UI** button or the LightDash sidebar entry. This opens
the dashboard index page within the HA interface. This is fine for devices you're happy to login on regularly.

### Via Direct Port (HTTP, No Auth)

The add-on also exposes a raw HTTP port (`8001` by default). Any device on
your LAN can reach it without Home Assistant authentication:

    http://[your HA server]]:8001/

This is useful for:
- **Wall-mounted tablets** that shouldn't show a login screen
- **Guest devices** that shouldn't have HA credentials
- **kiosk-mode browsers** or screens that auto-launch a URL

The hostname defaults to your HA instance's hostname (auto-detected from the
Supervisor API). You can override it in the add-on Configuration tab:

| Option          | Default                 | Description                                    |
|-----------------|-------------------------|------------------------------------------------|
| `public_host`   | auto-detected           | Hostname for direct-port URLs                  |
| `public_port`   | `8001`                  | Port mapped to `8000/tcp` inside the container |

**Security note:** The direct port has no authentication. Anyone on the
network can view dashboards. Use firewall rules or a reverse proxy if you
need to restrict access. Disable the port mapping in the add-on Info tab
(change `8000/tcp: 8001` to `8000/tcp: null`) if you only want ingress access.

### Dashboard URLs

Each dashboard is available at:

    {base}/d/{name}

Where `{base}` depends on the access method:

- **Ingress:** `https://[your HA server]/api/hassio_ingress/{token}/d/{dashboard name}`
- **Direct port:** `http://[your HA server]:8001/d/{dashboard name}`

The exact URLs are logged in the add-on logs at startup and listed at the
`/dashboards` endpoint. Use the **Public URL** button in the config editor
to copy the external URL for the current dashboard.


In-App Editor
-------------

Dashboards are managed entirely through the in-app editor.

1. Open the LightDash sidebar entry (or navigate to the dashboard index)
2. Click **⚙ Config** at the bottom of the page
3. Click **+ Add Dashboard** and enter a URL-safe name (e.g. `living-room`)
4. Edit the YAML in the left pane
5. Click **Save** — the preview pane updates automatically
6. Click **Preview** to refresh the preview without saving
7. Click **Public URL** to copy the externally-available URL to add to your kiosk devices' config

The config page shows a split view:

```
┌──────────────────────────────────────────────────────────┐
│  Dashboard list         CodeMirror YAML    Preview       │
│                         editor             (iframe)      │
│  living-room ──active── ┌─────────────────┐              │
│  kitchen                │ views:          │   [rendered  │
│                         │   - title: Home │    view]     │
│  [+ Add Dashboard]      │     path: home  │              │
│  [Delete]               │     sections:...│              │
│                         └─────────────────┘              │
│                         [Preview] [Save]                 │
└──────────────────────────────────────────────────────────┘
```

- **Add Dashboard**: Creates a new YAML file with a starter template
- **Delete**: Removes the dashboard file entirely
- **Rename**: Renames the dashboard (and its YAML file on disk)
- **Save**: Writes YAML to disk and reloads the dashboard
- **Preview**: Renders the current editor content in the right pane
- **Public URL**: Copies the external dashboard URL to the clipboard

Dashboards are stored as individual YAML files in the add-on data directory
(`/data/dashboards/`), which is included in HA snapshots.


YAML Dashboard Format
---------------------

A dashboard is a YAML file with a top-level `views` key:

```yaml
title: Living Room
lightdash:
  container_width: 480px
  container_height: 480px
views:
  - title: Home
    path: home
    icon: mdi:home
    bg_image: /api/image/serve/abc123/original
    type: sections
    max_columns: 4
    sections:
      - type: grid
        cards:
          - type: tile
            entity: light.porch
            features:
              - type: light-brightness
            features_position: inline
```

**Top-level fields:**

| Field       | Description                                        |
|-------------|----------------------------------------------------|
| `title`     | Display title                                      |
| `lightdash` | Container sizing (see below)                       |
| `views`     | List of views                                      |

### lightdash config

Container sizing, visual theme, and auto-timeout behaviours.

```yaml
lightdash:
  container_width: 480px           # fixed container width (e.g. 480px, 100%)
  container_height: 480px          # fixed container height
  theme: ha-dark                   # visual theme: ha-dark, daylight, glass, hearth,
                                   #   ink, sage, soft, bauhaus, terminal
  auto_revert_seconds: 120         # auto-return to first view after inactivity
                                   #   (0=disabled, wall-mounted tablet friendly)
  auto_close_modal_seconds: 15     # auto-close popup modals after inactivity
                                   #   (0=disabled)
```

![Themes](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/readme-themes.png)

### View fields

| Field         | Description                                        |
|---------------|----------------------------------------------------|
| `title`       | Display title (also used in `<title>`)             |
| `path`        | URL path segment (defaults to slug of title)       |
| `icon`        | MDI icon (shown in view index)                     |
| `bg_color`    | CSS background-color                               |
| `bg_image`    | Background image URL (`/api/image/serve/...`)      |
| `type`        | View layout type (`sections`, `custom:layout-card`, or `fixed-grid`) |
| `max_columns` | Column count for max-width grid                    |

When `type: custom:layout-card` is used, the parser groups cards into grid
sections split by `custom:layout-break` card entries. The `layout.max_cols`
value determines section column count.

### Fixed-grid view type

Use `type: fixed-grid` for a view-level row-and-column grid where each card
has explicit position and size. The view defines the grid dimensions, and
each card specifies its origin and span.

```yaml
views:
  - type: fixed-grid
    title: My Grid
    grid:
      rows: 6
      columns: 12
    cards:
      - type: tile
        entity: light.living_room
        grid_layout:
          x: 0
          y: 0
          width: 6
          height: 2
      - type: tile
        entity: light.bedroom
        grid_layout:
          x: 6
          y: 0
          width: 6
          height: 2
```

| Field            | Description                                   |
|------------------|-----------------------------------------------|
| `grid.rows`      | Number of rows in the grid                    |
| `grid.columns`   | Number of columns in the grid                 |
| `grid_layout.x`  | Column origin (0-indexed, top-left)           |
| `grid_layout.y`  | Row origin (0-indexed, top-left)              |
| `grid_layout.width`  | Number of columns to span                 |
| `grid_layout.height` | Number of rows to span                   |

Cards without a `grid_layout` are auto-placed by CSS Grid into the next
available cell.

When `lightdash.container_height` is set, rows distribute evenly within that
height. Without it, the grid auto-sizes via `aspect-ratio` based on your
column/row counts.

### Section fields

| Field     | Description                          |
|-----------|--------------------------------------|
| `type`    | Section type (`grid`)                |
| `columns` | Number of grid columns               |

### Grid options on cards

```yaml
grid_options:
  columns: 6      # span this many columns
  rows: auto      # span this many rows
```


Supported Card Types
--------------------

### tile

A rich card showing entity icon, name, state, and optional controls.

```yaml
type: tile
entity: light.living_room
name: Living Room
icon: mdi:lamp
color: yellow              # tint icon (yellow/orange/red/pink/purple/blue/green/teal)
vertical: true             # stack icon above info
hide_state: true           # hide entity state & toggle
features_position: inline   # or "bottom" (default)
features:
  - type: light-brightness
  - type: light-color-temp
  - type: numeric-input
```

Features:

| Feature            | Description                                     |
|--------------------|-------------------------------------------------|
| `light-brightness` | Range slider (0–100%), posts `light.turn_on`    |
| `light-color-temp` | Range slider (153–500 mired), posts `light.turn_on` |
| `numeric-input`    | Decrement/increment buttons, posts `input_number.decrement/increment` |

Binary-domain entities (`light`, `switch`, `fan`, `input_boolean`) get a
toggle switch. Non-binary entities show state text. Cover entities show
open/stop/close buttons instead of a toggle.

Light entities support a **long-press dimmer modal** — a vertical brightness
slider with tap-to-toggle, auto-closes after inactivity (see
[Long-Press Modals](#long-press-modals) below).

Cover entities support a **long-press position modal** — a vertical position
slider with open/stop/close buttons (see
[Long-Press Modals](#long-press-modals) below).

Both light and cover tiles accept a `lightdash.favourite_values` list to add
shortcut buttons to their long-press modal (see
[Favourite Values](#favourite-values) below).

```yaml
type: tile
entity: light.living_room
lightdash:
  favourite_values: [25, 50, 75, 100]
```

### entities

A grouped list of entity rows, each with icon, name, state, and controls.

```yaml
type: entities
title: Lights
entities:
  - entity: light.dining_room
  - entity: light.kitchen
    name: Kitchen
    icon: mdi:counter
  - entity: cover.kitchen_roof
    icon: mdi:window-closed
  - type: divider           # horizontal rule
  - type: section           # section header
    name: Other
```

Cover entities automatically get open/stop/close buttons.
Binary non-cover entities get a toggle switch.

To remove the toggles (and click-to-toggle) from an entities card, set
`lightdash.show_toggle` to `false` on the card or on an individual row:

```yaml
type: entities
entities:
  - entity: light.kitchen
    lightdash:
      show_toggle: false
```

Light and cover entity rows also accept `lightdash.favourite_values` for
shortcut buttons in the long-press modal:

```yaml
type: entities
entities:
  - entity: light.kitchen
    lightdash:
      favourite_values: [25, 50, 75, 100]
```

### button

A compact action button. Icon and name are on one line. Does **not** require an
`entity` — ideal for triggering HA services directly.

```yaml
type: button
name: Other Rooms
icon: mdi:arrow-right-bold
tap_action:
  action: navigate
  navigation_path: other-rooms
```

Call any HA service with `target` and `data`:

```yaml
type: button
icon: mdi:air-filter
name: ""
tap_action:
  action: call-service
  service: cover.set_cover_position
  target:
    entity_id:
      - cover.velux_window_roof_window
  data:
    position: 7
```

### glance

A grid of entity icons with names and state, organised in columns.

```yaml
type: glance
title: Sensors
columns: 3
entities:
  - sensor.temperature
  - entity: sensor.humidity
    icon: mdi:water-percent
    tap_action:
      action: toggle
```

### entity

A single-row entity card.

```yaml
type: entity
entity: sensor.temperature
name: Temp
icon: mdi:thermometer
```

### heading

```yaml
type: heading
heading: Living Room
icon: mdi:sofa
```

### markdown

Simple markdown rendering with bold, italic, code, links, lists, and headers.
**HA Jinja2 template syntax (`{{`, `{%`) is not supported.** Use a `clock`
card for time display instead.

```yaml
type: markdown
content: |
  # Hello
  **bold** and *italic*
```

### clock

Digital clock card with timezone and format support. Updates every 30 seconds
via JS `Intl.DateTimeFormat`.

```yaml
type: clock
time_zone: Europe/London
time_format: "24"           # or "12"
show_seconds: false
clock_size: large           # small, medium, large, "150%" (percent), "fit" (auto-size), "fit 75%" (auto-size then scale)
no_background: true
```

`clock_size` accepts named sizes (`small`, `medium`, `large`), a percentage
string like `"150%"` to scale the text, `"fit"` to auto-size text to fill
the card width without wrapping, or `"fit 75%"` to auto-size and then scale
down to 75% of the fill width.

#### Date line (via `lightdash`)

Show the current date below the time. Options are nested under `lightdash` to
make explicit they are LightDash-specific extensions:

```yaml
type: clock
clock_size: large
lightdash:
  date_show: true
  date_format: default         # default (toDateString), iso (toISOString), locale (toLocaleDateString)
  date_fontsize: "80%"         # same options as clock_size (%, fit, fit 75%)
```

![Clock](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-clock.png)

### sensor

```yaml
type: sensor
entity: sensor.temperature
name: Outside
graph: line                 # or leave unset
hours_to_show: 24
```

### gauge

```yaml
type: gauge
entity: sensor.battery
min: 0
max: 100
severity:
  green: 40
  yellow: 20
  red: 0
```

### history-graph / statistics-graph

```yaml
type: history-graph
title: Temperature
entities:
  - sensor.outdoor_temp
hours_to_show: 24
```

Requires uPlot (loaded from CDN).

### light

A legacy light card with toggle + brightness slider (all-in-one).

```yaml
type: light
entity: light.living_room
name: Ceiling
```

### grid / horizontal-stack / vertical-stack

Nested card layouts:

```yaml
type: grid
columns: 2
cards:
  - type: entity
    entity: sensor.a
  - type: entity
    entity: sensor.b
```

### conditional

Shows/hides a child card based on entity state conditions:

```yaml
type: conditional
conditions:
  - entity: light.test
    state: "on"
card:
  type: entity
  entity: sensor.a
```

### iframe

```yaml
type: iframe
url: https://example.com
aspect_ratio: "50%"
```

### weather-forecast

Displays current weather conditions and forecast from a `weather` entity. The
forecast is read from the entity's `attributes.forecast`, or from a separate
`forecast_entity` sensor (required for integrations like Pirate Weather that
don't expose forecast in entity state attributes).

```yaml
type: weather-forecast
entity: weather.openweathermap
forecast_entity: sensor.london_forecast_hourly    # optional forecast source
name: London                                       # optional
show_current: true                                 # optional, default true
show_forecast: true                                # optional, default true
forecast_type: hourly                              # daily / hourly / twice_daily
secondary_info_attribute: extrema                  # extrema / precipitation / humidity
round_temperature: false                           # round to whole degrees
forecast_count: 12                                 # items to show (default 5/12)
```

| Config | Description |
|--------|-------------|
| `forecast_entity` | Sensor entity to read forecast data from (e.g. a template sensor). If omitted, forecast is read from the main `entity`'s `attributes.forecast`. |
| `forecast_type` | `daily` — day name, icon, high/low. `hourly` — time, icon, temp. `twice_daily` — same layout as daily. |
| `secondary_info_attribute` | What to show under the current temperature. Defaults to `extrema` (high/low from today's forecast), then `precipitation`, then `humidity`. |
| `forecast_count` | How many forecast items to display. Defaults to 5 (daily/twice_daily) or 12 (hourly). |

Current conditions show the condition icon, condition name, temperature, and
secondary info. Forecast items are laid out horizontally (fill width for ≤5
items, scroll for more).

![Weather](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-weather.png)

### today-card

Lightweight day-agenda card showing events from one or more `calendar.*`
entities. Each calendar gets its own accent colour; events are marked as
past, current (with a "Now" pill), future, all-day, or multi-day.

```yaml
type: custom:today-card
title: "Today's Schedule"    # optional, omit to hide the header
advance: 0                   # optional, shift view by N days (1 = tomorrow)
show_all_day_events: true    # optional, default true
show_past_events: false      # optional, default false
limit: 0                     # optional, max events to show (0 = unlimited)
time_format: "HH:mm"         # optional, tokens: H HH h hh m mm A a
fallback_color: primary      # optional, HA colour name or hex for uncoloured calendars
height: 0                    # optional, fixed card height in px (0 = auto)
entities:
  - entity: calendar.work
    color: "#03a9f4"         # optional, hex or HA named colour
  - entity: calendar.family
    color: pink
tap_action:
  action: navigate
  navigation_path: agenda
```

| Config | Description |
|--------|-------------|
| `title` | Card header title. Omit to hide the header entirely. |
| `advance` | Shift the view forward (positive) or backward (negative) by N days. `0` = today. |
| `show_all_day_events` | Whether to include all-day events in the list. |
| `show_past_events` | Whether to include events that have already ended. |
| `limit` | Maximum number of events to display. `0` = show all matching events. |
| `time_format` | Time token format for event start/end times. Tokens: `HH` (00-23), `H` (0-23), `hh` (01-12), `h` (1-12), `mm` (00-59), `m` (0-59), `A` (AM/PM), `a` (am/pm). |
| `fallback_color` | Colour applied to calendars that don't specify their own `color`. Accepts any HA named colour (`primary`, `red`, `pink`, `green`, etc.) or a hex string. Defaults to cycling through an auto-palette. |
| `height` | Fixed card height in pixels. When set, the event list scrolls inside the card. `0` = auto-height (card grows with content). |
| `entities` | List of calendar entities. Each entry can be a bare entity ID string or an object with `entity` and optional `color`. |
| `color` | Per-calendar accent colour: hex string or HA named colour (e.g. `pink`, `amber`, `teal`, `indigo`). |

Colour mapping — any HA named colour is accepted as `color` or `fallback_color`:

| Name | Hex | Name | Hex | Name | Hex |
|------|-----|------|-----|------|-----|
| `primary` | `#03a9f4` | `red` | `#f44336` | `pink` | `#e91e63` |
| `purple` | `#926bc7` | `indigo` | `#3f51b5` | `blue` | `#2196f3` |
| `cyan` | `#00bcd4` | `teal` | `#009688` | `green` | `#4caf50` |
| `lime` | `#cddc39` | `yellow` | `#ffeb3b` | `orange` | `#ff9800` |
| `brown` | `#795548` | `grey` | `#9e9e9e` | `black` | `#000000` |

When no `color` and no `fallback_color` are set, calendars cycle through an
auto-palette: `#03a9f4`, `#e91e63`, `#009688`, `#ff9800`, `#926bc7`,
`#4caf50`, `#3f51b5`, `#00bcd4`.

The card respects `advance` for looking ahead or behind, and `limit` for
capping the number of visible events.

![Agenda](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-agenda.png)


### placeholder

Rendered when a card type is unknown. Displays a `?` placeholder.


Long-Press Modals
-----------------

Light and cover entities support long-press modals for fine-grained control.
Long-press any tile or entity row to open the modal.

### Light Dimmer

A vertical brightness slider with tap-to-toggle on the light icon. Drag up/down
to set brightness — value is sent on release. Tap the icon to toggle on/off
(turning on restores the last brightness).

![Dimmer modal](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-modal.png)

### Cover Position

A vertical position slider with open/stop/close buttons alongside, just like the dimmer above. Drag to set
a precise position, or tap the up/stop/down buttons for full open, halt, or
full close.


### Favourite Values

Configure up to 4 preset brightness or position values to appear as
tap-able buttons in the long-press modal. Set them under
`lightdash.favourite_values` on any tile or entity row:

```yaml
type: tile
entity: light.living_room
lightdash:
  favourite_values: [25, 50, 75, 100]
```

Each value must be an integer or float between 0 and 100. Values outside that
range are silently ignored. If more than 4 values are provided, only the
first 4 are used.

The buttons appear vertically on the left side of the modal, distributed
evenly top-to-bottom (highest to lowest):

![Favourite values](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-popup-favourites.png)

Tap a favourite button to set the brightness or position immediately.
The slider updates to match.

### Auto-Close

If `auto_close_modal_seconds` is set in the dashboard's `lightdash:` config,
the modal auto-dismisses after that many seconds of inactivity. Any
interaction (slider drag, button tap, backdrop tap) resets the timer.

Tap Actions
-----------

Cards can define a `tap_action` configuration:

| Action           | Effect                                                     |
|------------------|------------------------------------------------------------|
| `toggle`         | Posts entity toggle to HA                                  |
| `call-service`   | Calls an arbitrary HA service                              |
| `navigate`       | Navigates to another view within the same dashboard        |
| `url`            | Opens a URL in a new tab                                   |

```yaml
tap_action:
  action: call-service
  service: light.turn_on
  target:
    entity_id: light.living_room
  data:
    brightness_pct: 100
```


Auto-Mapped HA Custom Cards
---------------------------

These card types are automatically translated at parse time. The renderer
never sees the original type.

| Source card                      | Target    | Notes                                          |
|----------------------------------|-----------|------------------------------------------------|
| `custom:mushroom-light-card`     | `tile`    | brightness/color-temp features, inline layout  |
| `custom:mushroom-cover-card`     | `entities`| single entity row with open/stop/close buttons |
| `custom:mushroom-number-card`    | `tile`    | numeric-input feature                          |
| `custom:layout-card` (view type) | sections  | grouped by `custom:layout-break` into sections |

**Unsupported card types** (not mapped, rendered as `placeholder`):

- `custom:mushroom-template-card` — use `button` with `tap_action.navigate` instead
- `shortcut` — use `button` instead
- Any other `custom:*` card type


Badges
------

Badges are compact pills that sit above the cards in a view. They show entity state at a glance, navigate between views, or conditionally appear based on entity state.

![Badges](https://github.com/richkershaw/HA-LightDash/raw/main/example-images/example-badges.png)

Three badge types are supported — `entity`, `shortcut`, and `entity-filter`. See the [addon README](addons/lightdash/README.md#badges) for YAML examples.


Compatibility Checker
---------------------

The compatibility module (`app/compat.py`) scans dashboards at startup for
known limitations and logs warnings:

- **Custom card types not in the mapping table** — rendered as `placeholder`
- **HA Jinja2 template syntax** in markdown cards — unsupported
- **`card_mod` styling** — not supported
- **Mapped custom cards** — the mapping may not capture every nuance of the
  original Mushroom/Layout card configuration


Updating
--------

When a new version is released, the add-on shows an **Update** button on the
Info tab. Click it and then **Restart**. Dashboards persist across updates
in `/data/dashboards/`.


Architecture
------------

```
┌──────────────────────────────────────────────────────────────────┐
│                        LightDash (FastAPI)                       │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐                  │
│  │  parser  │◄──│  config  │◄──│  *yaml files  │  or inline      │
│  │  .py     │   │  .py     │   │  config/      │  add-on config  │
│  └────┬─────┘   └──────────┘   └──────────────┘                  │
│       │ Dashboard / View / Card models                           │
│       ▼                                                          │
│  ┌──────────┐                                                    │
│  │ renderer │────► HTML + CSS + JS  (htmx + SSE)                 │
│  │  .py     │                                                    │
│  └──────────┘                                                    │
│       │                                                          │
│  ┌──────────┐   ┌──────────────┐                                 │
│  │ compat   │   │  ha_client   │◄── HTTP POST /api/services/...  │
│  │  .py     │   │  .py         │◄── GET  /api/states/...         │
│  └──────────┘   └──────┬───────┘                                 │
│                        │                                         │
│  ┌──────────┐          │                                         │
│  │   sse    │◄─────────┘  WebSocket /api/websocket               │
│  │ manager  │──► SSE /_sse  (entity state events)                │
│  └──────────┘                                                    │
└──────────────────────────────────────────────────────────────────┘
        │
        │  Ingress (add-on) or direct HTTP (local dev)
        ▼
┌──────────────────┐       ┌────────────────────┐
│  Browser (client)│◄─────►│  Home Assistant    │
│  - htmx v2       │   SSE │  - REST API        │
│  - htmx-sse ext  │       │  - WebSocket       │
│  - live updates  │       └────────────────────┘
└──────────────────┘
```

**Data flow:**

1. **Startup** — YAML dashboard files are parsed into `Dashboard`/`View`/`Card`
   model objects. Custom HA card types (`custom:mushroom-*`,
   `custom:layout-card`) are mapped to native LightDash equivalents.

2. **Navigation** — `GET /d/{name}` redirects (302) to the first view.
   `GET /d/{name}/view/{path}` renders a full HTML page. If
   `auto_revert_seconds` is configured, a JS inactivity timer automatically
   navigates back to the first view on timeout.

3. **Rendering** — The renderer walks view cards/sections, generates HTML with
   htmx attributes for live interactions, SSE event attributes for live state
   updates, and inline CSS/JS for sliders, toggles, and clock.

4. **Live updates** — The SSE manager connects to the HA WebSocket API,
   subscribes to `state_changed` events, and relays entity state changes to
   connected browser clients via Server-Sent Events. htmx's
   `sse-swap` attribute updates entity state spans in-place.

5. **Actions** — Toggle switches, sliders, and tap actions POST to `/action`,
   which forwards service calls to the HA REST API.

6. **Long-press modals** — Light and cover entities open a dimmer or position
   modal on 500ms long-press. The modal reads entity state via `/api/state/{eid}`
   and sends actions via `navigator.sendBeacon()`. If `auto_close_modal_seconds`
   is configured, an inactivity timer auto-dismisses the modal.

7. **Toggle sync** — A JS function (`st()`) runs after every htmx swap and
   SSE message, synchronising toggle switch positions and dimming classes with
   the rendered entity state text.

7. **Slider sync** — A JS function (`ss()`) runs after SSE messages for views
   with brightness/color-temp features. It fetches the live entity state and
   updates slider values when the state changes externally.


Local Development
-----------------

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in HA_URL and HA_TOKEN
uvicorn app.main:app --reload  # → http://localhost:8000
```

Create dashboards by dropping YAML files into `config/`.
Each file becomes a dashboard at `/d/{filename_without_ext}`.

Run tests:

```bash
python3 -m pytest tests/test_pipeline.py -v
```
