from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from app.models import Card, Dashboard, FixedGrid, GridLayout, View

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_CONFIG = BASE_DIR / "config" / "living_room.yaml"


def test_parse_from_dict():
    from app.parser import parse_dashboard

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Test",
                "path": "test",
                "cards": [
                    {"type": "heading", "heading": "Hello"},
                    {"type": "markdown", "content": "**bold** text"},
                    {"type": "entity", "entity": "sensor.temp"},
                    {"type": "button", "name": "Press", "tap_action": {"action": "toggle", "entity": "light.test"}},
                    {"type": "tile", "entity": "light.test", "color": "yellow"},
                    {"type": "entities", "entities": [{"entity": "sensor.a"}, {"entity": "sensor.b"}], "title": "Sensors"},
                    {"type": "glance", "entities": ["sensor.a", "sensor.b"], "columns": 2},
                    {"type": "grid", "columns": 2, "cards": [{"type": "entity", "entity": "sensor.a"}, {"type": "entity", "entity": "sensor.b"}]},
                    {"type": "horizontal-stack", "cards": [{"type": "entity", "entity": "sensor.a"}, {"type": "entity", "entity": "sensor.b"}]},
                    {"type": "vertical-stack", "cards": [{"type": "entity", "entity": "sensor.a"}, {"type": "entity", "entity": "sensor.b"}]},
                    {"type": "conditional", "conditions": [{"entity": "light.test", "state": "on"}], "card": {"type": "entity", "entity": "sensor.a"}},
                    {"type": "light", "entity": "light.test"},
                    {"type": "sensor", "entity": "sensor.temp", "graph": "line"},
                    {"type": "gauge", "entity": "sensor.temp", "min": 0, "max": 100},
                    {"type": "history-graph", "entities": ["sensor.temp"], "hours_to_show": 24},
                    {"type": "iframe", "url": "https://example.com"},
                    {"type": "unknown_type"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    assert dashboard.title == "LightDash"
    assert len(dashboard.views) == 1
    view = dashboard.views[0]
    assert view.title == "Test"
    assert view.path == "test"

    card_types = [c.type for c in view.cards]
    assert "heading" in card_types
    assert "markdown" in card_types
    assert "entity" in card_types
    assert "button" in card_types
    assert "tile" in card_types
    assert "entities" in card_types
    assert "glance" in card_types
    assert "grid" in card_types
    assert "horizontal-stack" in card_types
    assert "vertical-stack" in card_types
    assert "conditional" in card_types
    assert "light" in card_types
    assert "sensor" in card_types
    assert "gauge" in card_types
    assert "history-graph" in card_types
    assert "iframe" in card_types
    assert "unknown_type" in card_types


def test_parse_and_render_all_cards():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "All Cards",
                "path": "all",
                "cards": [
                    {"type": "heading", "heading": "Section", "icon": "mdi:home"},
                    {"type": "markdown", "content": "Hello **world**"},
                    {"type": "entity", "entity": "sensor.temp", "name": "Temperature"},
                    {"type": "button", "name": "Toggle", "icon": "mdi:lightbulb", "tap_action": {"action": "toggle"}},
                    {"type": "tile", "entity": "light.test", "name": "Lamp", "icon": "mdi:lamp", "color": "yellow"},
                    {"type": "entities", "entities": [{"entity": "sensor.a"}, {"entity": "sensor.b"}], "title": "Sensors"},
                    {"type": "glance", "entities": ["sensor.a", "sensor.b", "sensor.c"], "columns": 3, "title": "Overview"},
                    {"type": "grid", "columns": 2, "cards": [{"type": "entity", "entity": "sensor.a"}, {"type": "entity", "entity": "sensor.b"}]},
                    {"type": "horizontal-stack", "cards": [{"type": "entity", "entity": "sensor.a"}, {"type": "entity", "entity": "sensor.b"}]},
                    {"type": "vertical-stack", "cards": [{"type": "entity", "entity": "sensor.a"}]},
                    {"type": "conditional", "conditions": [{"entity": "light.test", "state": "on"}], "card": {"type": "entity", "entity": "sensor.a"}},
                    {"type": "light", "entity": "light.test", "name": "Ceiling"},
                    {"type": "sensor", "entity": "sensor.temp", "name": "Temp"},
                    {"type": "gauge", "entity": "sensor.temp", "min": 0, "max": 100},
                    {"type": "history-graph", "entities": ["sensor.temp"], "hours_to_show": 24},
                    {"type": "iframe", "url": "https://example.com"},
                    {"type": "clock", "clock_style": "digital", "time_zone": "Europe/London", "time_format": "24", "no_background": True},
                    {"type": "placeholder"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert "<!DOCTYPE html>" in html
    assert 'id="view-all"' in html
    assert "htmx.org" in html
    assert "lv-view" in html
    assert "ha-card" in html

    for ctype in ["heading", "entity", "entities", "glance", "grid", "light", "sensor", "gauge", "iframe", "clock", "placeholder"]:
        assert f"{ctype}-card" in html or f"{ctype}_card" in html, f"Missing class for {ctype}"

        assert "Hello" in html
    assert "<strong>world</strong>" in html or "strong" in html


def test_tile_toggle_switch_for_binary_entity():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Tiles",
                "path": "tiles",
                "cards": [
                    {"type": "tile", "entity": "light.test", "name": "Lamp", "color": "yellow"},
                    {"type": "tile", "entity": "sensor.temp", "name": "Temp"},
                    {"type": "tile", "entity": "light.porch", "name": "Porch", "vertical": True, "hide_state": True},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert html.count('class="toggle-switch"') == 1, "Expected 1 toggle-switch (light.test only)"
    assert html.count('class="toggle-input"') == 1, "Expected 1 toggle-input"
    assert html.count('class="toggle-slider"') == 1, "Expected 1 toggle-slider"

    assert '<div class="tile-name">Temp</div>' in html

    assert '<div class="tile-name">Porch</div>' in html
    assert 'class="tile-content vertical"' in html, "Expected vertical class"
    assert html.count('class="entity-state"') == 3, "Expected 3 entity-state spans (light.test + sensor.temp + light.porch)"
    assert html.count('class="ha-card tile-card hide-state"') == 1, "Expected 1 tile-card with hide-state class"

    assert "function st()" in html, "Expected toggle sync script"


def test_tile_vertical_layout():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Tile Vertical",
                "path": "tv",
                "cards": [
                    {"type": "tile", "entity": "light.test", "vertical": True},
                    {"type": "tile", "entity": "light.test2"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="tile-content vertical"' in html
    assert 'class="tile-content"' in html
    assert html.count('class="tile-content') == 2


def test_tile_hide_state():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Tiles",
                "path": "tiles",
                "cards": [
                    {"type": "tile", "entity": "sensor.temp", "hide_state": True},
                    {"type": "tile", "entity": "sensor.temp2"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="entity-state"' in html
    assert html.count('class="entity-state"') == 1, "Expected only 1 entity-state (non-hidden tile)"


def test_uplot_loaded_when_needed():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Charts",
                "path": "charts",
                "cards": [
                    {"type": "sensor", "entity": "sensor.temp", "graph": "line"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert "uplot" in html.lower() or "uPlot" in html


def test_server_starts_and_serves():
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        r = client.get("/")
        assert r.status_code == 200
        assert "LightDash" in r.text

        r2 = client.get("/health")
        assert r2.status_code == 200
        data = r2.json()
        assert "status" in data
        assert "ha_connected" in data


def test_action_endpoint():
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        r = client.post("/action", json={"entity_id": "light.test", "action": "toggle", "service": "light.toggle"})
        assert r.status_code == 200

        r2 = client.post("/action", json={"entity_id": "light.test", "action": "call-service", "service": "light.turn_on", "target": {"entity_id": "light.test"}, "data": {"brightness_pct": 50}})
        assert r2.status_code == 200


def test_api_dashboard_endpoint():
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        r = client.get("/api/dashboard")
        assert r.status_code == 404


def test_unknown_card_renders_placeholder():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Test",
                "path": "test",
                "cards": [
                    {"type": "completely_fake_card_type"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert "placeholder-card" in html
    assert "?" in html


def test_markdown_rendering():
    from app.renderer import _render_markdown_text

    md = "# Title\n\n**bold** text\n\n- item 1\n- item 2\n\n`code`"
    html = _render_markdown_text(md)

    assert "Title" in html
    assert "strong" in html or "bold" in html


def test_friendly_name():
    from app.renderer import _friendly_name

    assert _friendly_name("sensor.living_room_temperature") == "Living Room Temperature"
    assert _friendly_name("light.test") == "Test"
    assert _friendly_name("no_dot") == "no_dot"


def test_entities_cover_controls():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "title": "Controls",
                        "entities": [
                            "sensor.temp",
                            "cover.kitchen_roof",
                            {"entity": "cover.garage_door", "name": "Garage"},
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Cover controls rendered for both cover entities
    assert 'class="cover-controls"' in html
    # Three buttons per cover × 2 covers = 6 inline control buttons
    assert html.count('class="cover-btn" aria-label') == 6

    # Buttons use correct services
    assert "cover.open_cover" in html
    assert "cover.stop_cover" in html
    assert "cover.close_cover" in html

    # Button symbols present
    assert "▲" in html
    assert "⏹" in html
    assert "▼" in html

    # Non-cover entity (sensor) has no cover controls
    # 2 cover entities = 2 containers; sensor row has none
    assert html.count("cover-controls") == 2


def test_tile_numeric_input_feature():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Numbers",
                "path": "nums",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "input_number.test",
                        "name": "Test",
                        "features": [
                            {"type": "numeric-input"},
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Numeric-input feature rendered
    assert 'class="numeric-input"' in html
    assert 'class="num-btn"' in html

    # Decrement and increment buttons
    assert "input_number.decrement" in html
    assert "input_number.increment" in html

    # Button symbols
    assert "−" in html or "&minus;" in html
    assert "+" in html


def test_clock_card_renderer():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Clock",
                "path": "clk",
                "cards": [
                    {
                        "type": "clock",
                        "clock_style": "digital",
                        "time_zone": "Europe/London",
                        "time_format": "24",
                        "show_seconds": False,
                        "no_background": True,
                        "clock_size": "medium",
                    },
                    {
                        "type": "clock",
                        "clock_style": "digital",
                        "time_zone": "US/Eastern",
                        "time_format": "12",
                        "show_seconds": True,
                        "clock_size": "large",
                    },
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Clock card class
    assert "clock-card" in html
    assert "clock-digital" in html

    # No-background variant
    assert "clock-no-bg" in html

    # Size classes
    assert "clock-size-medium" in html
    assert "clock-size-large" in html

    # Data attributes for first clock
    assert 'data-tz="Europe/London"' in html
    assert 'data-fmt="24"' in html
    assert 'data-sec="1"' in html  # second clock only

    # Second clock attributes
    assert 'data-tz="US/Eastern"' in html
    assert 'data-fmt="12"' in html

    # Clock ticker script injected
    assert "function uclk()" in html
    assert "setInterval(uclk,30000)" in html
    assert 'Intl.DateTimeFormat("en-GB"' in html or "Intl.DateTimeFormat" in html


def test_clock_size_percent():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "clock_size": "150%"}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert 'style="font-size: 150%"' in html


def test_clock_size_fit():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "clock_size": "fit"}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert "icey_text_fit" in html
    assert "/static/scripts.js" in html
    assert "icey_textFit()" in html


def test_clock_fit_retriggers_on_uclk():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "clock_size": "fit"}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert 'typeof icey_textFit==="function")icey_textFit()' in html


def test_clock_date_default():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert "clock-date" in html
    assert 'data-dfmt="default"' in html
    assert "toDateString()" in html


def test_clock_date_iso():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True, "date_format": "iso"}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert 'data-dfmt="iso"' in html
    assert 'toISOString().split("T")[0]' in html


def test_clock_date_locale():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True, "date_format": "locale"}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert 'data-dfmt="locale"' in html
    assert "toLocaleDateString()" in html


def test_clock_date_fontsize():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True, "date_fontsize": "80%"}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert 'style="font-size: 80%"' in html


def test_clock_date_fontsize_fit_triggers_scripts():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True, "date_fontsize": "fit"}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert "icey_text_fit" in html
    assert "/static/scripts.js" in html
    assert "icey_textFit()" in html


def test_clock_size_fit_pct():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "clock_size": "fit 75%"}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert "icey_text_fit" in html
    assert 'data-fit-pct="75"' in html
    assert "/static/scripts.js" in html


def test_clock_date_fontsize_fit_pct():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [{"title": "Clock", "path": "clk", "cards": [{"type": "clock", "lightdash": {"date_show": True, "date_fontsize": "fit 50%"}}]}]
    }
    dashboard = parse_dashboard(raw)
    html = render_view(dashboard.views[0], dashboard)
    assert "icey_text_fit" in html
    assert 'data-fit-pct="50"' in html
    assert "/static/scripts.js" in html


def test_entity_toggle_in_entities_card():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            "light.kitchen",
                            "sensor.temp",
                            "fan.bathroom",
                            "cover.garage",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Binary non-cover entities get toggle switches
    assert html.count('class="entity-toggle"') == 2, "Expected 2 toggles (light + fan)"

    # Cover gets cover controls instead
    assert 'class="cover-controls"' in html

    # Sensor gets no controls
    rows = html.split('class="entity-row"')
    assert len(rows) == 5  # header + 4 rows

    # Toggle sync script present (because light entity has toggle)
    assert "function st()" in html

    # Binary entity rows now have click-to-toggle hx attributes on the row div
    assert 'hx-post="/action"' in html
    assert "entity_id: 'light.kitchen'" in html, "Expected light row hx-vals"
    assert "entity_id: 'fan.bathroom'" in html, "Expected fan row hx-vals"
    # Sensor and cover rows still have plain entity-row (no hx-post on the row itself)
    assert '<div class="entity-row">\n' in html, "Non-togglable rows should be plain entity-row"


def test_entity_icon_resolution():
    import app.renderer as r

    # Priority 1: config icon wins
    assert r._entity_icon("light.porch", "mdi:lamp") == "mdi:lamp"
    # Priority 2: entity state icon (set module-level _entity_icons)
    r._entity_icons = {"light.porch": "mdi:lightbulb-outline", "sensor.temp": "mdi:thermometer-alert"}
    assert r._entity_icon("light.porch", "") == "mdi:lightbulb-outline"
    # Priority 3: domain default
    r._entity_icons = {}
    assert r._entity_icon("sensor.unknown", "") == "mdi:thermometer"
    # Priority 4: empty
    assert r._entity_icon("totally_fake.entity", "") == ""

def test_icon_html_without_ha_url():
    import app.renderer as r

    r._ha_url = ""
    assert r._icon_html("mdi:lightbulb", 24) == ""
    assert r._icon_html("", 24) == ""

def test_icon_html_with_cache():
    import app.renderer as r

    r._ha_url = "http://ha.local:8123"
    r._icon_svg_cache["lightbulb"] = '<svg viewBox="0 0 24 24"><path d="M12 2"/></svg>'
    html = r._icon_html("mdi:lightbulb", 24)
    assert 'class="icon"' in html
    assert 'width="24"' in html
    assert 'height="24"' in html
    assert '<path d="M12 2"/>' in html
    r._icon_svg_cache.clear()
    r._ha_url = ""


def test_navigate_action_uses_d_url():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Nav",
                "path": "nav",
                "cards": [
                    {
                        "type": "button",
                        "name": "Go",
                        "tap_action": {"action": "navigate", "navigation_path": "other"},
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard, dashboard_name="test_dash")

    assert 'hx-get="/d/test_dash/view/other"' in html


def test_entity_state_data_entity():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Test",
                "path": "test",
                "cards": [
                    {"type": "tile", "entity": "light.test"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-entity="light.test"' in html


def test_tile_light_brightness_feature():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "name": "Test Light",
                        "features": [
                            {"type": "light-brightness"},
                        ],
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Slider rendered
    assert 'class="feature-slider"' in html
    assert 'min="0"' in html
    assert 'max="100"' in html
    assert 'value="0"' in html  # default when no entity_states

    # No label when default (non-inline rendered with label)
    # Actually default is bottom, which HAS label
    assert "Brightness" in html

    # HTMX attributes for brightness control
    assert "brightness_pct" in html
    assert "light.turn_on" in html


def test_tile_light_brightness_inline():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "name": "Test Light",
                        "features_position": "inline",
                        "features": [
                            {"type": "light-brightness"},
                        ],
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Inline layout
    assert 'class="tile-info tile-info-inline"' in html

    # No label in inline mode
    assert "Brightness" not in html

    # Slider rendered
    assert 'class="feature-slider"' in html

    # ss() script injected (view has tile with light-brightness feature)
    assert "function ss(" in html


def test_tile_light_brightness_initial_value():
    """Slider value should reflect entity brightness from entity_states."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "features": [
                            {"type": "light-brightness"},
                        ],
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]

    # Test with brightness at 50% (128/255)
    entity_states = {
        "light.test": {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"brightness": 128},
        }
    }
    html = render_view(view, dashboard, entity_states=entity_states)
    assert 'value="50"' in html

    # Test with brightness at 100% (255/255)
    entity_states["light.test"]["attributes"]["brightness"] = 255
    html = render_view(view, dashboard, entity_states=entity_states)
    assert 'value="100"' in html

    # Test with light off - should default to 0
    entity_states["light.test"]["state"] = "off"
    html = render_view(view, dashboard, entity_states=entity_states)
    assert 'value="0"' in html


def test_lightdash_container_width():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "lightdash": {
            "container_width": "375px",
            "container_height": "667px",
        },
        "views": [
            {
                "title": "Test",
                "path": "test",
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ],
    }
    dashboard = parse_dashboard(raw)
    assert dashboard.lightdash.container_width == "375px"
    assert dashboard.lightdash.container_height == "667px"

    view = dashboard.views[0]
    html = render_view(view, dashboard)
    assert 'width: 375px' in html
    assert 'height: 667px' in html
    assert 'overflow-y: auto' in html


def test_lightdash_container_width_default():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Test",
                "path": "test",
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ],
    }
    dashboard = parse_dashboard(raw)
    assert dashboard.lightdash.container_width == ""
    assert dashboard.lightdash.container_height == ""

    view = dashboard.views[0]
    html = render_view(view, dashboard)
    assert 'width:' not in html
    assert 'height:' not in html


def test_weather_forecast_card():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Weather",
                "path": "wthr",
                "cards": [
                    {
                        "type": "weather-forecast",
                        "entity": "weather.openweathermap",
                        "name": "London",
                        "forecast_type": "daily",
                        "forecast_count": 3,
                        "round_temperature": True,
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    entity_states = {
        "weather.openweathermap": {
            "entity_id": "weather.openweathermap",
            "state": "partlycloudy",
            "attributes": {
                "temperature": 18.7,
                "temperature_unit": "\u00b0C",
                "humidity": 65,
                "pressure": 1013,
                "condition": "partlycloudy",
                "forecast": [
                    {"datetime": "2026-06-05T00:00:00", "temperature": 22, "templow": 14, "condition": "sunny", "precipitation": 0.0},
                    {"datetime": "2026-06-06T00:00:00", "temperature": 19, "templow": 12, "condition": "cloudy", "precipitation": 0.5},
                    {"datetime": "2026-06-07T00:00:00", "temperature": 16, "templow": 10, "condition": "rainy", "precipitation": 2.0},
                    {"datetime": "2026-06-08T00:00:00", "temperature": 20, "templow": 13, "condition": "partlycloudy"},
                ],
            },
        }
    }

    html = render_view(view, dashboard, entity_states=entity_states)

    assert "weather-card" in html
    assert "weather-current" in html
    assert "weather-forecast" in html
    assert "weather-icon-large" in html
    assert "weather-temp" in html
    assert "weather-condition" in html
    assert "Partly cloudy" in html
    assert "19°C" in html  # 18.7 rounded to 19
    assert "H: 22°C" in html  # extrema from first forecast day
    assert "L: 14°C" in html

    assert "weather-fc-item" in html
    assert html.count("weather-fc-item") == 3  # forecast_count=3 capped

    assert "Fri" in html or "Sat" in html  # day names
    assert "14-22°C" in html  # high/low from first forecast item (templow/temp)
    assert "10-16°C" in html  # third forecast item


def test_weather_forecast_without_current():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Weather",
                "path": "wthr",
                "cards": [
                    {
                        "type": "weather-forecast",
                        "entity": "weather.local",
                        "show_current": False,
                        "show_forecast": True,
                        "forecast_type": "hourly",
                        "forecast_count": 2,
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    entity_states = {
        "weather.local": {
            "entity_id": "weather.local",
            "state": "rainy",
            "attributes": {
                "temperature": 15.0,
                "temperature_unit": "\u00b0C",
                "forecast": [
                    {"datetime": "2026-06-05T14:00:00", "temperature": 15, "condition": "rainy"},
                    {"datetime": "2026-06-05T15:00:00", "temperature": 16, "condition": "cloudy"},
                ],
            },
        }
    }
    html = render_view(view, dashboard, entity_states=entity_states)

    # show_current=false — no current weather section
    assert "weather-current" not in html
    # Forecast still rendered
    assert "weather-forecast" in html
    assert html.count("weather-fc-item") == 2
    assert "14:00" in html
    assert "15:00" in html


def test_weather_forecast_no_state():
    """When entity has no state, render placeholder instead."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Weather",
                "path": "wthr",
                "cards": [
                    {"type": "weather-forecast", "entity": ""},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)
    assert "placeholder-card" in html


def test_tile_cover_controls():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Covers",
                "path": "covers",
                "cards": [
                    {"type": "tile", "entity": "cover.kitchen_roof", "name": "Roof"},
                    {"type": "tile", "entity": "light.test", "name": "Light"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Cover tile has cover controls (3 buttons) but no toggle
    assert 'class="cover-controls"' in html
    assert html.count('class="cover-btn"') == 3
    assert "cover.open_cover" in html
    assert "cover.stop_cover" in html
    assert "cover.close_cover" in html

    # Light tile still has toggle
    assert html.count('class="toggle-switch"') == 1
    assert html.count('class="toggle-input"') == 1

    # Cover tile has entity state span
    assert 'data-entity="cover.kitchen_roof"' in html

    # Cover tile body NOT clickable to toggle
    toggle_actions = html.count('hx-post="/action"')
    # Light tile has 1 action (toggle on body), cover has 3 actions (open/stop/close)
    assert toggle_actions >= 3


def test_tile_favourite_values_light():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "name": "Test Light",
                        "lightdash": {
                            "favourite_values": [25, 50, 75, 100],
                        },
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="25,50,75,100"' in html
    assert 'data-light-entity="light.test"' in html


def test_tile_favourite_values_cover():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Covers",
                "path": "covers",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "cover.garage",
                        "name": "Garage",
                        "lightdash": {
                            "favourite_values": [0, 50, 100],
                        },
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="0,50,100"' in html
    assert 'data-cover-entity="cover.garage"' in html


def test_entities_favourite_values_light():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            {
                                "entity": "light.kitchen",
                                "lightdash": {"favourite_values": [1, 10, 50, 99]},
                            },
                        ],
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="1,10,50,99"' in html
    assert 'data-light-entity="light.kitchen"' in html


def test_entities_favourite_values_cover():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            {
                                "entity": "cover.garage",
                                "lightdash": {"favourite_values": [0, 100]},
                            },
                        ],
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="0,100"' in html
    assert 'data-cover-entity="cover.garage"' in html


def test_favourite_values_truncation():
    """Only first 4 values should be emitted."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "lightdash": {"favourite_values": [10, 20, 30, 40, 50]},
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="10,20,30,40"' in html
    assert 'data-fav-vals="10,20,30,40,50"' not in html


def test_favourite_values_bounds_filtering():
    """Values outside 0-100 should be filtered out."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "lightdash": {"favourite_values": [-1, 0, 50, 100, 101]},
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="0,50,100"' in html


def test_favourite_values_non_numeric_filtered():
    """Non-numeric values (strings) should be filtered out."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "lightdash": {"favourite_values": ["foo", 50, None, 75]},
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="50,75"' in html


def test_favourite_values_empty_list_no_attribute():
    """Empty favourite_values list should not emit data-fav-vals."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                        "lightdash": {"favourite_values": []},
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="' not in html


def test_badge_entity_renders():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {"type": "entity", "entity": "sensor.temp", "name": "Temp"},
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badges-bar"' in html
    assert 'class="badge entity-badge"' in html
    assert 'class="badge-name"' in html
    assert "Temp" in html
    assert 'data-entity="sensor.temp"' in html


def test_badge_entity_binary_toggle():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {"type": "entity", "entity": "light.kitchen", "name": "Kitchen"},
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badge entity-badge"' in html
    assert 'hx-post="/action"' in html
    assert "light.toggle" in html


def test_badge_shortcut_navigate():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "shortcut",
                        "icon": "mdi:home",
                        "label": "Home",
                        "tap_action": {"action": "navigate", "navigation_path": "home"},
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard, dashboard_name="test_dash")

    assert 'class="badge shortcut-badge"' in html
    assert "badge-name" in html
    assert "Home" in html
    assert 'hx-get="/d/test_dash/view/home"' in html
    assert 'hx-target="body"' in html


def test_badge_shortcut_url():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "shortcut",
                        "label": "HA",
                        "tap_action": {"action": "url", "url_path": "http://ha.local:8123"},
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badge shortcut-badge"' in html
    assert "window.open" in html
    assert "http://ha.local:8123" in html


def test_badge_entity_filter_matches():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "entity-filter",
                        "entity": "light.kitchen",
                        "name": "Kitchen On",
                        "conditions": [{"entity": "light.kitchen", "state": "on"}],
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    entity_states = {"light.kitchen": {"entity_id": "light.kitchen", "state": "on"}}
    html = render_view(view, dashboard, entity_states=entity_states)

    assert 'class="badges-bar"' in html
    assert 'class="badge entity-filter-badge"' in html
    assert "Kitchen On" in html
    assert 'id="badge-0"' in html


def test_badge_entity_filter_no_match():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "entity-filter",
                        "entity": "light.kitchen",
                        "name": "Kitchen On",
                        "conditions": [{"entity": "light.kitchen", "state": "on"}],
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    entity_states = {"light.kitchen": {"entity_id": "light.kitchen", "state": "off"}}
    html = render_view(view, dashboard, entity_states=entity_states)

    assert 'class="badges-bar"' not in html
    assert "Kitchen On" not in html


def test_badge_entity_filter_no_conditions():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "entity-filter",
                        "entity": "light.kitchen",
                        "name": "Kitchen",
                        "conditions": [],
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badges-bar"' in html
    assert "Kitchen" in html


def test_badges_empty_list():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badges-bar"' not in html


def test_badges_no_badge_key():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "No Badges",
                "path": "nb",
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'class="badges-bar"' not in html


def test_css_link_loads_style_first():
    from app.renderer import _css_link

    html = _css_link("daylight")
    assert '/static/style.css' in html
    assert '/static/daylight.css' in html
    assert html.index('/static/style.css') < html.index('/static/daylight.css')


def test_badge_entity_filter_sse_trigger_wired():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw = {
        "views": [
            {
                "title": "Badge Test",
                "path": "bt",
                "badges": [
                    {
                        "type": "entity-filter",
                        "entity": "light.kitchen",
                        "name": "Kitchen",
                        "conditions": [{"entity": "light.kitchen", "state": "on"}],
                    },
                ],
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    entity_states = {"light.kitchen": {"entity_id": "light.kitchen", "state": "on"}}
    html = render_view(view, dashboard, entity_states=entity_states)

    assert 'hx-trigger="sse:entity_light_kitchen"' in html
    assert 'hx-get=' in html
    assert '/badge/0' in html
    assert 'hx-swap="outerHTML"' in html


def test_favourite_values_no_lightdash_key():
    """Missing lightdash key should not emit data-fav-vals."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {
                        "type": "tile",
                        "entity": "light.test",
                    }
                ],
            }
        ]
    }
    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'data-fav-vals="' not in html


# ---- fixed-grid view type tests ----


def test_parse_fixed_grid_view():
    from app.parser import parse_dashboard

    raw: Dict[str, Any] = {
        "views": [
            {
                "type": "fixed-grid",
                "title": "Grid View",
                "path": "grid",
                "grid": {"rows": 4, "columns": 6},
                "cards": [
                    {"type": "tile", "entity": "light.a", "grid_layout": {"x": 0, "y": 0, "width": 3, "height": 2}},
                    {"type": "tile", "entity": "light.b", "grid_layout": {"x": 3, "y": 0, "width": 3, "height": 1}},
                    {"type": "sensor", "entity": "sensor.temp", "grid_layout": {"x": 3, "y": 1, "width": 3, "height": 1}},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    assert len(dashboard.views) == 1
    view = dashboard.views[0]
    assert view.type == "fixed-grid"
    assert view.grid is not None
    assert view.grid.rows == 4
    assert view.grid.columns == 6
    assert len(view.cards) == 3
    assert len(view.sections) == 0

    gl = view.cards[0].grid_layout
    assert gl is not None
    assert gl.x == 0
    assert gl.y == 0
    assert gl.width == 3
    assert gl.height == 2

    gl = view.cards[1].grid_layout
    assert gl is not None
    assert gl.x == 3
    assert gl.y == 0
    assert gl.width == 3
    assert gl.height == 1

    assert view.cards[2].grid_layout is not None


def test_render_fixed_grid_view():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "type": "fixed-grid",
                "title": "Grid View",
                "path": "grid",
                "grid": {"rows": 4, "columns": 6},
                "cards": [
                    {"type": "tile", "entity": "light.a", "grid_layout": {"x": 0, "y": 0, "width": 3, "height": 2}},
                    {"type": "tile", "entity": "light.b", "grid_layout": {"x": 3, "y": 1, "width": 3, "height": 1}},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert "fixed-grid" in html
    assert "--fg-cols: 6" in html
    assert "aspect-ratio:" in html and "6" in html and "4" in html
    assert "grid-column: 1 / span 3" in html
    assert "grid-row: 1 / span 2" in html
    assert "grid-column: 4 / span 3" in html
    assert "grid-row: 2 / span 1" in html
    assert 'class="grid-cell"' in html
    assert "ha-card" in html


def test_fixed_grid_card_without_grid_layout():
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "type": "fixed-grid",
                "title": "Grid View",
                "path": "grid",
                "grid": {"rows": 3, "columns": 4},
                "cards": [
                    {"type": "tile", "entity": "light.a", "grid_layout": {"x": 0, "y": 0, "width": 2, "height": 1}},
                    {"type": "sensor", "entity": "sensor.temp"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    assert view.cards[1].grid_layout is None

    html = render_view(view, dashboard)

    assert "grid-column: 1 / span 2" in html
    assert html.count('class="grid-cell"') == 2


def test_entities_card_lightdash_show_toggle_false():
    """Card-level lightdash: show_toggle: false removes toggles and the sync script."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "title": "Lights",
                        "lightdash": {"show_toggle": False},
                        "entities": [
                            "light.kitchen",
                            "sensor.temp",
                            "fan.bathroom",
                            "cover.garage",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # No toggles rendered anywhere
    assert html.count('class="entity-toggle"') == 0, "Expected 0 toggles"

    # Cover still gets cover controls
    assert 'class="cover-controls"' in html

    # Rows keep their layout
    rows = html.split('class="entity-row"')
    assert len(rows) == 5  # header + 4 rows

    # No toggle sync script injected (no visible toggles in view)
    assert "function st()" not in html

    # No click-to-toggle on the row divs (cover controls still use hx-post)
    assert "action: 'toggle'" not in html


def test_entities_entity_lightdash_show_toggle_false():
    """Per-entity lightdash: show_toggle: false suppresses only that row's toggle."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            {"entity": "light.kitchen", "lightdash": {"show_toggle": False}},
                            "fan.bathroom",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Only fan.bathroom keeps a toggle
    assert html.count('class="entity-toggle"') == 1, "Expected 1 toggle (fan.bathroom only)"
    assert "entity_id: 'fan.bathroom'" in html
    assert "entity_id: 'light.kitchen'" not in html

    # Sync script still injected because one toggle remains
    assert "function st()" in html


def test_entities_show_toggle_defaults_on():
    """Without lightdash.show_toggle the toggle behavior is unchanged."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            "light.kitchen",
                            "fan.bathroom",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert html.count('class="entity-toggle"') == 2
    assert "function st()" in html


def test_dimmer_modal_emitted_for_light_tile():
    """Long-press dimmer modal markup must be injected when a light tile is present."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {"type": "tile", "entity": "light.kitchen", "name": "Kitchen"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    # Modal container emitted and hidden by default
    assert 'id="dimmer-modal"' in html
    assert 'id="dimmer-modal" style="display:none"' in html or 'style="display:none"' in html

    # Every element the dimmer.js script drives must exist
    for elem in ["dimmer-track", "dimmer-fill", "dimmer-pct", "dimmer-name",
                 "dimmer-close-btn", "dimmer-icon", "dimmer-left"]:
        assert f'id="{elem}"' in html, f"Missing #{elem}"

    # Trigger element present
    assert 'data-light-entity="light.kitchen"' in html


def test_cover_modal_emitted_for_cover_tile():
    """Long-press cover modal markup must be injected when a cover tile is present."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Covers",
                "path": "covers",
                "cards": [
                    {"type": "tile", "entity": "cover.garage", "name": "Garage"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="cover-modal"' in html
    for elem in ["cover-track", "cover-fill", "cover-pos", "cover-name",
                 "cover-close-btn", "cover-btn-up", "cover-btn-stop", "cover-btn-down", "cover-left"]:
        assert f'id="{elem}"' in html, f"Missing #{elem}"

    # Cover control buttons present
    assert "▲" in html
    assert "⏹" in html
    assert "▼" in html


def test_dimmer_modal_emitted_for_light_entity_row():
    """Long-press dimmer also wires up for light entities inside entities cards."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            "light.kitchen",
                            "sensor.temp",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="dimmer-modal"' in html
    assert 'data-light-entity="light.kitchen"' in html


def test_modals_not_emitted_without_light_or_cover():
    """No modal markup or scripts when a view has neither lights nor covers."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Sensors",
                "path": "sensors",
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="dimmer-modal"' not in html
    assert 'id="cover-modal"' not in html
    assert "showDimmer" not in html
    assert "showCover" not in html


def test_fan_modal_emitted_for_fan_tile():
    """Long-press level modal (dimmer) must be injected for fan tiles."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Fans",
                "path": "fans",
                "cards": [
                    {"type": "tile", "entity": "fan.bathroom", "name": "Bathroom Fan"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="dimmer-modal"' in html
    assert 'data-fan-entity="fan.bathroom"' in html
    assert 'id="dimmer-track"' in html
    assert 'id="dimmer-pct"' in html


def test_fan_modal_emitted_for_fan_entity_row():
    """Long-press level modal also wires up for fan rows inside entities cards."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            "fan.living_room",
                            "sensor.temp",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="dimmer-modal"' in html
    assert 'data-fan-entity="fan.living_room"' in html


def test_climate_modal_emitted_for_climate_tile():
    """Long-press climate modal must be injected for climate tiles."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Climate",
                "path": "climate",
                "cards": [
                    {"type": "tile", "entity": "climate.living_room", "name": "Living Room"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="climate-modal"' in html
    assert 'data-climate-entity="climate.living_room"' in html
    for elem in ["climate-current-temp", "climate-target-temp", "climate-temp-up",
                 "climate-temp-down", "climate-modes", "climate-close-btn", "climate-name"]:
        assert f'id="{elem}"' in html, f"Missing #{elem}"


def test_climate_modal_emitted_for_climate_entity_row():
    """Long-press climate modal also wires up for climate rows inside entities cards."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Entities",
                "path": "ents",
                "cards": [
                    {
                        "type": "entities",
                        "entities": [
                            "climate.master",
                            "sensor.temp",
                        ],
                    }
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="climate-modal"' in html
    assert 'data-climate-entity="climate.master"' in html


def test_modals_not_emitted_without_supported_domains():
    """No dimmer/cover/climate modal markup when a view has none of those domains."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Sensors",
                "path": "sensors",
                "cards": [
                    {"type": "entity", "entity": "sensor.temp"},
                    {"type": "tile", "entity": "switch.something"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    assert 'id="dimmer-modal"' not in html
    assert 'id="cover-modal"' not in html
    assert 'id="climate-modal"' not in html
    assert "showDimmer" not in html
    assert "showCover" not in html
    assert "showClimate" not in html


def test_modal_scripts_rendered_in_body_slot():
    """Modal scripts must live inside the body (not head) so htmx view swaps re-run them."""
    from app.parser import parse_dashboard
    from app.renderer import render_view

    raw: Dict[str, Any] = {
        "views": [
            {
                "title": "Lights",
                "path": "lights",
                "cards": [
                    {"type": "tile", "entity": "light.kitchen", "name": "Kitchen"},
                    {"type": "tile", "entity": "fan.bathroom", "name": "Bath Fan"},
                    {"type": "tile", "entity": "climate.living", "name": "HVAC"},
                    {"type": "tile", "entity": "cover.garage", "name": "Garage"},
                ],
            }
        ]
    }

    dashboard = parse_dashboard(raw)
    view = dashboard.views[0]
    html = render_view(view, dashboard)

    body = html.split("</head>", 1)[1]

    # Scripts must be inside body so they re-execute on htmx body swaps
    assert "window.__ldLevelWired" in body
    assert "window.__ldCoverWired" in body
    assert "window.__ldClimateWired" in body
    # And must not be duplicated in head
    head = html.split("</head>", 1)[0]
    assert "window.__ldLevelWired" not in head
    assert "window.__ldCoverWired" not in head
    assert "window.__ldClimateWired" not in head
