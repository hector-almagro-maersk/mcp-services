import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from mcp.server.fastmcp import FastMCP


ISO_DATE_FMT = "%Y-%m-%d"


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def parse_changelog(changelog: str) -> List[Dict[str, Any]]:
    version_pattern = re.compile(r"^##+\s*\[?v?(\d+\.\d+\.\d+(?:-[^\]\s]+)?)\]?\s*-?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})?\s*$", re.MULTILINE)
    matches = list(version_pattern.finditer(changelog))
    changelog_entries = []
    for i, m in enumerate(matches):
        v = m.group(1)
        date = m.group(2) or None
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(changelog)
        section = changelog[start:end].strip()
        changes = {}
        type_pattern = re.compile(r"^###\s+([A-Za-z ]+)\s*$", re.MULTILINE)
        type_matches = list(type_pattern.finditer(section))
        for j, t in enumerate(type_matches):
            change_type = t.group(1).strip()
            t_start = t.end()
            t_end = type_matches[j+1].start() if j+1 < len(type_matches) else len(section)
            bullets = re.findall(r"^[-*]\s+(.*)$", section[t_start:t_end], re.MULTILINE)
            changes[change_type] = bullets
        changelog_entries.append({
            "version": v,
            "date": date,
            "changes": changes
        })
    return changelog_entries


def _load_json_env(var: str) -> Optional[Dict[str, Any]]:
    val = os.environ.get(var)
    if not val:
        return None
    try:
        return json.loads(val)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in {var}: {e}")


def get_rotation_config() -> Dict[str, Any]:
    """Load rotation configuration from env or config.json."""
    cfg = _load_json_env("MCP_ROTATION_CONFIG")
    if cfg:
        return cfg
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    raise Exception("No rotation configuration found. Set MCP_ROTATION_CONFIG or provide config.json")


def _parse_date(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, ISO_DATE_FMT)
    except ValueError:
        raise ValueError(f"Invalid date format for {field}: '{value}' (expected YYYY-MM-DD)")


def _normalize_overrides(overrides: Any) -> List[Dict[str, str]]:
    if overrides is None:
        return []
    if isinstance(overrides, dict):
        if "date" in overrides and "engineer" in overrides:
            return [overrides]
        else:
            raise ValueError("Override object missing 'date' or 'engineer'")
    if isinstance(overrides, list):
        norm: List[Dict[str, str]] = []
        for item in overrides:
            if not isinstance(item, dict) or "date" not in item or "engineer" not in item:
                raise ValueError("Each override must be an object with 'date' and 'engineer'")
            norm.append(item)
        return norm
    raise ValueError("Overrides must be a dict or list of dicts")


def _parse_override_pairs(raw: str) -> List[Dict[str, str]]:
    """Parse the new override string format.

    Expected format (single string):
        "Engineer One:2025-09-01,Engineer Two:2025-10-12"

    - Pairs separated by commas
    - Each pair = engineer name + ':' + ISO date (YYYY-MM-DD)
    - Whitespace around commas / colon is trimmed
    - Order is preserved; duplicates (same date+engineer) are ignored after first
    - Invalid pairs (missing colon, invalid date) raise ValueError
    """
    overrides: List[Dict[str, str]] = []
    if not raw.strip():
        return overrides
    pairs = [p.strip() for p in raw.split(',') if p.strip()]
    seen = set()
    for pair in pairs:
        if ':' not in pair:
            raise ValueError(f"Override pair missing colon: '{pair}'")
        # Engineer names may contain additional colons theoretically; use rsplit
        name, date_part = pair.rsplit(':', 1)
        name = name.strip()
        date_part = date_part.strip()
        if not name:
            raise ValueError(f"Engineer name missing in pair: '{pair}'")
        # Validate date
        _parse_date(date_part, 'override.date')
        key = (date_part, name)
        if key in seen:
            continue
        seen.add(key)
        overrides.append({"date": date_part, "engineer": name})
    return overrides


def _merge_overrides(base: List[Dict[str, str]], ad_hoc_pairs: Optional[str]) -> List[Dict[str, str]]:
    combined = list(base) if base else []
    if ad_hoc_pairs is not None:
        try:
            parsed_pairs = _parse_override_pairs(ad_hoc_pairs)
        except ValueError as e:
            raise ValueError(f"Invalid overrides format: {e}")
        combined.extend(parsed_pairs)
    # Deduplicate by (date, engineer) preserving order
    seen: set = set()
    dedup: List[Dict[str, str]] = []
    for o in combined:
        key = (o['date'], o['engineer'])
        if key not in seen:
            seen.add(key)
            dedup.append(o)
    return dedup


