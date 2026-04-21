import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class GrokBrowserExporter:
    def __init__(
        self,
        *,
        cdp_port: int = 9223,
        runner: "GrokBrowserRunner | None" = None,
    ) -> None:
        self._runner = runner or AgentBrowserGrokRunner(cdp_port=cdp_port)

    def export(self, output_dir: str | Path, *, page_size: int = 100) -> dict[str, Any]:
        base = Path(output_dir)
        base.mkdir(parents=True, exist_ok=True)
        responses_dir = base / "responses"
        responses_dir.mkdir(parents=True, exist_ok=True)

        conversations: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            payload = self._runner.fetch_conversations(page_size=page_size, page_token=page_token)
            batch = payload.get("conversations") or payload.get("items") or payload.get("results") or []
            if not isinstance(batch, list):
                raise ValueError("Grok conversation listing payload must contain a list")
            conversations.extend(item for item in batch if isinstance(item, dict))
            next_page = payload.get("nextPageToken")
            page_token = next_page if isinstance(next_page, str) and next_page else None
            if page_token is None:
                break

        retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (base / "conversations.index.json").write_text(
            json.dumps(
                {
                    "summary": {
                        "conversation_count": len(conversations),
                        "retrieved_at": retrieved_at,
                    },
                    "conversations": conversations,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        failures: list[dict[str, Any]] = []
        response_files_total = 0
        for conversation in conversations:
            conversation_id = conversation.get("conversationId") or conversation.get("id")
            if not isinstance(conversation_id, str) or not conversation_id:
                failures.append({"error": "missing conversation id", "conversation": conversation})
                continue
            try:
                responses_payload = self._runner.fetch_responses(conversation_id)
            except Exception as exc:  # pragma: no cover - exercised via fake runner tests if needed later
                failures.append({"conversation_id": conversation_id, "error": str(exc)})
                continue
            (responses_dir / f"{conversation_id}.responses.json").write_text(
                json.dumps(responses_payload, ensure_ascii=False, indent=2)
            )
            response_files_total += 1

        result = {
            "provider": "grok",
            "output_dir": str(base),
            "conversation_count": len(conversations),
            "response_files_total": response_files_total,
            "failure_count": len(failures),
            "failures": failures,
            "retrieved_at": retrieved_at,
        }
        (base / "responses.export.result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        (base / "manifest.json").write_text(
            json.dumps(
                {
                    "provider": "grok",
                    "acquisition_mode": "browser_automation_experimental",
                    "import_status": "raw_saved",
                    "retrieved_at": retrieved_at,
                    "conversation_count": len(conversations),
                    "response_files_total": response_files_total,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return result


class AgentBrowserGrokRunner:
    def __init__(self, *, cdp_port: int = 9223, command_runner: Callable[[list[str]], str] | None = None) -> None:
        self._cdp_port = cdp_port
        self._command_runner = command_runner or _run_agent_browser_json
        self._text_command_runner: Callable[[list[str]], str] = _run_agent_browser_text
        self._tab_prepared = False

    def fetch_conversations(self, *, page_size: int, page_token: str | None = None) -> dict[str, Any]:
        self._ensure_grok_tab()
        query = f"?pageSize={int(page_size)}"
        if page_token:
            query += f"&pageToken={json.dumps(page_token)[1:-1]}"
        js = (
            "fetch('https://grok.com/rest/app-chat/conversations"
            + query
            + "', {credentials: 'include'}).then(async (res) => ({status: res.status, body: await res.json()}))"
        )
        payload = self._eval_json(js)
        return _unwrap_agent_browser_payload(payload)

    def fetch_responses(self, conversation_id: str) -> dict[str, Any]:
        quoted_id = json.dumps(conversation_id)
        js = (
            f"fetch('https://grok.com/rest/app-chat/conversations/' + {quoted_id} + '/responses', "
            "{credentials: 'include'}).then(async (res) => ({status: res.status, body: await res.json()}))"
        )
        payload = self._eval_json(js)
        return _unwrap_agent_browser_payload(payload)

    def _eval_json(self, js: str) -> dict[str, Any]:
        return json.loads(
            self._command_runner([
                _resolve_agent_browser_executable(),
                "--cdp",
                str(self._cdp_port),
                "eval",
                js,
                "--json",
            ])
        )

    def _ensure_grok_tab(self) -> None:
        if self._tab_prepared:
            return
        executable = _resolve_agent_browser_executable()
        listing = self._text_command_runner([executable, "--cdp", str(self._cdp_port), "tab", "list"])
        for line in listing.splitlines():
            if "https://grok.com/" not in line:
                continue
            prefix = line.split("]", 1)[0]
            index = prefix.split("[")[-1].replace("→", "").strip()
            if index:
                self._text_command_runner([executable, "--cdp", str(self._cdp_port), "tab", index])
                self._tab_prepared = True
                return
        self._text_command_runner([executable, "--cdp", str(self._cdp_port), "open", "https://grok.com/"])
        self._tab_prepared = True


class GrokBrowserRunner:
    def fetch_conversations(self, *, page_size: int, page_token: str | None = None) -> dict[str, Any]: ...
    def fetch_responses(self, conversation_id: str) -> dict[str, Any]: ...


def _run_agent_browser_json(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def _run_agent_browser_text(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def _resolve_agent_browser_executable() -> str:
    env_override = os.environ.get("AGENT_BROWSER_BIN")
    if env_override:
        return env_override
    discovered = shutil.which("agent-browser")
    if discovered:
        return discovered
    candidates = [
        str(Path.home() / ".local" / "bin" / "agent-browser"),
        str(Path.home() / ".hermes" / "hermes-agent" / ".worktrees" / "local-dev-runtime" / "node_modules" / ".bin" / "agent-browser"),
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("agent-browser executable not found")


def _unwrap_agent_browser_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if "status" in payload and "body" in payload:
        if int(payload["status"]) != 200:
            raise ValueError(f"Grok browser export request failed: {payload['status']}")
        body = payload["body"]
        if not isinstance(body, dict):
            raise ValueError("Grok browser export body must be an object")
        return body
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        if "status" in data and "body" in data:
            return _unwrap_agent_browser_payload(data)
        result = data.get("result")
        if isinstance(result, dict):
            return _unwrap_agent_browser_payload(result)
    result = payload.get("result") if isinstance(payload, dict) else None
    if isinstance(result, dict) and "status" in result and "body" in result:
        return _unwrap_agent_browser_payload(result)
    raise ValueError("Unexpected agent-browser payload shape")
