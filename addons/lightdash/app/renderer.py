from __future__ import annotations

import contextvars
import html
import httpx
import json
import logging
import re
from collections import OrderedDict
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Tuple

import datetime as _today_dt

from app.compat import JINJA_RE
from app.constants import _SW_SCRIPT
from app.models import Action, Card, Dashboard, Section, View

logger = logging.getLogger(__name__)

_SP = "  "
_DEFAULT_SECTION_COLUMNS = 1

RENDERERS: Dict[str, Any] = {}

_DEFAULT_ICONS: Dict[str, str] = {
    "light": "mdi:lightbulb",
    "switch": "mdi:light-switch",
    "fan": "mdi:fan",
    "input_boolean": "mdi:toggle-switch-variant",
    "cover": "mdi:blinds",
    "lock": "mdi:lock",
    "scene": "mdi:palette",
    "script": "mdi:script-text-play",
    "automation": "mdi:robot",
    "sensor": "mdi:thermometer",
    "binary_sensor": "mdi:motion-sensor",
    "climate": "mdi:thermostat",
    "media_player": "mdi:speaker",
    "person": "mdi:account",
    "sun": "mdi:white-balance-sunny",
    "weather": "mdi:weather-partly-cloudy",
    "button": "mdi:button-pointer",
    "input_number": "mdi:numeric",
    "input_select": "mdi:form-dropdown",
    "number": "mdi:numeric",
    "select": "mdi:form-dropdown",
    "timer": "mdi:timer",
    "vacuum": "mdi:robot-vacuum",
    "camera": "mdi:camera",
    "device_tracker": "mdi:cellphone",
    "alarm_control_panel": "mdi:shield-alert",
    "valve": "mdi:valve",
    "water_heater": "mdi:water-boiler",
    "update": "mdi:package-up",
    "siren": "mdi:alarm-light",
    "humidifier": "mdi:water-percent",
}

_DEFAULT_THEME = "ha-dark"

def _css_link(theme: str = "") -> str:
    if not theme:
        theme = _DEFAULT_THEME
    return '<link rel="stylesheet" href="' + _url("/static/style.css") + '">\n<link rel="stylesheet" href="' + _url(f"/static/{theme}.css") + '">\n'

_entity_icons: Dict[str, str] = {}
_entity_states: Dict[str, Any] = {}
_ha_url: str = ""
_dashboard_name: str = ""
_view_path: str = ""
_base_path: str = ""
_forecast_data: Dict[str, list] = {}
_calendar_data: Dict[str, list] = {}
_via_ingress = contextvars.ContextVar("renderer_via_ingress", default=False)
_icon_svg_cache: Dict[str, str] = OrderedDict()
_ICON_CACHE_MAX = 200

_TPL_DIR = Path(__file__).parent / "templates"

def _load_tpl(name: str) -> Template:
    return Template((_TPL_DIR / name).read_text())

_TPL_VIEW = _load_tpl("view.html")
_TPL_VIEW_INDEX = _load_tpl("view_index.html")
_TPL_DASH_INDEX = _load_tpl("dashboard_index.html")
_TPL_ERROR = _load_tpl("error.html")
_TPL_TOGGLE_SYNC = _load_tpl("toggle_sync.js")
_TPL_SLIDER_SYNC = _load_tpl("slider_sync.js")
_TPL_DIMMER = _load_tpl("dimmer.js")
_TPL_COVER = _load_tpl("cover.js")
_TPL_CLIMATE = _load_tpl("climate.js")
_TPL_AUTO_REVERT = _load_tpl("auto_revert.js")
_TPL_ALARM_PANEL = _load_tpl("alarm_panel.js")

_DIMMER_MODAL_HTML = (_TPL_DIR / "dimmer_modal.html").read_text() if (_TPL_DIR / "dimmer_modal.html").exists() else ""
_COVER_MODAL_HTML = (_TPL_DIR / "cover_modal.html").read_text() if (_TPL_DIR / "cover_modal.html").exists() else ""
_CLIMATE_MODAL_HTML = (_TPL_DIR / "climate_modal.html").read_text() if (_TPL_DIR / "climate_modal.html").exists() else ""


def _url(path: str) -> str:
    if _base_path and _via_ingress.get():
        return _base_path + path
    return path


def register(type_name: str):
    def decorator(fn):
        RENDERERS[type_name] = fn
        return fn
    return decorator


def render_view(view: View, dashboard: Dashboard, ha_url: str = "", entity_icons: Optional[dict] = None, entity_states: Optional[dict] = None, dashboard_name: str = "", forecast_data: Optional[dict] = None, calendar_data: Optional[dict] = None) -> str:
    global _entity_icons, _entity_states, _ha_url, _dashboard_name, _view_path, _forecast_data, _calendar_data
    _entity_icons = entity_icons or {}
    _entity_states = entity_states or {}
    _ha_url = ha_url or ""
    _dashboard_name = dashboard_name or ""
    _view_path = view.path
    _forecast_data = forecast_data or {}
    _calendar_data = calendar_data or {}

    _prefetch_icons(view)

    bg = ""
    if view.bg_color:
        bg += f"background-color: {view.bg_color};"
    if view.bg_image:
        img = view.bg_image
        if img.startswith("/api/image/serve/"):
            img = _url("/ha/image/serve/" + img[len("/api/image/serve/"):])
        bg += f"background-image: url('{html.escape(img)}');background-size: cover;background-position: center;"
    if dashboard.lightdash.container_width:
        bg += f"width: {dashboard.lightdash.container_width}; max-width: none;"
    if dashboard.lightdash.container_height:
        bg += f"height: {dashboard.lightdash.container_height};overflow-y: auto;"

    needs_uplot = _view_needs_charts(view)

    if view.type == "fixed-grid" and view.grid:
        cards_html = _render_fixed_grid(view, dashboard.lightdash.container_height, dashboard.lightdash.container_width)
    elif view.sections:
        cards_html = "\n".join(_render_section(s, 2) for s in view.sections)
    else:
        cards_html = "\n".join(_render_card(c, 2) for c in view.cards)

    title = html.escape(view.title or dashboard.title)
    path = html.escape(view.path)

    head_extra = ""
    if needs_uplot:
        head_extra += (
            '<script src="https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.iife.min.js"></script>\n'
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/uplot@1.6.31/dist/uPlot.min.css">\n'
        )
    if _view_needs_toggle_sync(view):
        head_extra += _TPL_TOGGLE_SYNC.substitute(state_api_url=_url("/api/state/"))
    if _view_needs_slider_sync(view):
        head_extra += _TPL_SLIDER_SYNC.substitute(state_api_url=_url("/api/state/"))
    needs_clock = _view_needs_clock(view)
    needs_fit_text = _view_needs_fit_text(view)
    if needs_clock or needs_fit_text:
        head_extra += '<script src="' + _url("/static/scripts.js") + '"></script>\n'
    modal_html = ""
    modal_scripts = ""
    body_script = ""

    if dashboard.lightdash.auto_close_modal_seconds > 0:
        body_script += '<script>var _acMs=' + str(dashboard.lightdash.auto_close_modal_seconds * 1000) + ';</script>\n'

    if _view_needs_level_modal(view):
        auto_close_timer = ""
        auto_close_reset = ""
        if dashboard.lightdash.auto_close_modal_seconds > 0:
            auto_close_timer = (
                "clearTimeout(_acTimer);_acTimer=setTimeout(hideDimmer,_acMs);\n"
            )
            auto_close_reset = "if(typeof _acMs!=='undefined'){clearTimeout(_acTimer);_acTimer=setTimeout(hideDimmer,_acMs)}"

        modal_html += _DIMMER_MODAL_HTML
        modal_scripts += _TPL_DIMMER.substitute(
            action_url=_url("/action"),
            state_api_url=_url("/api/state/"),
            auto_close_timer=auto_close_timer,
            auto_close_reset=auto_close_reset,
        )

    if _view_needs_cover_modal(view):
        auto_close_timer = ""
        auto_close_reset = ""
        if dashboard.lightdash.auto_close_modal_seconds > 0:
            auto_close_timer = (
                "clearTimeout(_acTimer);_acTimer=setTimeout(hideCover,_acMs);\n"
            )
            auto_close_reset = "if(typeof _acMs!=='undefined'){clearTimeout(_acTimer);_acTimer=setTimeout(hideCover,_acMs)}"

        modal_html += _COVER_MODAL_HTML
        modal_scripts += _TPL_COVER.substitute(
            action_url=_url("/action"),
            state_api_url=_url("/api/state/"),
            auto_close_timer=auto_close_timer,
            auto_close_reset=auto_close_reset,
        )

    if _view_needs_climate_modal(view):
        auto_close_timer = ""
        auto_close_reset = ""
        if dashboard.lightdash.auto_close_modal_seconds > 0:
            auto_close_timer = (
                "clearTimeout(_acTimer);_acTimer=setTimeout(hideClimate,_acMs);\n"
            )
            auto_close_reset = "if(typeof _acMs!=='undefined'){clearTimeout(_acTimer);_acTimer=setTimeout(hideClimate,_acMs)}"

        modal_html += _CLIMATE_MODAL_HTML
        modal_scripts += _TPL_CLIMATE.substitute(
            action_url=_url("/action"),
            state_api_url=_url("/api/state/"),
            auto_close_timer=auto_close_timer,
            auto_close_reset=auto_close_reset,
        )

    if _view_needs_alarm_panel(view):
        head_extra += _TPL_ALARM_PANEL.substitute()

    if dashboard.lightdash.auto_revert_seconds > 0:
        first_view_url = _url("/d/" + html.escape(_dashboard_name) + "/view/" + html.escape(dashboard.views[0].path))
        ar_secs = dashboard.lightdash.auto_revert_seconds * 1000
        body_script += _TPL_AUTO_REVERT.substitute(
            first_view_url=json.dumps(first_view_url),
            ar_secs=str(ar_secs),
        )

    body_tail = ""
    if needs_fit_text:
        body_tail = '<script>window.addEventListener("DOMContentLoaded",()=>{icey_textFit()});</script>\n'

    return _TPL_VIEW.substitute(
        title=title,
        css_link=_css_link(dashboard.lightdash.theme),
        sw_script=_SW_SCRIPT,
        head_extra=head_extra,
        body_script=body_script,
        path=path,
        sse_url=_url("/_sse"),
        bg=bg,
        badges=_render_badges(view),
        cards_html=cards_html + "\n",
        modal_html=modal_html,
        scripts=modal_scripts,
        body_tail=body_tail,
    )



