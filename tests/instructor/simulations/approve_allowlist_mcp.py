#!/usr/bin/env python3
"""approve_allowlist_mcp.py: a stdio MCP server whose one tool is a permission
handler for headless `/contract` simulations (skill_sims.py, case f).

Claude Code treats `.claude/state/contract-allowlist` as a sensitive file: an
interactive session asks the learner to approve each write, and a headless
`claude -p` run cannot show that prompt, so allow rules do not help. Passed as
`--permission-prompt-tool mcp__approver__approve`, this server stands in for the
learner's click: it approves a Write or Edit whose `file_path` is exactly
`<ALLOWLIST_PATH>` and denies every other request. Each request and decision is
appended to `<APPROVER_LOG>` (one JSON line; the tool input's content as a
length only).

Environment: ALLOWLIST_PATH (absolute path), APPROVER_LOG (absolute path).
"""

import json
import os
import sys

ALLOW = os.environ.get("ALLOWLIST_PATH", "")
LOG = os.environ.get("APPROVER_LOG", "")
TOOL = {
    "name": "approve",
    "description": "Permission handler for the course's skill simulations: approves only a "
                   "Write or Edit of the contract allowlist file.",
    "inputSchema": {"type": "object",
                    "properties": {"tool_name": {"type": "string"}, "input": {"type": "object"},
                                   "tool_use_id": {"type": "string"}},
                    "required": ["tool_name", "input"]},
}


def log(entry):
    if LOG:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def decide(args):
    name = args.get("tool_name")
    tin = args.get("input") or {}
    path = tin.get("file_path")
    ok = (name in ("Write", "Edit") and bool(ALLOW) and isinstance(path, str)
          and os.path.normpath(path) == os.path.normpath(ALLOW))
    log({"tool_name": name, "file_path": path,
         "content_chars": len(tin.get("content") or tin.get("new_string") or ""),
         "decision": "allow" if ok else "deny"})
    if ok:
        return {"behavior": "allow", "updatedInput": tin}
    return {"behavior": "deny",
            "message": "Not approved: this simulated learner approves only writes to the "
                       "contract allowlist file."}


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, mid = req.get("method"), req.get("id")
        if mid is None:
            continue   # a notification
        if method == "initialize":
            pv = (req.get("params") or {}).get("protocolVersion", "2024-11-05")
            reply(mid, {"protocolVersion": pv, "capabilities": {"tools": {}},
                        "serverInfo": {"name": "approver", "version": "1"}})
        elif method == "tools/list":
            reply(mid, {"tools": [TOOL]})
        elif method == "tools/call":
            p = req.get("params") or {}
            if p.get("name") != "approve":
                reply(mid, error={"code": -32602, "message": "unknown tool"})
                continue
            reply(mid, {"content": [{"type": "text",
                                     "text": json.dumps(decide(p.get("arguments") or {}))}]})
        elif method == "ping":
            reply(mid, {})
        else:
            reply(mid, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    main()
