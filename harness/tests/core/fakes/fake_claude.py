"""A fake Claude Code CLI for fvh's backend tests (DV4-PLAN §9). It never calls a
model: it prints a stream-json event stream with neutral content, in the shape
of DV0's recorded policy call (infra/claude-p-design-argv-stream: the init,
assistant, rate_limit_event and result events and the keys fvh reads), and
records how it was called.

The test copies this file into a throwaway HOME (with a shebang naming the test's
own interpreter), pins its sha256 in a throwaway apparatus file, and steers it
through `fake-control.json` beside the copy:

  proposal        the structured output (default: one stop action)
  rate_limit      the rate_limit_info object, or null for no rate_limit_event
  init            keys that replace the init event's
  result          keys that replace the result event's
  no_result       print no result event (a crash after output)
  exit            the exit code (default 0)
  touch           leave a file in the working directory
  synthetic       print the assistant event as the CLI's own message (model
                  "<synthetic>") with this text, as an unauthenticated call does

Each call appends one line to `calls.jsonl` beside the copy: argv, the
environment, the working directory, and the credentials file it was given (its
keys and mode, never a value's content beyond the fake test values).
"""

import json
import os
import stat
import sys
from pathlib import Path

here = Path(__file__).resolve()
ctl_path = here.parent / "fake-control.json"
ctl = json.loads(ctl_path.read_text()) if ctl_path.exists() else {}
args = sys.argv[1:]


def opt(name):
    return args[args.index(name) + 1] if name in args else None


cred = Path(os.environ.get("CLAUDE_CONFIG_DIR", "/nonexistent")) / ".credentials.json"
cred_info = None
if cred.exists():
    cred_info = {"mode": stat.S_IMODE(cred.stat().st_mode), "data": json.loads(cred.read_text())}
with (here.parent / "calls.jsonl").open("a") as fh:
    fh.write(json.dumps({"argv": args, "env": dict(os.environ), "cwd": os.getcwd(),
                         "cwd_entries": sorted(os.listdir(".")), "credentials": cred_info})
             + "\n")
if ctl.get("touch"):
    Path("left-behind.txt").write_text("x")

init = {"type": "system", "subtype": "init", "cwd": os.getcwd(), "tools": ["StructuredOutput"],
        "mcp_servers": [], "model": opt("--model"), "permissionMode": "default",
        "apiKeySource": "none", "claude_code_version": ctl.get("version", "0.0.0-fake"),
        "plugins": [], "skills": [], "session_id": "fake-session"}
init.update(ctl.get("init", {}))
print(json.dumps(init))
if ctl.get("synthetic"):           # a message the CLI writes itself (model "<synthetic>")
    print(json.dumps({"type": "assistant", "message": {
        "model": "<synthetic>", "content": [{"type": "text", "text": ctl["synthetic"]}]}}))
else:
    print(json.dumps({"type": "assistant", "message": {"content": [{"type": "text",
                                                                     "text": "(fake)"}]}}))
info = ctl.get("rate_limit", {"status": "allowed", "resetsAt": 1, "rateLimitType": "five_hour",
                              "overageStatus": "rejected",
                              "overageDisabledReason": "org_level_disabled",
                              "isUsingOverage": False,
                              "unifiedWindows": {"five_hour": {"utilization": 0.1, "resetsAt": 1},
                                                 "seven_day": {"utilization": 0.2,
                                                               "resetsAt": 1}}})
if info is not None:
    print(json.dumps({"type": "rate_limit_event", "rate_limit_info": info}))
if not ctl.get("no_result"):
    result = {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
              "api_error_status": None, "result": "",
              "structured_output": ctl.get("proposal", {"actions": [{"type": "stop",
                                                                     "reason": "give-up"}]}),
              "usage": {"input_tokens": 3, "cache_creation_input_tokens": 10,
                        "cache_read_input_tokens": 0, "output_tokens": 7},
              "modelUsage": {}, "permission_denials": [], "total_cost_usd": 0.0}
    result.update(ctl.get("result", {}))
    print(json.dumps(result))
sys.exit(int(ctl.get("exit", 0)))