def _render_fixed_grid(view: View, container_height: str = "", container_width: str = "") -> str:
    g = view.grid
    if g is None:
        return ""
    indent = 2
    gap = 8

    cards_html = ""

    if container_width and container_height:
        cw = int(container_width.replace("px", ""))
        pad = 12
        grid_w = cw - 2 * pad

        layouts = [c.grid_layout for c in view.cards if c.grid_layout]
        columns = max((gl.x + gl.width for gl in layouts), default=g.columns)
        columns = max(columns, g.columns)

        col_w = (grid_w - (columns - 1) * gap) / columns

        style = "position: relative; display: block;"
        row_h = 40

        for c in view.cards:
            gl = c.grid_layout
            cell_style = ""
            if gl is not None:
                left = gl.x * (col_w + gap)
                top = gl.y * row_h
                width = gl.width * col_w + (gl.width - 1) * gap
                height = gl.height * row_h + (gl.height - 1) * gap
                cell_style = f"position: absolute; left: {left:.1f}px; top: {top:.1f}px; width: {width:.1f}px; height: {height:.1f}px;"

            cell_attrs = {"class": "grid-cell"}
            if cell_style:
                cell_attrs["style"] = cell_style

            card_content = _render_card(c, indent + 1)
            cards_html += "\n" + _SP * (indent + 1) + f"<div{_build_attrs(cell_attrs)}>\n"
            cards_html += card_content
            cards_html += "\n" + _SP * (indent + 1) + "</div>"
    else:
        style = f"--fg-cols: {g.columns}; grid-template-rows: repeat({g.rows}, 1fr)"
        if container_height:
            style += "; flex: 1; min-height: 0"
        else:
            style += f"; aspect-ratio: {g.columns} / {g.rows}"

        for c in view.cards:
            gl = c.grid_layout
            cell_style = ""
            if gl is not None:
                x = gl.x + 1
                y = gl.y + 1
                cell_style = f"grid-column: {x} / span {gl.width}; grid-row: {y} / span {gl.height}"

            cell_attrs = {"class": "grid-cell"}
            if cell_style:
                cell_attrs["style"] = cell_style

            card_content = _render_card(c, indent + 1)
            cards_html += "\n" + _SP * (indent + 1) + f"<div{_build_attrs(cell_attrs)}>\n"
            cards_html += card_content
            cards_html += "\n" + _SP * (indent + 1) + "</div>"

    if cards_html:
        cards_html += "\n" + _SP * indent

    return _h("div", {"class": "fixed-grid", "style": style}, cards_html, indent)


def _render_section(section: Section, indent: int = 2) -> str:
    cols = _section_col_count(section)
    style = f"--section-cols: {cols}"
    cards_html = ""
    for c in section.cards:
        go = c.get("grid_options")
        span_col = 0
        span_row = 0
        if isinstance(go, dict):
            span_col = go.get("columns", 0)
            span_row = go.get("rows", 0)
        if not isinstance(span_col, int):
            span_col = 0
        if not isinstance(span_row, int):
            span_row = 0
        cell_style = ""
        if span_col:
            cell_style += f"grid-column: span {min(span_col, cols)};"
        if span_row and isinstance(span_row, int) and span_row > 1:
            cell_style += f"grid-row: span {span_row};"
        cell_attrs = {"class": "grid-cell"}
        if cell_style:
            cell_attrs["style"] = cell_style
        card_content = _render_card(c, indent + 1)
        cards_html += "\n" + _SP * (indent + 1) + f'<div{_build_attrs(cell_attrs)}>\n'
        cards_html += card_content
        cards_html += '\n' + _SP * (indent + 1) + '</div>'
    if cards_html:
        cards_html += "\n" + _SP * indent
    return _h("div", {"class": "section-grid", "style": style}, cards_html, indent)


def _section_col_count(section: Section) -> int:
    max_col = section.columns if section.columns > 0 else 0
    for c in section.cards:
        go = c.get("grid_options")
        if isinstance(go, dict):
            span = go.get("columns", 0)
            if isinstance(span, int) and span > max_col:
                max_col = span
    return max(max_col, _DEFAULT_SECTION_COLUMNS)


def render_view_index(views: List[View], dashboard: Dashboard, dashboard_name: str = "") -> str:
    links = ""
    for v in views:
        href = _url(f"/d/{html.escape(dashboard_name)}/view/{html.escape(v.path)}") if dashboard_name else _url("/view/" + html.escape(v.path))
        links += '    <li><a href="' + href + '">'
        if v.icon:
            links += '<span class="vi">' + html.escape(v.icon) + "</span> "
        links += html.escape(v.title or v.path) + "</a></li>\n"
    return _TPL_VIEW_INDEX.substitute(
        css_link=_css_link(dashboard.lightdash.theme),
        sw_script=_SW_SCRIPT,
        links=links,
    )


def render_dashboard_index(dashboards: List[Dict[str, str]], theme: str = "") -> str:
    links = ""
    for d in dashboards:
        name = d.get("url_path", d.get("title", "?"))
        title = d.get("title", name)
        href = _url("/d/" + html.escape(name))
        links += '    <li><a href="' + href + '">' + html.escape(title) + " (" + html.escape(name) + ")</a></li>\n"
    return _TPL_DASH_INDEX.substitute(
        css_link=_css_link(theme),
        sw_script=_SW_SCRIPT,
        links=links,
    )


def render_error(message: str) -> str:
    msg = html.escape(message)
    return _TPL_ERROR.substitute(
        css_link=_css_link(),
        sw_script=_SW_SCRIPT,
        message=msg,
        home_url=_url("/"),
    )


