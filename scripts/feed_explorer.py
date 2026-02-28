"""
Feed search and detail extraction helpers for Xiaohongshu.

This module focuses on extracting data from `window.__INITIAL_STATE__` on
Xiaohongshu pages. It is designed to be reused by CDP automation flows.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlencode


SEARCH_BASE_URL = "https://www.xiaohongshu.com/search_result"
FEED_DETAIL_URL_TEMPLATE = (
    "https://www.xiaohongshu.com/explore/{feed_id}"
    "?xsec_token={xsec_token}&xsec_source=pc_feed"
)


SORT_BY_OPTIONS = ("综合", "最新", "最多点赞", "最多评论", "最多收藏")
NOTE_TYPE_OPTIONS = ("不限", "视频", "图文")
PUBLISH_TIME_OPTIONS = ("不限", "一天内", "一周内", "半年内")
SEARCH_SCOPE_OPTIONS = ("不限", "已看过", "未看过", "已关注")
LOCATION_OPTIONS = ("不限", "同城", "附近")

_FILTER_VALUE_OPTIONS = {
    "sort_by": SORT_BY_OPTIONS,
    "note_type": NOTE_TYPE_OPTIONS,
    "publish_time": PUBLISH_TIME_OPTIONS,
    "search_scope": SEARCH_SCOPE_OPTIONS,
    "location": LOCATION_OPTIONS,
}
_ALL_FILTER_OPTION_VALUES = tuple(
    dict.fromkeys(
        [
            *SORT_BY_OPTIONS,
            *NOTE_TYPE_OPTIONS,
            *PUBLISH_TIME_OPTIONS,
            *SEARCH_SCOPE_OPTIONS,
            *LOCATION_OPTIONS,
        ]
    )
)


class FeedExplorerError(Exception):
    """Raised when search/detail extraction fails."""


@dataclass(slots=True)
class SearchFilters:
    """Filter options for Xiaohongshu search page."""

    sort_by: str | None = None
    note_type: str | None = None
    publish_time: str | None = None
    search_scope: str | None = None
    location: str | None = None

    def selected_items(self) -> list[tuple[str, str]]:
        """Return selected non-empty filter items as (field_name, value)."""
        items: list[tuple[str, str]] = []
        for name in _FILTER_VALUE_OPTIONS:
            value = getattr(self, name)
            if value:
                items.append((name, value))
        return items

    def validate(self):
        """Validate selected filter values."""
        for name, value in self.selected_items():
            valid_values = _FILTER_VALUE_OPTIONS[name]
            if value not in valid_values:
                raise FeedExplorerError(
                    f"Invalid value for {name}: {value}. "
                    f"Valid options: {', '.join(valid_values)}"
                )


def make_search_url(keyword: str) -> str:
    """Build Xiaohongshu search URL for feed search."""
    if not keyword.strip():
        raise FeedExplorerError("Keyword cannot be empty.")
    query = urlencode({"keyword": keyword.strip(), "source": "web_explore_feed"})
    return f"{SEARCH_BASE_URL}?{query}"


def make_feed_detail_url(feed_id: str, xsec_token: str) -> str:
    """Build feed detail URL from feed id and xsec token."""
    feed_id = feed_id.strip()
    xsec_token = xsec_token.strip()
    if not feed_id:
        raise FeedExplorerError("feed_id cannot be empty.")
    if not xsec_token:
        raise FeedExplorerError("xsec_token cannot be empty.")
    return FEED_DETAIL_URL_TEMPLATE.format(feed_id=feed_id, xsec_token=xsec_token)


class FeedExplorer:
    """
    Reusable extractor for feed search/detail pages.

    Args:
        evaluate: A callable that executes JavaScript and returns result value.
        sleep: A callable compatible with `sleep(base_seconds, minimum_seconds=...)`.
    """

    def __init__(
        self,
        evaluate: Callable[[str], Any],
        sleep: Callable[..., None],
        move_mouse: Callable[[float, float], None] | None = None,
        click_mouse: Callable[[float, float], None] | None = None,
    ):
        self._evaluate = evaluate
        self._sleep = sleep
        self._move_mouse = move_mouse
        self._click_mouse = click_mouse

    def _option_ordered_values(self, filters: SearchFilters) -> list[str]:
        """Return filter values in deterministic UI order."""
        ordered_keys = ("sort_by", "note_type", "publish_time", "search_scope", "location")
        values: list[str] = []
        for key in ordered_keys:
            value = getattr(filters, key)
            if value:
                values.append(value)
        return values

    def _wait_js_condition(
        self,
        condition_js: str,
        timeout_seconds: float = 20.0,
        poll_seconds: float = 0.5,
    ) -> bool:
        """Wait until JavaScript condition becomes truthy."""
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                ok = self._evaluate(condition_js)
                if ok:
                    return True
            except Exception:
                # Ignore transient DOM errors and continue polling.
                pass
            self._sleep(poll_seconds, minimum_seconds=min(0.2, poll_seconds))
        return False

    def _wait_for_search_state(self):
        """Wait until search feed data is available in __INITIAL_STATE__."""
        ready = self._wait_js_condition(
            """
            (() => {
                const state = window.__INITIAL_STATE__;
                return !!(
                    state &&
                    state.search &&
                    state.search.feeds
                );
            })()
            """,
            timeout_seconds=25.0,
            poll_seconds=0.6,
        )
        if not ready:
            raise FeedExplorerError(
                "Timed out waiting for search data in window.__INITIAL_STATE__."
            )

    def _wait_for_detail_state(self):
        """Wait until detail note data is available in __INITIAL_STATE__."""
        ready = self._wait_js_condition(
            """
            (() => {
                const state = window.__INITIAL_STATE__;
                return !!(
                    state &&
                    state.note &&
                    state.note.noteDetailMap
                );
            })()
            """,
            timeout_seconds=25.0,
            poll_seconds=0.6,
        )
        if not ready:
            raise FeedExplorerError(
                "Timed out waiting for feed detail in window.__INITIAL_STATE__."
            )

    def _find_filter_button_rect(self) -> dict[str, float] | None:
        """Return visible filter button rect."""
        rect = self._evaluate(
            """
            (() => {
                const btn = document.querySelector("div.filter, [class*='filter']");
                if (!(btn instanceof HTMLElement) || btn.offsetParent === null) {
                    return null;
                }
                const r = btn.getBoundingClientRect();
                return { x: r.x, y: r.y, width: r.width, height: r.height };
            })()
            """
        )
        return rect if isinstance(rect, dict) else None

    def _find_filter_panel_rect(self) -> dict[str, float] | None:
        """Return visible filter panel rect when available."""
        option_values_literal = json.dumps(list(_ALL_FILTER_OPTION_VALUES), ensure_ascii=False)
        rect = self._evaluate(f"""
            (() => {{
                const optionValues = {option_values_literal};
                const normalize = (text) => (text || "").replace(/\\s+/g, " ").trim();
                const root = document.querySelector("div.filter, [class*='filter']");
                if (!(root instanceof HTMLElement) || root.offsetParent === null) {{
                    return null;
                }}
                const selectors = [
                    ".filter-panel",
                    "[class*='filter-panel']",
                    "[class*='filter-pop']",
                ];
                const nodes = root.querySelectorAll(selectors.join(","));
                for (const node of nodes) {{
                    if (!(node instanceof HTMLElement) || node.offsetParent === null) {{
                        continue;
                    }}
                    const text = normalize(node.innerText || node.textContent);
                    if (!text) {{
                        continue;
                    }}
                    if (!optionValues.some((option) => text.includes(option))) {{
                        continue;
                    }}
                    const r = node.getBoundingClientRect();
                    if (r.width < 60 || r.height < 30) {{
                        continue;
                    }}
                    return {{ x: r.x, y: r.y, width: r.width, height: r.height }};
                }}
                return null;
            }})()
        """)
        return rect if isinstance(rect, dict) else None

    def _find_filter_option_rect(self, filter_value: str) -> dict[str, float] | None:
        """Return target filter option rect from visible filter panel only."""
        option_literal = json.dumps(filter_value, ensure_ascii=False)
        rect = self._evaluate(f"""
            (() => {{
                const targetText = {option_literal};
                const normalize = (text) => (text || "").replace(/\\s+/g, " ").trim();
                const root = document.querySelector("div.filter, [class*='filter']");
                if (!(root instanceof HTMLElement) || root.offsetParent === null) {{
                    return null;
                }}
                const panel = root.querySelector(
                    ".filter-panel, [class*='filter-panel'], [class*='filter-pop']"
                );
                if (!(panel instanceof HTMLElement) || panel.offsetParent === null) {{
                    return null;
                }}
                const nodes = panel.querySelectorAll("button, [role='button'], div, span, li, a");
                for (const el of nodes) {{
                    if (!(el instanceof HTMLElement) || el.offsetParent === null) {{
                        continue;
                    }}
                    const text = normalize(el.textContent);
                    if (text !== targetText) {{
                        continue;
                    }}

                    const r = el.getBoundingClientRect();
                    if (r.width < 12 || r.height < 10 || r.width > 260 || r.height > 96) {{
                        continue;
                    }}

                    let hasSameTextChild = false;
                    for (const child of el.children) {{
                        if (normalize(child.textContent) === targetText) {{
                            hasSameTextChild = true;
                            break;
                        }}
                    }}
                    if (hasSameTextChild) {{
                        continue;
                    }}
                    return {{ x: r.x, y: r.y, width: r.width, height: r.height }};
                }}
                return null;
            }})()
        """)
        return rect if isinstance(rect, dict) else None

    def _open_filter_panel_via_hover_mouse(self) -> tuple[bool, str]:
        """Open hover panel and keep cursor inside panel area."""
        if not self._move_mouse:
            return False, "mouse_dispatch_not_available"

        button_rect = self._find_filter_button_rect()
        if not button_rect:
            return False, "filter_button_not_found"

        bx = float(button_rect["x"]) + float(button_rect["width"]) / 2
        by = float(button_rect["y"]) + float(button_rect["height"]) / 2
        near_x = bx - 18.0
        near_y = by + 18.0

        for attempt in range(20):
            if attempt == 0:
                self._move_mouse(bx, by)
            else:
                if attempt % 2 == 0:
                    self._move_mouse(near_x, near_y)
                else:
                    self._move_mouse(bx, by)
            self._sleep(0.08, minimum_seconds=0.03)

            panel_rect = self._find_filter_panel_rect()
            if panel_rect:
                enter_x = float(panel_rect["x"]) + float(panel_rect["width"]) - 18.0
                enter_y = float(panel_rect["y"]) + min(28.0, float(panel_rect["height"]) - 10.0)
                self._move_mouse(enter_x, enter_y)
                self._sleep(0.06, minimum_seconds=0.02)
                if self._find_filter_panel_rect():
                    return True, "ok"

        return False, "filter_panel_not_found"

    def _apply_filters_in_single_panel(self, option_values: list[str]) -> tuple[bool, str]:
        """Apply all filters in one hover session/panel."""
        if not option_values:
            return True, "ok"
        if not self._move_mouse or not self._click_mouse:
            return False, "mouse_dispatch_not_available"

        opened, reason = self._open_filter_panel_via_hover_mouse()
        if not opened:
            return False, reason

        for value in option_values:
            applied = False
            for _ in range(8):
                option_rect = self._find_filter_option_rect(value)
                if not option_rect:
                    opened, reason = self._open_filter_panel_via_hover_mouse()
                    if not opened:
                        continue
                    option_rect = self._find_filter_option_rect(value)

                if not option_rect:
                    self._sleep(0.07, minimum_seconds=0.03)
                    continue

                ox = float(option_rect["x"]) + float(option_rect["width"]) / 2
                oy = float(option_rect["y"]) + float(option_rect["height"]) / 2
                self._move_mouse(ox, oy)
                self._sleep(0.05, minimum_seconds=0.02)
                self._click_mouse(ox, oy)
                self._sleep(0.16, minimum_seconds=0.06)

                panel_rect = self._find_filter_panel_rect()
                if panel_rect:
                    keep_x = float(panel_rect["x"]) + float(panel_rect["width"]) - 18.0
                    keep_y = float(panel_rect["y"]) + min(28.0, float(panel_rect["height"]) - 10.0)
                    self._move_mouse(keep_x, keep_y)
                    self._sleep(0.05, minimum_seconds=0.02)

                applied = True
                break

            if not applied:
                return False, f"option_not_found:{value}"

        return True, "ok"

    def _try_apply_filter_via_hover_mouse(self, filter_value: str) -> tuple[bool, str]:
        """
        Apply one filter option via real CDP mouse hover/click.

        This path is used because some Xiaohongshu filter panels are CSS-hover
        driven and cannot be reliably opened via synthetic JS events.
        """
        if not self._move_mouse or not self._click_mouse:
            return False, "mouse_dispatch_not_available"

        button_rect = self._find_filter_button_rect()
        if not button_rect:
            return False, "filter_button_not_found"

        bx = float(button_rect["x"]) + float(button_rect["width"]) / 2
        by = float(button_rect["y"]) + float(button_rect["height"]) / 2
        below_x = bx
        below_y = float(button_rect["y"]) + float(button_rect["height"]) + 28

        self._move_mouse(bx, by)
        self._sleep(0.12, minimum_seconds=0.05)

        for idx in range(24):
            panel_rect = self._find_filter_panel_rect()
            if panel_rect:
                px = float(panel_rect["x"]) + min(28.0, float(panel_rect["width"]) * 0.25)
                py = float(panel_rect["y"]) + min(24.0, float(panel_rect["height"]) * 0.25)
                self._move_mouse(px, py)
                self._sleep(0.05, minimum_seconds=0.02)

            option_rect = self._find_filter_option_rect(filter_value)
            if option_rect:
                ox = float(option_rect["x"]) + float(option_rect["width"]) / 2
                oy = float(option_rect["y"]) + float(option_rect["height"]) / 2
                self._move_mouse(ox, oy)
                self._sleep(0.08, minimum_seconds=0.03)
                self._click_mouse(ox, oy)
                return True, "ok"

            if idx % 2 == 0:
                self._move_mouse(bx, by)
            else:
                self._move_mouse(below_x, below_y)
            self._sleep(0.12, minimum_seconds=0.05)

        return False, "option_not_found"

    def _apply_single_filter_js_fallback(self, filter_value: str) -> dict[str, Any]:
        """Fallback path using in-page synthetic events only."""
        option_literal = json.dumps(filter_value)
        option_values_literal = json.dumps(list(_ALL_FILTER_OPTION_VALUES), ensure_ascii=False)
        result = self._evaluate(f"""
            (async () => {{
                const targetText = {option_literal};
                const optionValues = {option_values_literal};
                const filterBtn = document.querySelector("div.filter, [class*='filter']");
                if (!filterBtn) {{
                    return {{ ok: false, reason: "filter_button_not_found" }};
                }}

                const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
                const normalizeText = (text) => (text || "").replace(/\\s+/g, " ").trim();

                const openFilterPanel = () => {{
                    filterBtn.dispatchEvent(new MouseEvent("mouseenter", {{ bubbles: true }}));
                    filterBtn.dispatchEvent(new MouseEvent("mouseover", {{ bubbles: true }}));
                    filterBtn.dispatchEvent(new MouseEvent("mousemove", {{ bubbles: true }}));
                }};

                const findVisiblePanel = () => {{
                    const selectors = [
                        ".filter-panel",
                        "[class*='filter-panel']",
                        "[class*='filter-pop']",
                        "[class*='popover']",
                        "[class*='popup']",
                        "[role='menu']",
                        "[role='listbox']",
                    ];
                    const nodes = document.querySelectorAll(selectors.join(","));
                    for (const node of nodes) {{
                        if (!(node instanceof HTMLElement)) {{
                            continue;
                        }}
                        if (node.offsetParent === null) {{
                            continue;
                        }}
                        const text = normalizeText(node.innerText || node.textContent);
                        if (!optionValues.some((option) => text.includes(option))) {{
                            continue;
                        }}
                        return node;
                    }}
                    return null;
                }};

                openFilterPanel();
                let panel = null;
                for (let i = 0; i < 20; i++) {{
                    panel = findVisiblePanel();
                    if (panel) {{
                        break;
                    }}
                    if (i === 6 || i === 12) {{
                        openFilterPanel();
                    }}
                    await sleep(120);
                }}

                if (!panel) {{
                    return {{ ok: false, reason: "filter_panel_not_found" }};
                }}

                const findOption = () => {{
                    const candidates = panel.querySelectorAll(
                        "[class*='tag'], [role='button'], button, span, div, li"
                    );
                    for (const el of candidates) {{
                        if (!(el instanceof HTMLElement) || el.offsetParent === null) {{
                            continue;
                        }}
                        const text = normalizeText(el.textContent);
                        if (text !== targetText) {{
                            continue;
                        }}
                        let hasSameTextChild = false;
                        for (const child of el.children) {{
                            if (normalizeText(child.textContent) === targetText) {{
                                hasSameTextChild = true;
                                break;
                            }}
                        }}
                        if (hasSameTextChild) {{
                            continue;
                        }}
                        return el;
                    }}
                    return null;
                }};

                let optionEl = null;
                for (let i = 0; i < 12; i++) {{
                    optionEl = findOption();
                    if (optionEl) {{
                        break;
                    }}
                    await sleep(80);
                }}

                if (!optionEl) {{
                    return {{ ok: false, reason: "option_not_found" }};
                }}

                optionEl.click();
                return {{ ok: true }};
            }})()
        """)
        return result if isinstance(result, dict) else {"ok": False, "reason": "unknown"}

    def _apply_single_filter(self, filter_value: str):
        """Apply one filter option with hover-first strategy."""
        hover_reason = None
        if self._move_mouse and self._click_mouse:
            hover_ok, hover_reason = self._try_apply_filter_via_hover_mouse(filter_value)
            if hover_ok:
                self._sleep(1.2, minimum_seconds=0.4)
                self._wait_for_search_state()
                return

        js_result = self._apply_single_filter_js_fallback(filter_value)
        if js_result.get("ok"):
            self._sleep(1.2, minimum_seconds=0.4)
            self._wait_for_search_state()
            return

        reason = js_result.get("reason", "unknown")
        if hover_reason and hover_reason != reason:
            reason = f"{reason} (hover_attempt={hover_reason})"
        raise FeedExplorerError(
            f"Failed to apply search filter '{filter_value}': {reason}"
        )

    def _extract_search_feeds(self) -> list[dict[str, Any]]:
        """Extract feeds array from search initial state."""
        raw = self._evaluate(
            """
            (() => {
                if (
                    window.__INITIAL_STATE__ &&
                    window.__INITIAL_STATE__.search &&
                    window.__INITIAL_STATE__.search.feeds
                ) {
                    const feeds = window.__INITIAL_STATE__.search.feeds;
                    const data = feeds.value !== undefined ? feeds.value : feeds._value;
                    if (data) {
                        return JSON.stringify(data);
                    }
                }
                return "";
            })()
            """
        )

        if not raw:
            return []

        if not isinstance(raw, str):
            raise FeedExplorerError("Search feed payload is not a JSON string.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FeedExplorerError(f"Failed to parse search feed JSON: {exc}") from exc

        if not isinstance(parsed, list):
            raise FeedExplorerError("Search feed payload is not a list.")
        return parsed

    def _extract_feed_detail(self, feed_id: str) -> dict[str, Any]:
        """Extract one feed detail object from noteDetailMap."""
        feed_literal = json.dumps(feed_id)
        raw = self._evaluate(f"""
            (() => {{
                const feedId = {feed_literal};
                const state = window.__INITIAL_STATE__;
                if (!state || !state.note || !state.note.noteDetailMap) {{
                    return "";
                }}

                const detailMap = state.note.noteDetailMap;
                if (detailMap[feedId]) {{
                    return JSON.stringify(detailMap[feedId]);
                }}

                const keys = Object.keys(detailMap || {{}});
                if (keys.length === 1 && detailMap[keys[0]]) {{
                    return JSON.stringify(detailMap[keys[0]]);
                }}
                return "";
            }})()
        """)

        if not raw:
            raise FeedExplorerError(
                f"Could not find feed detail for id '{feed_id}' in noteDetailMap."
            )

        if not isinstance(raw, str):
            raise FeedExplorerError("Feed detail payload is not a JSON string.")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FeedExplorerError(f"Failed to parse feed detail JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise FeedExplorerError("Feed detail payload is not an object.")
        return parsed

    def search_feeds(
        self,
        keyword: str,
        filters: SearchFilters | None = None,
    ) -> list[dict[str, Any]]:
        """Extract feed list from the current search page and apply optional filters."""
        _ = keyword  # kept for future keyword-aware diagnostics
        self._wait_for_search_state()

        if filters:
            filters.validate()
            values = self._option_ordered_values(filters)

            # Prefer a single hover session so multiple options are selected
            # within the same filter panel without resetting previous states.
            if values and self._move_mouse and self._click_mouse:
                ok, reason = self._apply_filters_in_single_panel(values)
                if not ok:
                    # Fallback path for page variants where hover structure differs.
                    for value in values:
                        self._apply_single_filter(value)
                else:
                    self._sleep(1.2, minimum_seconds=0.4)
                    self._wait_for_search_state()
            else:
                for value in values:
                    self._apply_single_filter(value)

        feeds = self._extract_search_feeds()
        if feeds:
            return feeds

        # On some page variants `search.feeds` is initialized as [] first and
        # filled asynchronously. Retry briefly before returning empty results.
        deadline = time.time() + 8.0
        while time.time() < deadline:
            self._sleep(0.6, minimum_seconds=0.2)
            feeds = self._extract_search_feeds()
            if feeds:
                return feeds
        return feeds

    def get_feed_detail(self, feed_id: str) -> dict[str, Any]:
        """Extract feed detail from the current feed detail page."""
        feed_id = feed_id.strip()
        if not feed_id:
            raise FeedExplorerError("feed_id cannot be empty.")
        self._wait_for_detail_state()
        return self._extract_feed_detail(feed_id)
