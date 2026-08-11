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

You can optionally fix the container size - useful for small-screen devices, and previewing rendering. You can also set auto-timeout behaviours.

```yaml
lightdash:
  container_width: 480px           # fixed container width (e.g. 480px, 100%)
  container_height: 480px          # fixed container height
  auto_revert_seconds: 120         # auto-return to first view after inactivity (0=disabled)
  auto_close_modal_seconds: 15     # auto-close popup modals after inactivity (0=disabled)
  theme: glass                     # optional, CSS theme name (see below)
```

#### CSS Themes

LightDash ships with 10 visual themes selectable via `lightdash.theme`:

| Theme       | Style                                            |
|-------------|--------------------------------------------------|
| `ha-dark`   | Default — dark HA-style, neutral greys           |
| `daylight`  | Warm light background, soft amber accents        |
| `glass`     | Frosted translucent panels, vibrant backdrop     |
| `hearth`    | Deep rich tones, red/orange warmth               |
| `ink`       | Pure black & white, high contrast                |
| `sage`      | Muted greens, earthy feel                        |
| `soft`      | Pastel tones, gentle readability                 |
| `bauhaus`   | Sharp corners, bold geometric aesthetic          |
| `terminal`  | Monospace amber-green, retro CRT vibe            |

All themes share the same class structure — switching is a one-line config
change with no YAML restructuring needed.

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

**Long-press dimmer and cover modals:** Light tiles and cover tiles support
long-press (or hold-click) to open a full-screen modal with a vertical
position slider. Long-press on mobile, hold-click on desktop.

**Favourite values** on light and cover tiles — set up to 4 preset brightness
or position values that appear as tap-able shortcuts inside the modal:

```yaml
type: tile
entity: light.living_room
lightdash:
  favourite_values: [25, 50, 75, 100]   # up to 4 values, 0–100
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

To remove the toggle switches (and the click-to-toggle behaviour) from a card,
set `lightdash.show_toggle` to `false` on the card, or on an individual row:

```yaml
type: entities
title: Lights
lightdash:
  show_toggle: false     # hide toggles for the whole card
entities:
  - entity: light.kitchen
  - entity: light.dining_room
  - entity: fan.bathroom
    lightdash:
      show_toggle: false # ...or just for this row
```

**Additional entity-row options:**

```yaml
entities:
  - entity: light.kitchen
    name: Kitchen
    icon: mdi:counter
    icon: none                # hide the icon entirely
    features:                 # inline controls on entity rows
      - type: numeric-input
        style: buttons        # increment/decrement buttons
```

Set `icon: none` to hide the icon row — name and state shift left for a
cleaner compact look. Entity rows support `features` (same as tile cards):
`numeric-input` adds +/- buttons alongside the state text.

### button

A compact action button. Icon and name are on one line. Supports `tap_action`.

```yaml
type: button
name: Other Rooms
icon: mdi:arrow-right-bold
tap_action:
  action: navigate
  navigation_path: other-rooms
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
clock_size: large           # small / medium / large / fit / "fit 75%" / "150%"
no_background: true
lightdash:
  date_show: true            # show date line below time
  date_format: default       # default / iso / locale
  date_fontsize: fit 50%     # date line size (same options as clock_size)
```

`clock_size` accepts `small`, `medium`, `large`, `"fit"` (auto-scale to fill
width), `"fit N%"` (auto-scale then reduce by percentage), or percentage
strings like `"150%"`.

The `lightdash` subsection adds an optional date line below the clock.
`date_format` options: `default` (long date), `iso` (YYYY-MM-DD),
`locale` (localised short format). `date_fontsize` uses the same sizing
options as `clock_size`.

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

Displays current weather conditions from a `weather` domain entity and
forecast data from that entity's `forecast` attribute, or from a separate
``forecast_entity`` sensor (for integrations like Pirate Weather that
don't expose forecast in the entity state).

```yaml
type: weather-forecast
entity: weather.openweathermap      # current conditions source
forecast_entity: sensor.london_forecast_hourly  # optional, forecast data source
name: My Location                   # optional
show_current: true                  # optional, default true
show_forecast: true                 # optional, default true
forecast_type: hourly               # daily / hourly / twice_daily
secondary_info_attribute: extrema   # optional: extrema / precipitation / humidity
round_temperature: false            # optional, round temps to nearest integer
forecast_count: 12                  # optional, number of forecast items to show
```

| Config | Description |
|--------|-------------|
| `forecast_entity` | Sensor entity to read forecast data from (e.g. a template sensor). If omitted, forecast is read from the main `entity`'s `attributes.forecast`. |
| `forecast_type` | `daily` — shows day name, icon, high/low. `hourly` — shows time, icon, temp. `twice_daily` — same layout as daily. |
| `secondary_info_attribute` | What to show under the current temperature. Defaults to `extrema` (high/low from today's forecast), then `precipitation`, then `humidity`. |
| `forecast_count` | How many forecast items to display. Defaults to 5 (daily/twice_daily) or 12 (hourly). |

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

### alarm-panel

Full-featured alarm control panel for the [Alarmo](https://github.com/nielsfaber/alarmo)
integration. Shows a state badge with colour-coded icon and label, arm/disarm
action buttons, a numeric keypad for code entry, arming options (skip exit
delay, bypass open sensors), and diagnostic messages.

```yaml
type: alarm-panel
entity: alarm_control_panel.alarmo
name: House Alarm
show_keypad: true          # optional, show numeric keypad (default true)
show_messages: true        # optional, show diagnostic messages (default true)
show_bypassed_sensors: true  # optional, show bypassed-sensors warning (default true)
skip_delay: false          # optional, default state for "Skip exit delay" checkbox
force: false               # optional, default state for "Bypass open sensors" checkbox
states:                    # optional, override per-state appearance
  armed_home:
    button_label: "Stay"   # rename the arm button
    hide: false            # set true to hide this arm button
    button_order: 2        # reorder buttons (ascending, default 0)
  armed_away:
    button_icon: mdi:shield-lock  # override button icon
    button_label: "Full"
  disarmed:
    state_label: "Offline" # override the status label shown
    color: "#4CAF50"       # override the state colour
  armed_night:
    hide: true             # hides this arm mode entirely