def _view_needs_charts(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type in ("sensor", "history-graph", "statistics-graph"):
            return True
    return False


def _view_needs_toggle_sync(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "tile" and not c.get("hide_state"):
            eid = c.get("entity", "")
            if _is_binary_domain(eid):
                return True
        if c.type == "entities":
            ld_cfg = c.get("lightdash", {}) or {}
            show_toggle_card = not (isinstance(ld_cfg, dict) and ld_cfg.get("show_toggle") is False)
            if not show_toggle_card:
                continue
            for ent in (c.get("entities") or []):
                eid = ent if isinstance(ent, str) else (ent.get("entity", "") if isinstance(ent, dict) else "")
                if _is_binary_domain(eid) and eid.split(".")[0] != "cover":
                    if isinstance(ent, dict):
                        ent_ld = ent.get("lightdash", {}) or {}
                        if isinstance(ent_ld, dict) and ent_ld.get("show_toggle") is False:
                            continue
                    return True
    return False


def _view_needs_level_modal(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "tile":
            eid = c.get("entity", "")
            if eid.split(".")[0] in ("light", "fan"):
                return True
        if c.type == "entities":
            for ent in (c.get("entities") or []):
                eid = ent if isinstance(ent, str) else (ent.get("entity", "") if isinstance(ent, dict) else "")
                if eid.split(".")[0] in ("light", "fan"):
                    return True
    return False


def _view_needs_cover_modal(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "tile":
            eid = c.get("entity", "")
            if eid.split(".")[0] == "cover":
                return True
        if c.type == "entities":
            for ent in (c.get("entities") or []):
                eid = ent if isinstance(ent, str) else (ent.get("entity", "") if isinstance(ent, dict) else "")
                if eid.split(".")[0] == "cover":
                    return True
    return False


def _view_needs_climate_modal(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "tile":
            eid = c.get("entity", "")
            if eid.split(".")[0] == "climate":
                return True
        if c.type == "entities":
            for ent in (c.get("entities") or []):
                eid = ent if isinstance(ent, str) else (ent.get("entity", "") if isinstance(ent, dict) else "")
                if eid.split(".")[0] == "climate":
                    return True
    return False


def _view_needs_slider_sync(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "tile":
            for f in (c.get("features") or []):
                if isinstance(f, dict) and f.get("type") in ("light-brightness", "light-color-temp"):
                    return True
    return False


def _view_needs_clock(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "clock":
            return True
    return False


def _view_needs_fit_text(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "clock":
            size = str(c.get("clock_size", "") or "")
            if size == "fit" or size.startswith("fit "):
                return True
            ld = c.get("lightdash", {}) or {}
            if isinstance(ld, dict):
                dfs = str(ld.get("date_fontsize", "") or "")
                if dfs == "fit" or dfs.startswith("fit "):
                    return True
    return False


def _view_needs_alarm_panel(view: View) -> bool:
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        if c.type == "alarm-panel":
            return True
    return False


# ---- Badge Renderers -----------------------------------------------------


def _render_badges(view: View) -> str:
    if not view.badges:
        return ""
    items = ""
    for i, badge in enumerate(view.badges):
        btype = badge.get("type", "entity")
        if btype == "entity":
            items += _render_entity_badge(badge)
        elif btype == "shortcut":
            items += _render_shortcut_badge(badge)
        elif btype == "entity-filter":
            items += _render_entity_filter_badge(badge, i, view.path)
    if not items:
        return ""
    return '<div class="badges-bar">\n' + items + '</div>\n'


def _render_entity_badge(badge: dict) -> str:
    eid = badge.get("entity", "")
    if not eid:
        return ""
    icon = _icon_html(_entity_icon(eid, badge.get("icon", "")), 16)
    name = html.escape(badge.get("name", _friendly_name(eid)))
    state_span = _entity_span(eid)
    attrs: Dict[str, str] = {"class": "badge entity-badge"}
    if _is_binary_domain(eid):
        dom = eid.split(".")[0]
        svc = _domain_toggle_service(dom)
        attrs["hx-post"] = _url("/action")
        attrs["hx-trigger"] = "click"
        attrs["hx-vals"] = _js_obj(entity_id=eid, action="toggle", service=svc)
        attrs["hx-swap"] = "none"
    content = '<span class="badge-icon">' + icon + '</span><span class="badge-name">' + name + '</span>' + state_span
    return _h("div", attrs, content, 2)


def _render_shortcut_badge(badge: dict) -> str:
    icon = _icon_html(badge.get("icon", ""), 16)
    label = html.escape(badge.get("label", ""))
    attrs: Dict[str, str] = {"class": "badge shortcut-badge"}
    ta = badge.get("tap_action", {})
    if isinstance(ta, dict):
        a = Action(**{k: v for k, v in ta.items() if k in Action.__dataclass_fields__})
        if a.action == "navigate":
            path = _url("/d/" + html.escape(_dashboard_name) + "/view/" + html.escape(a.navigation_path))
            attrs["hx-get"] = path
            attrs["hx-target"] = "body"
            attrs["hx-push-url"] = "true"
            attrs["hx-trigger"] = "click"
        elif a.action == "url":
            attrs["onclick"] = "window.open('" + html.escape(a.url_path) + "','_blank')"
    content = '<span class="badge-icon">' + icon + '</span><span class="badge-name">' + label + '</span>'
    return _h("div", attrs, content, 2)


def _render_entity_filter_badge(badge: dict, idx: int, view_path: str) -> str:
    eid = badge.get("entity", "")
    conditions = badge.get("conditions", [])
    if not _filter_entity_matches(eid, conditions):
        return ""
    icon = _icon_html(_entity_icon(eid, badge.get("icon", "")), 16)
    name = html.escape(badge.get("name", _friendly_name(eid)))
    safe_dash = html.escape(_dashboard_name)
    safe_path = html.escape(view_path)
    attrs: Dict[str, str] = {
        "class": "badge entity-filter-badge",
        "id": f"badge-{idx}",
        "hx-get": _url(f"/api/view/{safe_dash}/{safe_path}/badge/{idx}"),
        "hx-trigger": f"sse:entity_{eid.replace('.', '_')}",
        "hx-swap": "outerHTML",
    }
    content = '<span class="badge-icon">' + icon + '</span><span class="badge-name">' + name + '</span>'
    return _h("div", attrs, content, 2)


def _filter_entity_matches(entity_id: str, conditions: list) -> bool:
    if not conditions:
        return True
    for cond in conditions:
        if not isinstance(cond, dict):
            continue
        cond_entity = cond.get("entity", "")
        cond_state = cond.get("state", "")
        if not cond_entity:
            continue
        state = _entity_states.get(cond_entity, {})
        actual = state.get("state", "")
        if actual.lower() != cond_state.lower():
            return False
    return True


def _render_card(card: Card, indent: int = 2) -> str:
    renderer = RENDERERS.get(card.type)
    if renderer is None:
        return _render_placeholder(card, indent)
    out = renderer(card, indent)
    if out is None:
        return _render_placeholder(card, indent)
    return out


def _h(tag: str, attrs: Dict[str, str], content: str = "", indent: int = 0) -> str:
    indent_str = _SP * indent
    attr_str = _build_attrs(attrs)
    self_closing = {"input", "br", "hr", "img", "meta", "link"}
    if tag in self_closing and not content:
        return indent_str + "<" + tag + attr_str + ">"
    return indent_str + "<" + tag + attr_str + ">" + content + "</" + tag + ">"


def _build_attrs(attrs: Dict[str, str]) -> str:
    if not attrs:
        return ""
    parts = []
    for k, v in attrs.items():
        if v is None or v is False:
            continue
        if v is True:
            parts.append(k)
        else:
            sv = str(v)
            escaped = sv.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(k + '="' + escaped + '"')
    return " " + " ".join(parts) if parts else ""


def _format_entity_state(entity_id: str) -> Optional[str]:
    state = _entity_states.get(entity_id)
    if not state:
        return None
    val = state.get("state", "")
    unit = state.get("attributes", {}).get("unit_of_measurement", "")
    return f"{val} {unit}" if unit else str(val)


def _icon_color_for_state(entity_id: str) -> str:
    state = _entity_states.get(entity_id)
    if not state:
        return ""
    state_val = state.get("state", "")
    if state_val == "off":
        return "#DDDDDD"
    if state_val == "on":
        brightness = state.get("attributes", {}).get("brightness")
        if brightness is not None:
            ratio = max(0, min(255, int(brightness))) / 255.0
            r = int(221 + (246 - 221) * ratio)
            g = int(221 + (195 - 221) * ratio)
            b = int(221 + (68 - 221) * ratio)
            return f"#{r:02x}{g:02x}{b:02x}"
        return "#F6C344"
    return ""


def _entity_span(entity_id: str, card_id: str = "", indent: int = 0) -> str:
    sid = html.escape(entity_id)
    display = _format_entity_state(entity_id)
    state = _entity_states.get(entity_id)
    attrs: Dict[str, str] = {
        "class": "entity-state",
        "id": f"state-{sid}",
        "data-entity": entity_id,
    }
    if display is None:
        attrs["hx-get"] = _url(f"/api/value/{sid}")
        attrs["hx-trigger"] = "load"
    else:
        brightness = state.get("attributes", {}).get("brightness") if state else None
        if brightness is not None:
            pct = max(0, min(255, int(brightness))) * 100 // 255
            attrs["data-brightness"] = str(brightness)
            attrs["style"] = f"--b: {pct}"
    attrs["hx-swap"] = "innerHTML"
    attrs["hx-target"] = "this"
    sse_event = "entity_" + entity_id.replace(".", "_")
    attrs["sse-swap"] = sse_event
    return _h("span", attrs, html.escape(display) if display is not None else "", indent)


def _prefetch_icons(view: View) -> None:
    needed = set()
    check_cards = view.cards
    if view.sections:
        check_cards = [c for s in view.sections for c in s.cards]
    for c in check_cards:
        eid = c.get("entity", "")
        icon = _entity_icon(eid, c.get("icon", ""))
        if icon:
            needed.add(icon.removeprefix("mdi:"))
        if c.type == "weather-forecast":
            for cond_icon in _WEATHER_CONDITION_ICONS.values():
                needed.add(cond_icon)
        if c.type == "alarm-panel":
            for alarm_icon in (
                "shield-off", "shield-home", "shield-lock", "shield-moon",
                "shield-airplane", "shield-check", "bell-ring", "shield-sync",
                "shield-alert", "backspace-outline", "close", "alert",
            ):
                needed.add(alarm_icon)
        if c.type in ("entities", "glance"):
            for ent in (c.get("entities") or []):
                if isinstance(ent, str):
                    eeid = ent
                    eicon = ""
                elif isinstance(ent, dict):
                    eeid = ent.get("entity", "")
                    eicon = ent.get("icon", "")
                else:
                    continue
                resolved = _entity_icon(eeid, eicon)
                if resolved:
                    needed.add(resolved.removeprefix("mdi:"))
    uncached = [n for n in needed if n not in _icon_svg_cache]
    if not uncached or not _ha_url:
        return
    logger.info("Prefetching %d uncached icons", len(uncached))
    base = "https://cdn.jsdelivr.net/npm/@mdi/svg@7.4.47/svg/"
    with httpx.Client(timeout=10) as hx:
        for name in uncached:
            try:
                r = hx.get(base + name + ".svg")
                if r.status_code == 200:
                    _icon_svg_cache[name] = r.text
                else:
                    logger.warning("Icon fetch failed %s: HTTP %d", name, r.status_code)
            except Exception as e:
                logger.warning("Icon fetch error %s: %s", name, e)
    while len(_icon_svg_cache) > _ICON_CACHE_MAX:
        _icon_svg_cache.pop(next(iter(_icon_svg_cache)), None)


def _icon_html(icon: str, size: int = 24) -> str:
    if not icon:
        return ""
    name = icon.removeprefix("mdi:")
    svg = _icon_svg_cache.get(name)
    if not svg:
        return ""
    extra = 'class="icon" width="' + str(size) + '" height="' + str(size) + '"'
    if 'fill="currentColor"' not in svg and 'fill="none"' not in svg:
        extra += ' fill="currentColor"'
    svg = svg.replace("<svg", "<svg " + extra, 1)
    return svg


def _entity_icon(entity_id: str, config_icon: str) -> str:
    if config_icon:
        return config_icon
    if entity_id in _entity_icons:
        return _entity_icons[entity_id]
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    return _DEFAULT_ICONS.get(domain, "")


def _js_obj(**kwargs) -> str:
    items = []
    for k, v in kwargs.items():
        if isinstance(v, str):
            items.append(f"{k}: '{v}'")
        elif isinstance(v, (int, float)):
            items.append(f"{k}: {v}")
        elif v is None:
            items.append(f"{k}: null")
        elif isinstance(v, bool):
            items.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, (dict, list)):
            items.append(f"{k}: {json.dumps(v)}")
    return "js:{" + ", ".join(items) + "}"


def _tap_action_attrs(card: Card) -> Dict[str, str]:
    raw = card.get("tap_action")
    if not raw or not isinstance(raw, dict):
        return {}
    a = Action(**{k: v for k, v in raw.items() if k in Action.__dataclass_fields__})
    if a.action == "toggle":
        eid = card.get("entity", "")
        domain = eid.split(".")[0] if "." in eid else ""
        svc = _domain_toggle_service(domain)
        return {
            "hx-post": _url("/action"),
            "hx-trigger": "click",
            "hx-vals": _js_obj(entity_id=eid, action="toggle", service=svc),
            "hx-swap": "none",
        }
    if a.action == "call-service":
        target = a.target or {}
        return {
            "hx-post": _url("/action"),
            "hx-trigger": "click",
            "hx-vals": _js_obj(action="call-service", service=a.service, target=target, data=a.data or {}),
            "hx-swap": "none",
        }
    if a.action == "navigate":
        path = _url("/d/" + html.escape(_dashboard_name) + "/view/" + html.escape(a.navigation_path))
        return {"hx-get": path, "hx-target": "body", "hx-push-url": "true", "hx-trigger": "click"}
    if a.action == "url":
        return {"onclick": "window.open('" + html.escape(a.url_path) + "','_blank')"}
    return {}


def _action_attrs(entity_id: str, action: str) -> Dict[str, str]:
    service = ""
    if action == "toggle" and entity_id:
        domain = entity_id.split(".")[0] if "." in entity_id else ""
        service = _domain_toggle_service(domain)
    return {
        "hx-post": _url("/action"),
        "hx-trigger": "click",
        "hx-vals": _js_obj(entity_id=entity_id, action=action, service=service),
        "hx-swap": "none",
    }


def _domain_toggle_service(domain: str) -> str:
    mapping = {
        "light": "light.toggle",
        "switch": "switch.toggle",
        "fan": "fan.toggle",
        "cover": "cover.toggle",
        "lock": "lock.lock",
        "input_boolean": "input_boolean.toggle",
        "scene": "scene.turn_on",
        "script": "script.turn_on",
        "automation": "automation.toggle",
        "climate": "climate.toggle",
        "media_player": "media_player.media_play_pause",
    }
    return mapping.get(domain, domain + ".toggle")


_BINARY_DOMAINS = frozenset({
    "light", "switch", "fan", "input_boolean", "cover",
    "lock", "scene", "script", "automation",
})


def _is_binary_domain(entity_id: str) -> bool:
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    return domain in _BINARY_DOMAINS


def _color_icon(color: str) -> str:
    if not color:
        return ""
    color_map = {
        "yellow": "#FFB300",
        "orange": "#FF6D00",
        "red": "#D32F2F",
        "pink": "#E91E63",
        "purple": "#9C27B0",
        "blue": "#2196F3",
        "green": "#4CAF50",
        "teal": "#009688",
    }
    return color_map.get(color.lower(), color)


# ---- Card Renderers -------------------------------------------------------


def _alarm_sensor_badges(sensors: dict, indent: int = 0) -> str:
    istr = _SP * indent
    lines = []
    for eid, sdata in (sensors.items() if isinstance(sensors, dict) else []):
        sname = ""
        sstate = ""
        if isinstance(sdata, dict):
            sname = sdata.get("name", eid) or eid
            sstate = sdata.get("state", "") or ""
        else:
            sname = str(sdata) or eid
        icon = _entity_icon(eid, "")
        icon_html = _icon_html(icon) if icon else ""
        lines.append(
            istr + '<span class="alarm-sensor-badge">'
            + (icon_html if icon_html else "")
            + '<span>' + html.escape(sname)
            + (' \u2014 ' + html.escape(sstate) if sstate else "")
            + '</span></span>'
        )
    return "\n".join(lines)


def _alarm_bypassed_badges(sensors: list, indent: int = 0) -> str:
    istr = _SP * indent
    lines = []
    for eid in (sensors or []):
        eid_s = str(eid)
        sname = ""
        st = _entity_states.get(eid_s, {})
        if st:
            sname = st.get("attributes", {}).get("friendly_name", eid_s)
        else:
            sname = eid_s
        lines.append(
            istr + '<span class="alarm-sensor-badge">'
            + '<span>' + html.escape(sname if sname else eid_s) + '</span>'
            + '</span>'
        )
    return "\n".join(lines)


@register("alarm-panel")
def _render_alarm_panel(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    if not eid:
        return _render_placeholder(card, indent)
    state_obj = _entity_states.get(eid, {})
    current_state = state_obj.get("state", "unknown")
    attrs = state_obj.get("attributes", {})
    name = card.get("name") or attrs.get("friendly_name", eid)
    sc = card.get("states", {}) or {}
    show_keypad = card.get("show_keypad", True)
    show_messages = card.get("show_messages", True)
    show_bypassed_sensors = card.get("show_bypassed_sensors", True)
    state_colors = {
        "disarmed": "#4CAF50",
        "armed_home": "#F44336", "armed_away": "#F44336",
        "armed_night": "#F44336", "armed_vacation": "#F44336",
        "armed_custom_bypass": "#F44336",
        "triggered": "#FF0000", "arming": "#FF9800", "pending": "#FF9800",
    }
    state_icons = {
        "disarmed": "mdi:shield-off",
        "armed_home": "mdi:shield-home", "armed_away": "mdi:shield-lock",
        "armed_night": "mdi:shield-moon", "armed_vacation": "mdi:shield-airplane",
        "armed_custom_bypass": "mdi:shield-check",
        "triggered": "mdi:bell-ring", "arming": "mdi:shield-sync", "pending": "mdi:shield-alert",
    }
    state_labels = {
        "disarmed": "Disarmed",
        "armed_home": "Armed Home", "armed_away": "Armed Away",
        "armed_night": "Armed Night", "armed_vacation": "Armed Vacation",
        "armed_custom_bypass": "Armed Custom",
        "triggered": "Triggered",
        "arming": "Arming\u2026", "pending": "Pending\u2026",
    }
    mode_icons = {
        "armed_away": "mdi:shield-lock", "armed_home": "mdi:shield-home",
        "armed_night": "mdi:shield-moon", "armed_vacation": "mdi:shield-airplane",
        "armed_custom_bypass": "mdi:shield-check",
    }
    mode_labels = {
        "armed_away": "Away", "armed_home": "Home", "armed_night": "Night",
        "armed_vacation": "Vacation", "armed_custom_bypass": "Bypass",
    }
    for m in mode_labels:
        ms = sc.get(m, {}) or {}
        if ms.get("button_label"):
            mode_labels[m] = ms["button_label"]
        if ms.get("button_icon"):
            mode_icons[m] = ms["button_icon"]
    stc = sc.get(current_state, {}) or {}
    if stc.get("state_label"):
        state_labels[current_state] = stc["state_label"]
    if stc.get("color"):
        state_colors[current_state] = stc["color"]
    color = state_colors.get(current_state, "#888")
    icon = state_icons.get(current_state, "mdi:shield-alert")
    label = state_labels.get(current_state, current_state)
    i = _SP * indent

    # Header — centred: icon badge, name, state label
    header = (
        i + _SP + '<div class="alarm-header">\n'
        + i + _SP * 2 + '<div class="alarm-badge">' + _icon_html(icon) + '</div>\n'
        + i + _SP * 2 + '<div class="alarm-name">' + html.escape(str(name)) + '</div>\n'
        + i + _SP * 2 + '<div class="alarm-state">' + html.escape(str(label)) + '</div>\n'
        + i + _SP + '</div>'
    )

    # Diagnostic messages
    messages = ""
    if show_messages:
        open_sensors = attrs.get("open_sensors", {})
        bypassed = attrs.get("bypassed_sensors", [])
        if current_state == "triggered" and open_sensors:
            badges = _alarm_sensor_badges(open_sensors, indent + 3)
            messages += (
                i + _SP + '<div class="alarm-messages">\n'
                + i + _SP * 2 + _icon_html("mdi:alert", 16) + '<span>Triggered by:</span>\n'
                + badges + '\n'
                + i + _SP + '</div>\n'
            )
        elif open_sensors and current_state == "disarmed":
            badges = _alarm_sensor_badges(open_sensors, indent + 3)
            messages += (
                i + _SP + '<div class="alarm-messages">\n'
                + i + _SP * 2 + _icon_html("mdi:alert", 16) + '<span>Sensors blocking arm:</span>\n'
                + badges + '\n'
                + i + _SP + '</div>\n'
            )
        if show_bypassed_sensors and bypassed and current_state.startswith("armed_"):
            badges = _alarm_bypassed_badges(bypassed, indent + 3)
            messages += (
                i + _SP + '<div class="alarm-messages bypassed">\n'
                + i + _SP * 2 + _icon_html("mdi:alert", 16) + '<span>Bypassed sensors active</span>\n'
                + badges + '\n'
                + i + _SP + '</div>\n'
            )

    # Action buttons
    actions = ""
    if current_state == "disarmed" or current_state == "triggered":
        buttons = []
        default_modes = [
            ("armed_away", 1), ("armed_home", 2), ("armed_night", 3),
            ("armed_vacation", 4), ("armed_custom_bypass", 5),
        ]
        for mode, dflt in default_modes:
            ms = sc.get(mode, {}) or {}
            if ms.get("hide"):
                continue
            order = ms.get("button_order", dflt)
            btn_label = ms.get("button_label") or mode_labels.get(mode, mode)
            btn_icon = ms.get("button_icon") or mode_icons.get(mode, "")
            ihtml = _icon_html(btn_icon) if btn_icon else ""
            buttons.append((order, mode, btn_label, ihtml))
        buttons.sort(key=lambda b: b[0])
        for _, mode, btn_label, ihtml in buttons:
            actions += (
                i + _SP * 2
                + '<button type="submit" name="action" value="' + html.escape(mode) + '" class="alarm-action-btn">'
                + (ihtml + '<span>' + html.escape(btn_label) + '</span>' if ihtml else '<span>' + html.escape(btn_label) + '</span>')
                + '</button>\n'
            )
    else:
        ds = sc.get("disarmed", {}) or {}
        dlabel = ds.get("button_label") or "Disarm"
        dicon = _icon_html(ds.get("button_icon") or "mdi:shield-off")
        actions = (
            i + _SP * 2
            + '<button type="submit" name="action" value="disarm" class="alarm-action-btn disarm">'
            + dicon + '<span>' + html.escape(dlabel) + '</span>'
            + '</button>\n'
        )
    if actions:
        actions = i + _SP + '<div class="alarm-actions">\n' + actions + i + _SP + '</div>\n'

    # Code section — dot indicators + text input (hidden when keypad shown)
    safe_id = eid.replace(".", "-")
    input_cls = "alarm-code-input-field hidden" if show_keypad else "alarm-code-input-field"
    code_section = (
        _h("input", {"type": "hidden", "name": "code", "class": "alarm-code-hidden", "id": "alarm-code-" + safe_id, "value": ""}, "", indent + 1)
        + '\n' + i + _SP + '<div class="alarm-code-section">\n'
        + i + _SP * 2 + '<div class="alarm-code-dots"></div>\n'
        + i + _SP * 2 + '<input type="password" class="' + input_cls + '" placeholder="Enter code" inputmode="numeric">\n'
        + i + _SP + '</div>'
    )

    keypad = ""
    if show_keypad:
        # Classic 3-column numpad: 1-9, then 0, backspace, clear
        keys = ["1","2","3","4","5","6","7","8","9","0","backspace","clear"]
        kbtns = ""
        for k in keys:
            if k == "backspace":
                inner = _icon_html("mdi:backspace-outline")
            elif k == "clear":
                inner = _icon_html("mdi:close")
            else:
                inner = '<span>' + k + '</span>'
            kbtns += i + _SP * 2 + '<button type="button" class="alarm-key" data-digit="' + k + '">' + inner + '</button>\n'
        keypad = i + _SP + '<div class="alarm-keypad">\n' + kbtns + i + _SP + '</div>\n'

    # Arming options (disarmed only)
    options = ""
    if current_state == "disarmed":
        skip_checked = ' checked' if card.get("skip_delay", False) else ""
        force_checked = ' checked' if card.get("force", False) else ""
        options = (
            i + _SP + '<div class="alarm-options">\n'
            + i + _SP * 2 + '<label class="alarm-option"><input type="checkbox" name="skip_delay" value="true"' + skip_checked + '> Skip exit delay</label>\n'
            + i + _SP * 2 + '<label class="alarm-option"><input type="checkbox" name="force" value="true"' + force_checked + '> Bypass open sensors</label>\n'
            + i + _SP + '</div>\n'
        )

    api_url = _url("/api/alarm-action/" + html.escape(_dashboard_name) + "/" + html.escape(_view_path))
    card_url = _url("/api/alarm-card/" + html.escape(_dashboard_name) + "/" + html.escape(_view_path) + "?entity=" + html.escape(eid))
    sse_event = "entity_" + eid.replace(".", "_")
    hidden_eid = _h("input", {"type": "hidden", "name": "entity_id", "value": eid}, "", indent + 2)
    return (
        i + '<div class="alarm-panel-wrap"'
        + ' hx-get="' + card_url + '"'
        + ' hx-trigger="sse:' + sse_event + '"'
        + ' hx-swap="outerHTML">\n'
        + i + _SP + '<form class="alarm-panel"'
        + ' hx-post="' + api_url + '" hx-swap="outerHTML" hx-target="closest .alarm-panel-wrap">\n'
        + i + _SP * 2 + '<div class="alarm-card" style="--alarm-color:' + color + '">\n'
        + hidden_eid + '\n'
        + header + '\n'
        + messages
        + actions
        + code_section + '\n'
        + keypad
        + options
        + i + _SP * 2 + '</div>\n'
        + i + _SP + '</form>\n'
        + i + '</div>'
    )


@register("placeholder")
def _render_placeholder(card: Card, indent: int = 2) -> str:
    return _h("div", {"class": "ha-card placeholder-card"}, "?", indent)


@register("heading")
def _render_heading(card: Card, indent: int = 2) -> str:
    text = html.escape(card.get("heading", ""))
    icon = _icon_html(card.get("icon", ""), 20)
    content = icon + '<h2 class="heading-text">' + text + "</h2>" if icon else '<h2 class="heading-text">' + text + "</h2>"
    return _h("div", {"class": "heading-card"}, content, indent)


@register("markdown")
def _render_markdown(card: Card, indent: int = 2) -> str:
    content = card.get("content", "")
    if JINJA_RE.search(content):
        return _render_placeholder(card, indent)
    rendered = _render_markdown_text(content)
    return _h("div", {"class": "ha-card markdown-card"}, rendered, indent)


@register("entity")
def _render_entity(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    name = html.escape(card.get("name", _friendly_name(eid)))
    icon = _icon_html(_entity_icon(eid, card.get("icon", "")), 20)
    state_span = _entity_span(eid, indent=indent + 2)
    icon_cell = '<div class="entity-icon">' + icon + "</div>" if icon else ""
    attrs: Dict[str, str] = {"class": "ha-card entity-card"}
    state_color = _icon_color_for_state(eid) if eid else ""
    if state_color:
        attrs["style"] = "--state-color: " + state_color
    ta = _tap_action_attrs(card)
    attrs.update(ta)
    content = (
        '\n' + _SP * (indent + 1) + '<div class="entity-row">\n'
        + _SP * (indent + 2) + icon_cell + '\n'
        + _SP * (indent + 2) + '<div class="entity-info">\n'
        + _SP * (indent + 3) + '<div class="entity-name">' + name + '</div>\n'
        + _SP * (indent + 3) + state_span + '\n'
        + _SP * (indent + 2) + '</div>\n'
        + _SP * (indent + 1) + '</div>\n'
        + _SP * indent
    )
    return _h("div", attrs, content, indent)


@register("entities")
def _render_entities(card: Card, indent: int = 2) -> str:
    title = html.escape(card.get("title", ""))
    raw_entities = card.get("entities", [])
    rows = ""
    ld_cfg = card.get("lightdash", {}) or {}
    show_toggle_card = not (isinstance(ld_cfg, dict) and ld_cfg.get("show_toggle") is False)
    for i, ent in enumerate(raw_entities):
        if isinstance(ent, str):
            eid = ent
            ename = _friendly_name(eid)
            eicon = ""
        elif isinstance(ent, dict):
            eid = ent.get("entity", "")
            ename = ent.get("name", _friendly_name(eid))
            eicon = ent.get("icon", "")
        else:
            continue
        icon_hidden = eicon == "none"
        icon = "" if icon_hidden else _icon_html(_entity_icon(eid, eicon), 18)
        state_span = _entity_span(eid, indent=indent + 3)
        type_attr = ent.get("type", "") if isinstance(ent, dict) else ""
        divider = ""
        if type_attr == "divider":
            rows += _SP * (indent + 1) + '<hr class="entities-divider">\n'
            continue
        if type_attr == "section":
            section = html.escape(ent.get("name", "") if isinstance(ent, dict) else "")
            rows += _SP * (indent + 1) + '<div class="entities-section-header">' + section + '</div>\n'
            continue
        show_toggle = show_toggle_card
        if show_toggle and isinstance(ent, dict):
            ent_ld = ent.get("lightdash", {}) or {}
            if isinstance(ent_ld, dict) and ent_ld.get("show_toggle") is False:
                show_toggle = False
        row_controls = _render_cover_controls(eid, indent + 2)
        if show_toggle:
            row_controls = row_controls or _render_entity_toggle(eid, indent + 2)
        features_html = ""
        if isinstance(ent, dict):
            ent_features = ent.get("features", [])
            if ent_features:
                features_html = "\n" + _render_features(ent, indent + 2)
        row_attrs: Dict[str, str] = {"class": "entity-row" + (" no-icon" if icon_hidden else "")}
        state_color = _icon_color_for_state(eid) if eid else ""
        if state_color:
            row_attrs["style"] = "--state-color: " + state_color
        if eid and "." in eid:
            if eid.split(".")[0] == "light":
                row_attrs["data-light-entity"] = eid
            elif eid.split(".")[0] == "fan":
                row_attrs["data-fan-entity"] = eid
            elif eid.split(".")[0] == "cover":
                row_attrs["data-cover-entity"] = eid
            elif eid.split(".")[0] == "climate":
                row_attrs["data-climate-entity"] = eid
        if isinstance(ent, dict):
            ld = ent.get("lightdash", {}) or {}
            if isinstance(ld, dict):
                fav_vals = ld.get("favourite_values", []) or []
                if isinstance(fav_vals, list):
                    valid = [str(int(v)) for v in fav_vals[:4] if isinstance(v, (int, float)) and 0 <= v <= 100]
                    if valid:
                        row_attrs["data-fav-vals"] = ",".join(valid)
        if show_toggle and _is_binary_domain(eid) and eid.split(".")[0] != "cover":
            dom = eid.split(".")[0]
            svc = _domain_toggle_service(dom)
            row_attrs.update({
                "hx-post": _url("/action"),
                "hx-trigger": "click",
                "hx-vals": _js_obj(entity_id=eid, action="toggle", service=svc),
                "hx-swap": "none",
            })
        rows += (
            _SP * (indent + 1) + '<div' + _build_attrs(row_attrs) + '>\n'
            + ('' if icon_hidden else _SP * (indent + 2) + '<div class="entity-icon">' + icon + '</div>\n')
            + _SP * (indent + 2) + '<div class="entity-info">\n'
            + _SP * (indent + 3) + '<div class="entity-name">' + html.escape(ename) + '</div>\n'
            + _SP * (indent + 3) + state_span + '\n'
            + _SP * (indent + 2) + '</div>\n'
            + row_controls
            + features_html
            + _SP * (indent + 1) + '</div>\n'
        )

    header = ""
    if title:
        header = _SP * (indent + 1) + '<div class="entities-header">' + title + '</div>\n'

    content = "\n" + header + rows + _SP * indent
    return _h("div", {"class": "ha-card entities-card"}, content, indent)


@register("glance")
def _render_glance(card: Card, indent: int = 2) -> str:
    title = html.escape(card.get("title", ""))
    columns = card.get("columns", 3)
    raw_entities = card.get("entities", [])
    items = ""
    for ent in raw_entities:
        if isinstance(ent, str):
            eid = ent
            ename = _friendly_name(eid)
            eicon = ""
        elif isinstance(ent, dict):
            eid = ent.get("entity", "")
            ename = ent.get("name", _friendly_name(eid))
            eicon = ent.get("icon", "")
        else:
            continue
        icon = _icon_html(_entity_icon(eid, eicon), 20)
        state_span = _entity_span(eid, indent=indent + 3)
        ta_attrs = ""
        style_attr = ""
        state_color = _icon_color_for_state(eid) if eid else ""
        if state_color:
            style_attr = ' style="--state-color: ' + state_color + '"'
        if isinstance(ent, dict) and ent.get("tap_action"):
            e_card = Card(type="glance_item", config=ent)
            ta = _tap_action_attrs(e_card)
            ta_attrs = _build_attrs(ta)
        items += (
            _SP * (indent + 1) + '<div class="glance-item"' + ta_attrs + style_attr + '>\n'
            + _SP * (indent + 2) + '<div class="glance-icon">' + icon + '</div>\n'
            + _SP * (indent + 2) + '<div class="glance-name">' + html.escape(ename) + '</div>\n'
            + _SP * (indent + 2) + state_span + '\n'
            + _SP * (indent + 1) + '</div>\n'
        )

    header = ""
    if title:
        header = _SP * (indent + 1) + '<div class="glance-header">' + title + '</div>\n'

    content = "\n" + header + items + _SP * indent
    return _h("div", {"class": "ha-card glance-card", "style": "--cols: " + str(columns)}, content, indent)


@register("button")
def _render_button(card: Card, indent: int = 2) -> str:
    name = html.escape(card.get("name", card.get("entity", "Action")))
    eid = card.get("entity", "")
    icon = _icon_html(_entity_icon(eid, card.get("icon", "")), 28)
    state_color = _icon_color_for_state(eid) if eid else ""
    style_attr = ' style="--state-color: ' + state_color + '"' if state_color else ""
    ta_attrs = _tap_action_attrs(card)

    if not ta_attrs and card.get("entity"):
        ta_attrs = _action_attrs(card.get("entity", ""), "toggle")

    content = (
        '\n' + _SP * (indent + 1) + '<button class="button-content"' + _build_attrs(ta_attrs) + style_attr + '>\n'
        + _SP * (indent + 2) + '<div class="button-icon">' + icon + '</div>\n'
        + _SP * (indent + 2) + '<div class="button-name">' + name + '</div>\n'
        + _SP * (indent + 1) + '</button>\n'
        + _SP * indent
    )
    return _h("div", {"class": "ha-card button-card"}, content, indent)


@register("tile")
def _render_tile(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    name = html.escape(card.get("name", _friendly_name(eid)))
    icon = _icon_html(_entity_icon(eid, card.get("icon", "")), 24)
    color = _color_icon(card.get("color", ""))
    vertical = card.get("vertical", False)
    hide_state = card.get("hide_state", False)
    features_inline = card.get("features_position", "") == "inline"

    attrs: Dict[str, str] = {"class": "ha-card tile-card"}
    if hide_state:
        attrs["class"] += " hide-state"
    if color:
        attrs["style"] = "--tile-color: " + color
    elif eid:
        state_color = _icon_color_for_state(eid)
        if state_color:
            attrs["style"] = "--tile-color: " + state_color
    if eid and "." in eid:
        if eid.split(".")[0] == "light":
            attrs["data-light-entity"] = eid
        elif eid.split(".")[0] == "fan":
            attrs["data-fan-entity"] = eid
        elif eid.split(".")[0] == "cover":
            attrs["data-cover-entity"] = eid
        elif eid.split(".")[0] == "climate":
            attrs["data-climate-entity"] = eid
    ld = card.get("lightdash", {}) or {}
    if isinstance(ld, dict):
        fav_vals = ld.get("favourite_values", []) or []
        if isinstance(fav_vals, list):
            valid = [str(int(v)) for v in fav_vals[:4] if isinstance(v, (int, float)) and 0 <= v <= 100]
            if valid:
                attrs["data-fav-vals"] = ",".join(valid)

    is_binary = _is_binary_domain(eid)
    is_cover = eid.split(".")[0] == "cover" if "." in eid else False
    state_html = ""
    if is_binary and not is_cover:
        dom = eid.split(".")[0] if "." in eid else ""
        svc = _domain_toggle_service(dom)
        toggle_attrs = {
            "hx-post": _url("/action"),
            "hx-trigger": "change",
            "hx-vals": _js_obj(entity_id=eid, action="toggle", service=svc),
            "hx-swap": "none",
        }
        span = _entity_span(eid, indent=indent + 2)
        state_html = span
        if not hide_state:
            state_html = (
                '<label class="toggle-switch" onclick="event.stopPropagation()">'
                '<input type="checkbox" class="toggle-input" ' + _build_attrs(toggle_attrs) + '>'
                '<span class="toggle-slider"></span>'
                '</label>'
                + span
            )
    elif is_cover and not hide_state:
        state_html = _entity_span(eid, indent=indent + 2)
    elif not hide_state:
        state_html = _entity_span(eid, indent=indent + 2)

    ta_attrs = _tap_action_attrs(card)

    if not ta_attrs and eid and not is_cover:
        ta_attrs = _action_attrs(eid, "toggle")

    tc_class = "tile-content" + (" vertical" if vertical else "")

    has_features = bool(card.get("features"))
    features_html = ""
    if has_features:
        features_html = "\n" + _render_features(card, indent + 1) + "\n" + _SP * indent

    if features_inline and has_features:
        inline_html = _render_features(card, indent + 3, inline=True)
        content = (
            '\n'
            + _SP * (indent + 1) + '<div class="' + tc_class + '"' + _build_attrs(ta_attrs) + '>\n'
            + _SP * (indent + 2) + '<div class="tile-icon">' + icon + '</div>\n'
            + _SP * (indent + 2) + '<div class="tile-info tile-info-inline">\n'
            + _SP * (indent + 3) + '<div class="tile-name">' + name + '</div>\n'
            + inline_html + '\n'
            + _SP * (indent + 2) + '</div>\n'
            + _SP * (indent + 1) + '</div>\n'
            + _SP * indent
        )
    elif is_cover and not hide_state:
        cover_html = _render_cover_controls(eid, indent + 3)
        content = (
            '\n'
            + _SP * (indent + 1) + '<div class="' + tc_class + '"' + _build_attrs(ta_attrs) + '>\n'
            + _SP * (indent + 2) + '<div class="tile-icon">' + icon + '</div>\n'
            + _SP * (indent + 2) + '<div class="tile-info tile-info-inline">\n'
            + _SP * (indent + 3) + '<div class="tile-name">' + name + '</div>\n'
            + _SP * (indent + 3) + state_html + '\n'
            + cover_html + '\n'
            + _SP * (indent + 2) + '</div>\n'
            + _SP * (indent + 1) + '</div>\n'
            + _SP * indent
        )
    else:
        content = (
            '\n'
            + _SP * (indent + 1) + '<div class="' + tc_class + '"' + _build_attrs(ta_attrs) + '>\n'
            + _SP * (indent + 2) + '<div class="tile-icon">' + icon + '</div>\n'
            + _SP * (indent + 2) + '<div class="tile-info">\n'
            + _SP * (indent + 3) + '<div class="tile-name">' + name + '</div>\n'
            + _SP * (indent + 3) + state_html + '\n'
            + _SP * (indent + 2) + '</div>\n'
            + _SP * (indent + 1) + '</div>\n'
            + features_html
            + _SP * indent
        )
    return _h("div", attrs, content, indent)


def _render_features(card: Card, indent: int, inline: bool = False) -> str:
    features = card.get("features", [])
    if not features or not isinstance(features, list):
        return ""
    if inline:
        html_out = ""
    else:
        html_out = _SP * indent + '<div class="tile-features">\n'
    for f in features:
        ftype = f.get("type", "")
        if ftype == "light-brightness":
            eid = card.get("entity", "")
            state = _entity_states.get(eid, {})
            brightness = state.get("attributes", {}).get("brightness", 0) if state.get("state") == "on" else 0
            pct = round(brightness / 255 * 100) if brightness else 0
            slider_attrs = {
                "type": "range",
                "class": "feature-slider",
                "min": "0",
                "max": "100",
                "value": str(pct),
                "hx-post": _url("/action"),
                "hx-trigger": "change",
                "hx-vals": _js_obj(entity_id=eid, action="call-service", service="light.turn_on", data={}),
                "hx-vals-js": '{"data": {"brightness_pct": parseInt(event.target.value)}}',
                "hx-swap": "none",
            }
            label = ""
            if not inline:
                label = _SP * (indent + 2) + '<span class="feature-label">Brightness</span>\n'
            html_out += (
                _SP * (indent + 1) + '<div class="feature-row">\n'
                + label
                + _SP * (indent + 2) + '<input ' + _build_attrs(slider_attrs) + '>\n'
                + _SP * (indent + 1) + '</div>\n'
            )
        elif ftype == "light-color-temp":
            eid = card.get("entity", "")
            html_out += (
                _SP * (indent + 1) + '<div class="feature-row">\n'
                + _SP * (indent + 2) + '<span class="feature-label">Color Temp</span>\n'
                + _SP * (indent + 2) + '<input type="range" class="feature-slider" min="153" max="500" '
                + _build_attrs({
                    "hx-post": _url("/action"),
                    "hx-trigger": "change",
                    "hx-vals": _js_obj(entity_id=eid, action="call-service", service="light.turn_on", data={}),
                    "hx-vals-js": '{"data": {"color_temp": parseInt(event.target.value)}}',
                    "hx-swap": "none",
                }) + '>\n'
                + _SP * (indent + 1) + '</div>\n'
            )
        elif ftype == "numeric-input":
            eid = card.get("entity", "")
            dec_attrs = {
                "hx-post": _url("/action"),
                "hx-trigger": "click",
                "hx-vals": _js_obj(entity_id=eid, action="call-service", service="input_number.decrement"),
                "hx-swap": "none",
            }
            inc_attrs = {
                "hx-post": _url("/action"),
                "hx-trigger": "click",
                "hx-vals": _js_obj(entity_id=eid, action="call-service", service="input_number.increment"),
                "hx-swap": "none",
            }
            html_out += (
                _SP * (indent + 1) + '<div class="feature-row">\n'
                + _SP * (indent + 2) + '<div class="numeric-input">\n'
                + _SP * (indent + 3) + _h("button", {"class": "num-btn", "aria-label": "Decrement", **dec_attrs}, "−") + '\n'
                + _SP * (indent + 3) + _entity_span(eid, indent=indent + 3) + '\n'
                + _SP * (indent + 3) + _h("button", {"class": "num-btn", "aria-label": "Increment", **inc_attrs}, "+") + '\n'
                + _SP * (indent + 2) + '</div>\n'
                + _SP * (indent + 1) + '</div>\n'
            )
    if not inline:
        html_out += _SP * indent + "</div>\n"
    return html_out


def _render_cover_controls(entity_id: str, indent: int) -> str:
    if not entity_id or "." not in entity_id:
        return ""
    dom = entity_id.split(".")[0]
    if dom != "cover":
        return ""
    eid = html.escape(entity_id)
    html_out = _SP * indent + '<div class="cover-controls">\n'
    for label, svc, aria in [("▲", "cover.open_cover", "Open"), ("⏹", "cover.stop_cover", "Stop"), ("▼", "cover.close_cover", "Close")]:
        attrs = {
            "hx-post": _url("/action"),
            "hx-trigger": "click",
            "hx-vals": _js_obj(entity_id=entity_id, action="call-service", service=svc),
            "hx-swap": "none",
            "class": "cover-btn",
            "aria-label": aria,
        }
        html_out += _SP * (indent + 1) + _h("button", attrs, label, 0) + "\n"
    html_out += _SP * indent + "</div>\n"
    return html_out


def _render_entity_toggle(entity_id: str, indent: int) -> str:
    if not entity_id or "." not in entity_id:
        return ""
    if not _is_binary_domain(entity_id):
        return ""
    dom = entity_id.split(".")[0]
    if dom == "cover":
        return ""
    svc = _domain_toggle_service(dom)
    toggle_attrs = {
        "hx-post": _url("/action"),
        "hx-trigger": "change",
        "hx-vals": _js_obj(entity_id=entity_id, action="toggle", service=svc),
        "hx-swap": "none",
    }
    html_out = _SP * indent + '<div class="entity-toggle" onclick="event.stopPropagation()">\n'
    html_out += _SP * (indent + 1) + '<label class="toggle-switch">\n'
    html_out += _SP * (indent + 2) + '<input type="checkbox" class="toggle-input" ' + _build_attrs(toggle_attrs) + '>\n'
    html_out += _SP * (indent + 2) + '<span class="toggle-slider"></span>\n'
    html_out += _SP * (indent + 1) + '</label>\n'
    html_out += _SP * indent + '</div>\n'
    return html_out


@register("grid")
def _render_grid(card: Card, indent: int = 2) -> str:
    columns = card.get("columns", 2)
    raw_cards = card.get("cards", [])
    children = ""
    for c in raw_cards:
        if isinstance(c, dict):
            children += "\n" + _render_card(Card(type=c.get("type", ""), config={k: v for k, v in c.items() if k != "type"}), indent + 1)
    if children:
        children += "\n" + _SP * indent
    return _h("div", {"class": "ha-card grid-card", "style": "--cols: " + str(columns)}, children, indent)


@register("horizontal-stack")
def _render_hstack(card: Card, indent: int = 2) -> str:
    raw_cards = card.get("cards", [])
    children = ""
    for c in raw_cards:
        if isinstance(c, dict):
            children += "\n" + _render_card(Card(type=c.get("type", ""), config={k: v for k, v in c.items() if k != "type"}), indent + 1)
    if children:
        children += "\n" + _SP * indent
    return _h("div", {"class": "ha-card hstack-card"}, children, indent)


@register("vertical-stack")
def _render_vstack(card: Card, indent: int = 2) -> str:
    raw_cards = card.get("cards", [])
    children = ""
    for c in raw_cards:
        if isinstance(c, dict):
            children += "\n" + _render_card(Card(type=c.get("type", ""), config={k: v for k, v in c.items() if k != "type"}), indent + 1)
    if children:
        children += "\n" + _SP * indent
    return _h("div", {"class": "ha-card vstack-card"}, children, indent)


@register("conditional")
def _render_conditional(card: Card, indent: int = 2) -> str:
    conditions = card.get("conditions", [])
    raw_card = card.get("card", {})
    if not isinstance(raw_card, dict):
        return _render_placeholder(card, indent)

    child = _render_card(Card(type=raw_card.get("type", ""), config={k: v for k, v in raw_card.items() if k != "type"}), indent + 1)

    cond_json = html.escape(json.dumps(conditions))
    cond_id = "cond-" + str(hash(json.dumps(conditions, sort_keys=True)) & 0xFFFFFFFF)

    attrs = {
        "class": "conditional-card",
        "id": cond_id,
        "data-conditions": cond_json,
    }

    content = "\n" + _SP * (indent + 1) + child + "\n" + _SP * indent
    return _h("div", attrs, content, indent)


@register("light")
def _render_light(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    name = html.escape(card.get("name", _friendly_name(eid)))
    icon = _icon_html(_entity_icon(eid, card.get("icon", "")), 24)
    state_span = _entity_span(eid, indent=indent + 2)

    toggle_attrs = _action_attrs(eid, "toggle")

    content = (
        '\n'
        + _SP * (indent + 1) + '<div class="light-content">\n'
        + _SP * (indent + 2) + '<div class="light-icon"' + _build_attrs(toggle_attrs) + '>' + icon + '</div>\n'
        + _SP * (indent + 2) + '<div class="light-info">\n'
        + _SP * (indent + 3) + '<div class="light-name">' + name + '</div>\n'
        + _SP * (indent + 3) + state_span + '\n'
        + _SP * (indent + 2) + '</div>\n'
        + _SP * (indent + 2) + '<input type="range" class="light-slider" min="0" max="100" value="0" '
        + _build_attrs({
            "hx-post": _url("/action"),
            "hx-trigger": "change",
            "hx-vals": _js_obj(entity_id=eid, action="call-service", service="light.turn_on", data={}),
            "hx-vals-js": '{"data": {"brightness_pct": parseInt(event.target.value)}}',
            "hx-swap": "none",
        }) + '>\n'
        + _SP * (indent + 1) + '</div>\n'
        + _SP * indent
    )
    return _h("div", {"class": "ha-card light-card"}, content, indent)


@register("sensor")
def _render_sensor(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    name = html.escape(card.get("name", _friendly_name(eid)))
    icon = _icon_html(_entity_icon(eid, card.get("icon", "")), 20)
    state_span = _entity_span(eid, indent=indent + 2)
    graph_type = card.get("graph", "")

    content = (
        '\n'
        + _SP * (indent + 1) + '<div class="sensor-content">\n'
        + _SP * (indent + 2) + '<div class="sensor-icon">' + icon + '</div>\n'
        + _SP * (indent + 2) + '<div class="sensor-info">\n'
        + _SP * (indent + 3) + '<div class="sensor-name">' + name + '</div>\n'
        + _SP * (indent + 3) + state_span + '\n'
        + _SP * (indent + 2) + '</div>\n'
        + _SP * (indent + 1) + '</div>\n'
        + _SP * indent
    )

    graph_html = ""
    if graph_type:
        hours = card.get("hours_to_show", 24)
        graph_html = '\n' + _SP * (indent + 1) + '<div class="sensor-graph" data-entity="' + html.escape(eid) + '" data-hours="' + str(hours) + '"></div>\n' + _SP * indent

    return _h("div", {"class": "ha-card sensor-card"}, "\n" + content + graph_html, indent)


@register("history-graph")
def _render_history_graph(card: Card, indent: int = 2) -> str:
    title = html.escape(card.get("title", ""))
    raw_entities = card.get("entities", [])
    hours = card.get("hours_to_show", 24)

    eids = []
    for ent in raw_entities:
        if isinstance(ent, str):
            eids.append(ent)
        elif isinstance(ent, dict):
            eids.append(ent.get("entity", ""))

    header = ""
    if title:
        header = '\n' + _SP * (indent + 1) + '<div class="graph-header">' + title + '</div>'

    chart_data = html.escape(json.dumps({"entities": eids, "hours": hours}))
    chart_div = '\n' + _SP * (indent + 1) + '<div class="history-graph" data-chart=\'' + chart_data + '\'></div>\n' + _SP * indent

    content = header + chart_div
    return _h("div", {"class": "ha-card graph-card"}, content, indent)


@register("gauge")
def _render_gauge(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    name = html.escape(card.get("name", _friendly_name(eid)))
    min_v = card.get("min", 0)
    max_v = card.get("max", 100)
    severity = card.get("severity", {})

    state_span = _entity_span(eid, indent=indent + 2)
    attrs = {
        "class": "ha-card gauge-card",
        "data-min": str(min_v),
        "data-max": str(max_v),
    }
    if severity:
        attrs["data-severity"] = html.escape(json.dumps(severity))

    content = (
        '\n'
        + _SP * (indent + 1) + '<div class="gauge-content">\n'
        + _SP * (indent + 2) + '<div class="gauge-value">\n'
        + _SP * (indent + 3) + state_span + '\n'
        + _SP * (indent + 2) + '</div>\n'
        + _SP * (indent + 2) + '<div class="gauge-name">' + name + '</div>\n'
        + _SP * (indent + 1) + '</div>\n'
        + _SP * indent
    )
    return _h("div", attrs, content, indent)


@register("iframe")
def _render_iframe(card: Card, indent: int = 2) -> str:
    url = html.escape(card.get("url", ""))
    aspect = card.get("aspect_ratio", "50%")
    style = "aspect-ratio: " + html.escape(str(aspect))
    content = '\n' + _SP * (indent + 1) + '<iframe src="' + url + '" style="' + style + ';width:100%;border:none"></iframe>\n' + _SP * indent
    return _h("div", {"class": "ha-card iframe-card"}, content, indent)


@register("clock")
def _render_clock(card: Card, indent: int = 2) -> str:
    tz = card.get("time_zone", "Europe/London")
    fmt = card.get("time_format", "24")
    sec = card.get("show_seconds", False)
    size = str(card.get("clock_size", "medium") or "")
    no_bg = card.get("no_background", False)

    named_sizes = {"small", "medium", "large"}
    size_class = f"clock-size-{size}" if size in named_sizes else "clock-size-medium"
    attrs = {"class": f"ha-card clock-card {size_class}"}
    if no_bg:
        attrs["class"] += " clock-no-bg"

    clock_id = f"c{abs(hash(tz+fmt+str(sec)))%99999999}"

    time_classes = "clock-digital"
    time_style = ""
    time_extra = ""
    if size == "fit" or size.startswith("fit "):
        time_classes += " icey_text_fit"
        if size.startswith("fit ") and size.endswith("%"):
            try:
                pct = int(size[4:-1])
                if 0 < pct < 1000:
                    time_extra = f' data-fit-pct="{pct}"'
            except ValueError:
                pass
    elif size.endswith("%"):
        time_style = f' style="font-size: {html.escape(size)}"'

    time_html = (
        f'<div class="{time_classes}" id="{clock_id}"'
        + f' data-tz="{html.escape(tz)}"'
        + f' data-fmt="{html.escape(fmt)}"'
        + (' data-sec="1"' if sec else '')
        + time_style
        + time_extra
        + '>--:--</div>'
    )

    ld = card.get("lightdash", {}) or {}
    if not isinstance(ld, dict):
        ld = {}

    date_html = ""
    if ld.get("date_show", False):
        date_format = ld.get("date_format", "default")
        date_fontsize = str(ld.get("date_fontsize", "") or "")

        date_classes = "clock-date"
        date_style = ""
        date_extra = ""
        if date_fontsize == "fit" or date_fontsize.startswith("fit "):
            date_classes += " icey_text_fit"
            if date_fontsize.startswith("fit ") and date_fontsize.endswith("%"):
                try:
                    pct = int(date_fontsize[4:-1])
                    if 0 < pct < 1000:
                        date_extra = f' data-fit-pct="{pct}"'
                except ValueError:
                    pass
        elif date_fontsize:
            date_style = f' style="font-size: {html.escape(date_fontsize)}"'

        date_id = f"d{abs(hash(tz+date_format))%99999999}"
        date_html = (
            '\n' + _SP * (indent + 1)
            + f'<div class="{date_classes}" id="{date_id}"'
            + f' data-dfmt="{html.escape(date_format)}"'
            + date_style
            + date_extra
            + '>---</div>'
        )

    content = (
        '\n'
        + _SP * (indent + 1)
        + time_html
        + date_html
        + '\n'
        + _SP * indent
    )
    return _h("div", attrs, content, indent)


_WEATHER_CONDITION_ICONS: Dict[str, str] = {
    "clear-night": "weather-night",
    "cloudy": "weather-cloudy",
    "fog": "weather-fog",
    "hail": "weather-hail",
    "lightning": "weather-lightning",
    "lightning-rainy": "weather-lightning-rainy",
    "partlycloudy": "weather-partly-cloudy",
    "pouring": "weather-pouring",
    "rainy": "weather-rainy",
    "snowy": "weather-snowy",
    "snowy-rainy": "weather-snowy-rainy",
    "sunny": "weather-sunny",
    "windy": "weather-windy",
    "windy-variant": "weather-windy-variant",
    "exceptional": "alert-outline",
}

_CONDITION_DISPLAY: Dict[str, str] = {
    "clear-night": "Clear night",
    "partlycloudy": "Partly cloudy",
    "snowy-rainy": "Snowy and rainy",
    "windy-variant": "Windy",
    "lightning-rainy": "Lightning and rain",
}


@register("weather-forecast")
def _render_weather_forecast(card: Card, indent: int = 2) -> str:
    eid = card.get("entity", "")
    if not eid:
        return _render_placeholder(card, indent)

    forecast_eid = card.get("forecast_entity", "")

    name = card.get("name", "")
    show_current = card.get("show_current", True)
    show_forecast = card.get("show_forecast", True)
    forecast_type = card.get("forecast_type", "daily")
    secondary_attr = card.get("secondary_info_attribute", "")
    round_temp = card.get("round_temperature", False)
    forecast_count = card.get("forecast_count", 0)

    state = _entity_states.get(eid, {})
    attrs_data = state.get("attributes", {}) if state else {}
    condition = state.get("state", "") if state else ""
    temp_unit = attrs_data.get("temperature_unit", "°C")

    fc_entity_key = forecast_eid or eid
    forecast_list = _forecast_data.get(fc_entity_key, [])
    if not forecast_list:
        if forecast_eid:
            fc_state = _entity_states.get(forecast_eid, {})
            fc_attrs = fc_state.get("attributes", {}) if fc_state else {}
            forecast_list = fc_attrs.get("forecast", [])
        else:
            forecast_list = attrs_data.get("forecast", [])

    def _fmt_temp(val, unit=temp_unit, should_round=round_temp):
        if val is None:
            return "—"
        if should_round:
            val = round(val)
        return f"{val}{html.escape(unit)}"

    content = ""

    if show_current:
        temp = attrs_data.get("temperature")
        humidity = attrs_data.get("humidity")
        icon_name = _WEATHER_CONDITION_ICONS.get(condition, "weather-cloudy")
        icon = _icon_html("mdi:" + icon_name, 48)

        sec_text = ""
        if secondary_attr == "extrema" or not secondary_attr:
            if forecast_list and forecast_type in ("daily", "twice_daily"):
                first = forecast_list[0]
                hi = first.get("temperature")
                lo = first.get("templow")
                if hi is not None and lo is not None:
                    sec_text = f"H: {_fmt_temp(hi)} L: {_fmt_temp(lo)}"
        if not sec_text and (secondary_attr == "precipitation" or not secondary_attr):
            if forecast_list:
                first = forecast_list[0]
                precip = first.get("precipitation")
                if precip is not None:
                    sec_text = f"Precip: {precip}mm"
        if not sec_text and (secondary_attr == "humidity" or not secondary_attr):
            if humidity is not None:
                sec_text = f"Humidity: {humidity}%"
        if not sec_text and secondary_attr:
            val = attrs_data.get(secondary_attr)
            if val is not None:
                sec_text = f"{secondary_attr.replace('_', ' ').title()}: {val}"

        if condition:
            key = condition.lower()
            if key in _CONDITION_DISPLAY:
                cond_display = _CONDITION_DISPLAY[key]
            else:
                cond_display = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', condition).replace("_", " ").replace("-", " ").title()
        else:
            cond_display = "—"
        temp_display = _fmt_temp(temp)

        content += (
            '\n'
            + _SP * (indent + 1) + '<div class="weather-current">\n'
            + _SP * (indent + 2) + '<div class="weather-icon-large">' + icon + '</div>\n'
            + _SP * (indent + 2) + '<div class="weather-info">\n'
            + _SP * (indent + 3) + '<div class="weather-condition">' + html.escape(cond_display) + '</div>\n'
        )
        if name:
            content += _SP * (indent + 3) + '<div class="weather-name">' + html.escape(name) + '</div>\n'
        content += (
            _SP * (indent + 2) + '</div>\n'
            + _SP * (indent + 2) + '<div class="weather-current-right">\n'
            + _SP * (indent + 3) + '<div class="weather-temp">' + html.escape(temp_display) + '</div>\n'
        )
        if sec_text:
            content += _SP * (indent + 3) + '<div class="weather-secondary">' + html.escape(sec_text) + '</div>\n'
        content += (
            _SP * (indent + 2) + '</div>\n'
            + _SP * (indent + 1) + '</div>\n'
        )

    if show_forecast:
        flist = forecast_list
        logger.info("Weather forecast for %s: %d items in forecast array", eid, len(flist))
        if forecast_count > 0:
            flist = flist[:forecast_count]
        elif forecast_type == "hourly":
            flist = flist[:12]
        else:
            flist = flist[:5]

        if flist:
            content += _SP * (indent + 1) + '<div class="weather-forecast">\n'
            for item in flist:
                fc_cond = item.get("condition", "")
                fc_icon_name = _WEATHER_CONDITION_ICONS.get(fc_cond, "weather-cloudy")
                fc_icon = _icon_html("mdi:" + fc_icon_name, 18)
                fc_temp = item.get("temperature")
                fc_templow = item.get("templow")
                dt_str = item.get("datetime", "")

                if forecast_type in ("daily", "twice_daily") and len(dt_str) >= 10:
                    import datetime as _dt_mod
                    try:
                        day = _dt_mod.datetime.strptime(dt_str[:10], "%Y-%m-%d").strftime("%a")
                    except (ValueError, ImportError):
                        day = dt_str[:10]
                elif forecast_type == "hourly" and len(dt_str) >= 16:
                    day = dt_str[11:16]
                else:
                    day = dt_str

                if fc_templow is not None and forecast_type in ("daily", "twice_daily"):
                    temp_str = f"{_fmt_temp(fc_templow, should_round=True, unit='')}-{_fmt_temp(fc_temp, should_round=True, unit=temp_unit)}"
                else:
                    temp_str = _fmt_temp(fc_temp, should_round=True)

                content += (
                    _SP * (indent + 2) + '<div class="weather-fc-item">\n'
                    + _SP * (indent + 3) + '<span class="weather-fc-day">' + html.escape(day) + '</span>\n'
                    + _SP * (indent + 3) + '<span class="weather-fc-icon">' + fc_icon + '</span>\n'
                    + _SP * (indent + 3) + '<span class="weather-fc-temps">' + html.escape(temp_str) + '</span>\n'
                    + _SP * (indent + 2) + '</div>\n'
                )
            content += _SP * (indent + 1) + '</div>\n'

    sse_trigger = f"sse:forecast_{eid.replace('.', '_')}"
    triggers = sse_trigger
    # Only lazy-load on initial cold render (no cached/WS data AND no attributes forecast)
    fc_key = forecast_eid or eid
    if fc_key not in _forecast_data and not forecast_list:
        triggers = f"load, {sse_trigger}"
    extra_attrs: Dict[str, str] = {
        "class": "ha-card weather-card",
        "data-forecast-entity": eid,
        "hx-trigger": triggers,
        "hx-get": _url(f"/api/weather-forecast/{_dashboard_name}/{_view_path}?entity={eid}"),
        "hx-target": "this",
        "hx-swap": "outerHTML",
    }
    return _h("div", extra_attrs, content, indent)


# ---- Helpers --------------------------------------------------------------


def _friendly_name(entity_id: str) -> str:
    parts = entity_id.split(".")
    if len(parts) < 2:
        return entity_id
    raw = parts[1].replace("_", " ").replace("-", " ")
    return raw.title()


def _render_markdown_text(text: str) -> str:
    lines = text.split("\n")
    html_out = ""
    in_list = False
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            html_out += f"<h{level}>{_inline_md(m.group(2))}</h{level}>\n"
            continue
        m = re.match(r"^[\-\*]\s+(.+)$", line)
        if m:
            if not in_list:
                html_out += "<ul>\n"
                in_list = True
            html_out += "<li>" + _inline_md(m.group(1)) + "</li>\n"
            continue
        if in_list:
            html_out += "</ul>\n"
            in_list = False
        if not line.strip():
            continue
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m:
            html_out += "<p>" + _inline_md(m.group(2)) + "</p>\n"
            continue
        html_out += "<p>" + _inline_md(line) + "</p>\n"
    if in_list:
        html_out += "</ul>\n"

    html_out = html_out.replace("&", "&amp;")
    html_out = html_out.replace("<strong>", "\x00strong\x00")
    html_out = html_out.replace("</strong>", "\x01strong\x01")
    html_out = html_out.replace("<em>", "\x00em\x00")
    html_out = html_out.replace("</em>", "\x01em\x01")
    html_out = html_out.replace("<code>", "\x00code\x00")
    html_out = html_out.replace("</code>", "\x01code\x01")
    html_out = html_out.replace("<a ", "\x00a\x00")
    html_out = html_out.replace("</a>", "\x01a\x01")
    html_out = html_out.replace("<", "&lt;").replace(">", "&gt;")
    html_out = html_out.replace("\x00strong\x00", "<strong>")
    html_out = html_out.replace("\x01strong\x01", "</strong>")
    html_out = html_out.replace("\x00em\x00", "<em>")
    html_out = html_out.replace("\x01em\x01", "</em>")
    html_out = html_out.replace("\x00code\x00", "<code>")
    html_out = html_out.replace("\x01code\x01", "</code>")
    html_out = html_out.replace("\x00a\x00", "<a ")
    html_out = html_out.replace("\x01a\x01", "</a>")

    return html_out


def _inline_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text


# ---------------------------------------------------------------------------
#  today-card  (custom:today-card)
# ---------------------------------------------------------------------------

_HA_COLORS: Dict[str, str] = {
    "primary": "#03a9f4", "dark-primary": "#0288d1", "light-primary": "#b3e5fc",
    "accent": "#ff9800", "disabled": "#bdbdbd",
    "red": "#f44336", "pink": "#e91e63", "purple": "#926bc7", "deep-purple": "#6e41ab",
    "indigo": "#3f51b5", "blue": "#2196f3", "light-blue": "#03a9f4", "cyan": "#00bcd4",
    "teal": "#009688", "green": "#4caf50", "light-green": "#8bc34a", "lime": "#cddc39",
    "yellow": "#ffeb3b", "amber": "#ffc107", "orange": "#ff9800", "deep-orange": "#ff6f22",
    "brown": "#795548", "light-grey": "#bdbdbd", "grey": "#9e9e9e", "dark-grey": "#606060",
    "blue-grey": "#607d8b", "black": "#000000", "white": "#ffffff",
}

_TODAY_AUTO_COLORS = [
    "#03a9f4", "#e91e63", "#009688", "#ff9800",
    "#926bc7", "#4caf50", "#3f51b5", "#00bcd4",
]

_TODAY_CAL_ICON = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">'
    '<path d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 '
    '2-2V6a2 2 0 0 0-2-2m0 16H5V10h14zm0-12H5V6h14z"/></svg>'
)


def _today_color(name: str) -> str:
    if not name:
        return ""
    if name.startswith("#"):
        return name
    return _HA_COLORS.get(name.lower(), name)


def _fmt_event_time(dt: "_today_dt.datetime", fmt: str) -> str:
    h24 = dt.hour
    h12 = h24 % 12 or 12
    tokens = [
        ("HH", f"{h24:02d}"), ("H", str(h24)),
        ("hh", f"{h12:02d}"), ("h", str(h12)),
        ("mm", f"{dt.minute:02d}"), ("m", str(dt.minute)),
        ("A", "AM" if h24 < 12 else "PM"), ("a", "am" if h24 < 12 else "pm"),
    ]
    out = ""
    i = 0
    while i < len(fmt):
        for tok, val in tokens:
            if fmt.startswith(tok, i):
                out += val
                i += len(tok)
                break
        else:
            out += fmt[i]
            i += 1
    return out


@register("today")
def _render_today_card(card: Card, indent: int = 2) -> str:
    cfg_entities = card.get("entities", []) or []
    title = card.get("title", "") or ""
    advance = int(card.get("advance", 0) or 0)
    show_all_day = card.get("show_all_day_events", True)
    show_past = card.get("show_past_events", False)
    limit = int(card.get("limit", 0) or 0)
    time_format = card.get("time_format", "HH:mm") or "HH:mm"
    fallback_color = _today_color(card.get("fallback_color", ""))
    card_height = int(card.get("height", 0) or 0)

    now = _today_dt.datetime.now().astimezone()
    today = now.date()
    target_date = (now + _today_dt.timedelta(days=advance)).date()

    collected: list = []
    auto_i = 0
    for ent in cfg_entities:
        if isinstance(ent, str):
            eid, color = ent, ""
        elif isinstance(ent, dict):
            eid, color = ent.get("entity", ""), _today_color(ent.get("color", ""))
        else:
            continue
        if not eid:
            continue
        if not color:
            if fallback_color:
                color = fallback_color
            else:
                color = _TODAY_AUTO_COLORS[auto_i % len(_TODAY_AUTO_COLORS)]
                auto_i += 1
        for ev in _calendar_data.get(eid, []):
            collected.append((ev, color))

    vms: list = []
    for ev, color in collected:
        start = ev.get("start")
        end = ev.get("end")
        if start is None or end is None:
            continue
        all_day = bool(ev.get("all_day", False))
        s_date = start.date()
        e_date = (end - _today_dt.timedelta(seconds=1)).date() if end > start else end.date()
        if not (s_date <= target_date <= e_date):
            continue
        if all_day and not show_all_day:
            continue

        classes = ["today-event"]
        is_current = is_past = is_future = False

        if all_day:
            classes.append("is-all-day")
            if target_date < today:
                is_past = True
            elif target_date > today:
                is_future = True
        else:
            if start <= now < end:
                is_current = True
            elif end <= now:
                is_past = True
            else:
                is_future = True

        if is_past and not show_past:
            continue
        if is_current:
            classes.append("is-current")
        elif is_past:
            classes.append("is-in-past")
        elif is_future:
            classes.append("is-in-future")

        count = ""
        if e_date > s_date:
            classes.append("is-multi-day")
            total = (e_date - s_date).days + 1
            day_idx = (target_date - s_date).days + 1
            if target_date == s_date:
                classes.append("is-first-day")
            if target_date == e_date:
                classes.append("is-last-day")
            count = f"({day_idx}/{total})"

        if all_day or e_date > s_date:
            sched = "All day"
        else:
            sched = _fmt_event_time(start, time_format) + " \u2013 " + _fmt_event_time(end, time_format)

        vms.append({
            "classes": classes,
            "color": color,
            "summary": ev.get("summary", "") or "(busy)",
            "sched": sched,
            "count": count,
            "is_current": is_current,
            "sort": (0 if all_day else 1, start),
        })

    vms.sort(key=lambda v: v["sort"])
    if limit > 0:
        vms = vms[:limit]

    header_html = ""
    if title:
        date_label = html.escape(target_date.strftime("%a %d %b").lstrip("0"))
        header_html = (
            _SP * (indent + 1) + '<div class="today-header">\n'
            + _SP * (indent + 2) + '<span class="today-header-icon">' + _TODAY_CAL_ICON + '</span>\n'
            + _SP * (indent + 2) + '<span class="today-title">' + html.escape(title) + '</span>\n'
            + _SP * (indent + 2) + '<span class="today-header-date">' + date_label + '</span>\n'
            + _SP * (indent + 1) + '</div>\n'
        )

    rows = ""
    for v in vms:
        cls = " ".join(v["classes"])
        count_html = (' <span class="today-event-count">' + html.escape(v["count"]) + '</span>') if v["count"] else ""
        now_html = ('\n' + _SP * (indent + 2) + '<span class="today-now">Now</span>') if v["is_current"] else ""
        rows += (
            _SP * (indent + 1) + '<div class="' + cls + '" style="--ev-color:' + html.escape(v["color"]) + '">\n'
            + _SP * (indent + 2) + '<div class="today-indicator"></div>\n'
            + _SP * (indent + 2) + '<div class="today-details">\n'
            + _SP * (indent + 3) + '<p class="today-event-title"><strong>' + html.escape(v["summary"]) + '</strong>' + count_html + '</p>\n'
            + _SP * (indent + 3) + '<p class="today-schedule">' + html.escape(v["sched"]) + '</p>\n'
            + _SP * (indent + 2) + '</div>'
            + now_html + '\n'
            + _SP * (indent + 1) + '</div>\n'
        )
    if not rows:
        rows = _SP * (indent + 1) + '<div class="today-empty">Nothing left on the calendar today</div>\n'

    list_style = ""
    if card_height > 0:
        list_style = ' style="overflow-y: auto"'
    list_html = _SP * (indent + 1) + '<div class="today-list"' + list_style + '>\n' + rows + _SP * (indent + 1) + '</div>\n'

    attrs: Dict[str, str] = {"class": "ha-card today-card"}
    if card_height > 0:
        attrs["style"] = f"height: {card_height}px;"
    ta = _tap_action_attrs(card)
    if ta:
        attrs["class"] += " is-tappable"
        attrs.update(ta)

    content = "\n" + header_html + list_html + _SP * indent
    return _h("div", attrs, content, indent)
