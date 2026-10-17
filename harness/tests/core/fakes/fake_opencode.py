"""A fake opencode CLI for fvh's backend tests (DV4-PLAN §9). It never calls a
model and opens no connection. `debug agent build --pure` and `debug config
--pure` print JSON in the shape of DV0's recorded isolation probe
(infra/opencode-iso-config-B3: a `tools` table and a `permission` list; the
resolved config); `run` prints JSON-lines events in the shape fvh's parser
assumes until DV4 step 3c probes it ("text" events with `part.text`,
"step_finish" events with `part.tokens`).

Steered by `fake-control.json` beside the copy:
  reply           the reply text of `run` (default: one stop action as JSON)
  tools_on        tool names `debug agent build` reports as enabled
  allow_external  an external_directory allow pattern to report
  extra_url       a second provider URL for `debug config` to report
  exit            the exit code of `run`
Each call appends one line to `calls.jsonl` beside the copy.
"""

import json
import os
import sys
from pathlib import Path

here = Path(__file__).resolve()
ctl_path = here.parent / "fake-control.json"
ctl = json.loads(ctl_path.read_text()) if ctl_path.exists() else {}
args = sys.argv[1:]
with (here.parent / "calls.jsonl").open("a") as fh:
    fh.write(json.dumps({"argv": args, "env": dict(os.environ), "cwd": os.getcwd()}) + "\n")

if args[:3] == ["debug", "agent", "build"]:
    names = ("bash", "read", "glob", "grep", "edit", "write", "task", "webfetch")
    tools = {n: n in ctl.get("tools_on", []) for n in names}
    perm = [{"permission": "*", "action": "deny", "pattern": "*"},
            {"permission": "external_directory", "action": "allow",
             "pattern": os.environ["XDG_DATA_HOME"] + "/opencode/tool-output/*"}]
    if ctl.get("allow_external"):
        perm.append({"permission": "external_directory", "action": "allow",
                     "pattern": ctl["allow_external"]})
    print(json.dumps({"name": "build", "permission": perm, "tools": tools}, indent=2))
    sys.exit(0)
if args[:2] == ["debug", "config"]:
    conf = json.loads(Path(os.environ["OPENCODE_CONFIG"]).read_text())
    if ctl.get("extra_url"):
        conf["provider"]["other"] = {"options": {"baseURL": ctl["extra_url"]}}
    print(json.dumps(conf, indent=2))
    sys.exit(0)
if args[:1] == ["run"]:
    reply = ctl.get("reply", json.dumps({"actions": [{"type": "stop", "reason": "give-up"}]}))
    half = len(reply) // 2
    for chunk in (reply[:half], reply[half:]):
        print(json.dumps({"type": "text", "part": {"type": "text", "text": chunk}}))
    print(json.dumps({"type": "step_finish", "part": {"tokens": {"input": 11, "output": 5}}}))
    sys.exit(int(ctl.get("exit", 0)))
sys.exit(2)
