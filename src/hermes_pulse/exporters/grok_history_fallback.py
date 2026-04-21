import json
import shutil
import sqlite3
import tempfile
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


CHROME_EPOCH_OFFSET = 11644473600000000


class ChromeHistoryGrokExporter:
    def export(self, history_db_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
        history_db_path = Path(history_db_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        rows = list(_read_history_rows(history_db_path))
        conversations = _normalize_grok_conversations(rows)
        retrieved_at = _iso_now()

        index_payload = {
            "summary": {
                "conversation_count": len(conversations),
                "retrieved_at": retrieved_at,
            },
            "conversations": conversations,
        }
        (output_dir / "conversations.index.json").write_text(json.dumps(index_payload, ensure_ascii=False, indent=2))

        manifest = {
            "provider": "grok",
            "acquisition_mode": "local_browser_history",
            "import_status": "raw_saved",
            "history_db_path": str(history_db_path),
            "retrieved_at": retrieved_at,
            "conversation_count": len(conversations),
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        return manifest


def _read_history_rows(history_db_path: Path) -> Iterable[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="grok-history-") as temp_dir:
        copied = Path(temp_dir) / "History"
        shutil.copy2(history_db_path, copied)
        connection = sqlite3.connect(copied)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """
                select url, title, last_visit_time, visit_count
                from urls
                where url like 'https://grok.com/%'
                order by last_visit_time desc, id desc
                """
            ).fetchall()
        finally:
            connection.close()
    for row in rows:
        yield dict(row)



def _normalize_grok_conversations(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    conversations: dict[str, dict[str, Any]] = {}
    for row in rows:
        parsed = _parse_grok_conversation_url(str(row.get("url") or ""))
        if parsed is None:
            continue
        conversation_id, canonical_url, normalized_variant = parsed
        conversation = conversations.setdefault(
            conversation_id,
            {
                "conversationId": conversation_id,
                "title": None,
                "canonicalUrl": canonical_url,
                "urlVariants": [],
                "visitCount": 0,
                "modifyTime": None,
            },
        )
        if normalized_variant not in conversation["urlVariants"]:
            conversation["urlVariants"].append(normalized_variant)
        conversation["visitCount"] += int(row.get("visit_count") or 0)
        modify_time = _chrome_time_to_iso(row.get("last_visit_time"))
        if modify_time and (conversation["modifyTime"] is None or modify_time > conversation["modifyTime"]):
            conversation["modifyTime"] = modify_time
        title = _normalize_grok_title(row.get("title"))
        if title and (conversation["title"] in {None, "Grok"}):
            conversation["title"] = title

    ordered = sorted(
        conversations.values(),
        key=lambda item: (str(item.get("modifyTime") or ""), str(item.get("conversationId") or "")),
        reverse=True,
    )
    for item in ordered:
        item["urlVariants"] = sorted(item["urlVariants"])
    return ordered



def _parse_grok_conversation_url(url: str) -> tuple[str, str, str] | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "grok.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or parts[0] != "c" or not parts[1]:
        return None
    conversation_id = parts[1]
    canonical = urlunparse((parsed.scheme, parsed.netloc, f"/c/{conversation_id}", "", "", ""))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if "rid" in query:
        normalized_variant = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode({"rid": query['rid']}), ""))
    else:
        normalized_variant = canonical
    return conversation_id, canonical, normalized_variant



def _normalize_grok_title(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    title = value.strip()
    if not title:
        return None
    if title.endswith(" - Grok"):
        title = title[: -len(" - Grok")].rstrip()
    return title or None



def _chrome_time_to_iso(value: Any) -> str | None:
    try:
        chrome_time = int(value)
    except (TypeError, ValueError):
        return None
    if chrome_time <= 0:
        return None
    unix_microseconds = chrome_time - CHROME_EPOCH_OFFSET
    unix_seconds = unix_microseconds / 1_000_000
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')



def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