```

**State colours and icons:**

| State                  | Default colour | Icon                |
|------------------------|---------------|---------------------|
| `disarmed`             | Green         | `shield-off`        |
| `armed_home`           | Red           | `shield-home`       |
| `armed_away`           | Red           | `shield-lock`       |
| `armed_night`          | Red           | `shield-moon`       |
| `armed_vacation`       | Red           | `shield-airplane`   |
| `armed_custom_bypass`  | Red           | `shield-check`      |
| `triggered`            | Bright red    | `bell-ring`         |
| `arming` / `pending`   | Amber         | `shield-sync` / `shield-alert` |

**Action buttons** appear when the alarm is disarmed. Available modes: Away,
Home, Night, Vacation, Bypass. A **Disarm** button (red-accented) replaces
them when the alarm is armed.

**Code entry:** A password input accepts the disarm/arm code. When `show_keypad`
is enabled (default), a 3-column numeric keypad (1-9, 0, backspace, clear)
replaces the text input — dot indicators show how many digits have been entered.
The code auto-clears after 120 seconds of inactivity.

**Arming options** (shown only when disarmed):
- **Skip exit delay** — arms immediately, no countdown
- **Bypass open sensors** — forces arming, temporarily bypassing sensors

**Diagnostic messages** appear when:
- **Sensors triggered:** alarm is in `triggered` state with `open_sensors`
  in entity attributes — each sensor shown as a badge with name and state
- **Sensors blocking:** arm attempt failed because sensors are open — shown
  on the re-rendered card after the service call fails
- **Bypassed sensors active:** alarm is armed with bypassed sensors

**Live updates:** The card listens for SSE entity state events. If someone
arms or disarms the alarm from a keypad, the HA app, or an automation, the
card re-renders automatically — no page refresh needed.

### placeholder

Rendered when a card type is unknown. Displays a `?` placeholder.


Badges
------

Views can display a row of compact pill-shaped badges at the top of the
dashboard. Three badge types are available:

### Entity badges

Display an entity's icon, name, and live state. Tap to toggle binary entities.

```yaml
badges:
  - type: entity
    entity: light.porch
    name: Porch
  - type: entity
    entity: sensor.temperature
    name: Temp
```

### Shortcut badges

Navigate to another view or open an external URL.

```yaml
badges:
  - type: shortcut
    icon: mdi:arrow-left-bold
    label: Back
    tap_action:
      action: navigate
      navigation_path: home
  - type: shortcut
    icon: mdi:weather-sunny
    label: HA
    tap_action:
      action: url
      url_path: http://ha.local:8123
```

### Entity-filter badges

Only appear when conditions are met. Re-evaluates on SSE entity state
changes so the badge appears and disappears dynamically.

```yaml
badges:
  - type: entity-filter
    entity: cover.kitchen_roof
    name: Roof open
    conditions:
      - entity: cover.kitchen_roof
        state: open
```

Tap an entity-filter badge to navigate to another view:

```yaml
  - type: entity-filter
    entity: sensor.smoke_co_alarm
    name: Smoke alarm
    conditions:
      - entity: sensor.smoke_co_alarm
        state: 'on'
    tap_action:
      action: navigate
      navigation_path: alerts
```


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
| `custom:today-card`              | `today`   | day-agenda card for `calendar.*` entities      |
| `custom:alarmo-card`             | `alarm-panel` | alarm control panel for Alarmo integration |
| `custom:layout-card` (view type) | sections  | grouped by `custom:layout-break` into sections |

**Unsupported card types** (not mapped, rendered as `placeholder`):

- `custom:mushroom-template-card` — use `button` with `tap_action.navigate` instead
- `shortcut` — use `button` instead
- Any other `custom:*` card type


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