def _compute_engineer(engineers: List[str], start: datetime, rotation_days: int, target: datetime) -> Tuple[int, int]:
    """Return slot_index, engineer_index for baseline schedule (no overrides)."""
    if rotation_days <= 0:
        rotation_days = 7
    delta_days = (target - start).days
    # Support dates before start (negative) deterministically
    slot_index = delta_days // rotation_days if delta_days >= 0 else -((-delta_days) // rotation_days)  # floor division semantics
    engineer_index = slot_index % len(engineers)
    return slot_index, engineer_index


def _apply_overrides(overrides: List[Dict[str, str]], target: datetime) -> Optional[Dict[str, str]]:
    applicable = []
    for o in overrides:
        try:
            o_date = _parse_date(o["date"], "override.date")
        except ValueError:
            continue  # Skip invalid override dates silently
        if o_date <= target:
            applicable.append((o_date, o))
    if not applicable:
        return None
    # Most recent past override
    applicable.sort(key=lambda x: x[0])
    return applicable[-1][1]


def _engineer_for_date(cfg: Dict[str, Any], date_str: str, ad_hoc_overrides: Optional[str]) -> Dict[str, Any]:
    engineers = cfg.get("engineers") or []
    if not engineers:
        raise ValueError("Configuration must include non-empty 'engineers' list")
    start_date = cfg.get("start_date")
    if not start_date:
        raise ValueError("Configuration missing 'start_date'")
    rotation_days = int(cfg.get("rotation_days", 7) or 7)
    overrides_cfg = cfg.get("overrides", [])
    overrides = _merge_overrides(_normalize_overrides(overrides_cfg), ad_hoc_overrides)

    target_dt = _parse_date(date_str, "date")
    start_dt = _parse_date(start_date, "start_date")

    slot_index, engineer_index = _compute_engineer(engineers, start_dt, rotation_days, target_dt)
    schedule_engineer = engineers[engineer_index]

    applied_override = _apply_overrides(overrides, target_dt)
    source = "schedule"
    final_engineer = schedule_engineer
    if applied_override:
        # Determine if override is still within its natural span: until next schedule change after its date
        override_dt = _parse_date(applied_override["date"], "override.date")
        # Next schedule boundary after override start
        days_since_start = (override_dt - start_dt).days
        override_slot_idx = days_since_start // rotation_days if days_since_start >= 0 else -((-days_since_start)//rotation_days)
        # Start of following slot
        following_slot_start = start_dt + timedelta(days=(override_slot_idx + 1) * rotation_days)
        if target_dt < following_slot_start:
            final_engineer = applied_override["engineer"]
            source = "override"
    return {
        "date": date_str,
        "engineer": final_engineer,
        "source": source,
        "rotation_start": start_date,
        "rotation_days": rotation_days,
        "slot_index": slot_index,
        "engineer_index": engineer_index,
        "total_engineers": len(engineers),
        **({"applied_override": applied_override} if source == "override" else {})
    }


mcp = FastMCP("MCP On-Call Rotation")


@mcp.tool(description="Get engineer on duty for a given date (YYYY-MM-DD). Optional overrides string: 'Engineer A:YYYY-MM-DD,Engineer B:YYYY-MM-DD'.")
def get_oncall(date: str, overrides: Optional[str] = None) -> str:  # type: ignore[override]
    """Return engineer on duty (JSON string).

    Overrides format (if provided): single string with comma-separated pairs
        "Engineer One:2025-09-01,Engineer Two:2025-10-12"

    Each pair => engineer takes over starting at the given date until next schedule boundary
    (or a later override) consistent with existing semantics.
    """
    try:
        if overrides is not None and not isinstance(overrides, str):
            return json.dumps({"error": "Overrides must be a string in the format 'Name:YYYY-MM-DD,...'"})
        cfg = get_rotation_config()
        result = _engineer_for_date(cfg, date, overrides)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(description="Show the current MCP version and the full changelog as structured JSON.")
def show_version() -> str:
    try:
        version_path = os.path.join(os.path.dirname(__file__), "VERSION")
        changelog_path = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")
        version = "0.1.0"
        if os.path.exists(version_path):
            version = read_file(version_path).strip()
        changelog_entries = []
        if os.path.exists(changelog_path):
            changelog_entries = parse_changelog(read_file(changelog_path))
        config_source = "MCP_ROTATION_CONFIG env var" if os.environ.get("MCP_ROTATION_CONFIG") else ("config.json file" if os.path.exists(os.path.join(os.path.dirname(__file__), "config.json")) else "none")
        return json.dumps({
            "current_version": version,
            "changelog": changelog_entries,
            "rotation_config": {"config_source": config_source}
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Error reading version or changelog: {e}"})


if __name__ == "__main__":
    mcp.run()
