#!/usr/bin/env python3
"""Author tool (DVR4 step 3; plan section 3.5, D-L3 (a)): seal Lab alpha's R13/R14-derived
tasks into Hidden/labs/R12/tasks.tar.age.

  seal_sealed.py ROOT

Every admitted family under sealed/families/ contributes its tasks: labs/R12/<task>/tasks/
<task>.dfy|.rs and labs/R12/<task>/ADMISSION.json, listed with their sha256 in
labs/R12/MANIFEST.sha256. The tree is written as one deterministic tar stream (sorted
names, mtime 0, uid/gid 0, mode 0644), encrypted with the pinned age binary
(~/.local/bin/age, sha256 as in sandbox/truth.toml) to the hidden-labs recipient
sandbox/truth.toml pins, and its pins are written to Hidden/labs/R12/SEALED.toml
(archive sha256, file count, manifest sha256, task ids with their source and admission
sha256). It never decrypts and never writes a sealed form into a learner-visible path."""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]).resolve()
AGE = Path.home() / ".local/bin/age"


def sha(b):
    return hashlib.sha256(b).hexdigest()


truth = tomllib.loads((ROOT / "sandbox/truth.toml").read_text())
lab = next(l for l in truth["lab"] if l["id"] == "Q15")          # the one hidden-labs key
assert sha(AGE.read_bytes()) == lab["age_sha256"], "age binary differs from its pin"
recipient = lab["recipient"]
files, rows = {}, []
for fp in sorted((HERE / "sealed/families").glob("*.json")):
    fam = json.loads(fp.read_text())
    if fam.get("status") != "admitted":
        continue
    for tid in fam["tasks"]:
        d = HERE / "sealed" / tid
        form = next((d / "tasks").glob(tid + ".*"))
        adm = json.loads((d / "ADMISSION.json").read_text())
        assert adm["status"] == "admitted" and adm["source_sha256"] == sha(form.read_bytes()), tid
        files[f"labs/R12/{tid}/tasks/{form.name}"] = form.read_bytes()
        files[f"labs/R12/{tid}/ADMISSION.json"] = (d / "ADMISSION.json").read_bytes()
        rows.append({"id": tid, "cluster": fam["cluster"], "source_sha256": sha(form.read_bytes()),
                     "admission_sha256": sha((d / "ADMISSION.json").read_bytes()), "file": form.name})
manifest = "".join(f"{sha(b)}  {n}\n" for n, b in sorted(files.items())).encode()
files["labs/R12/MANIFEST.sha256"] = manifest
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
    for name in sorted(files):
        ti = tarfile.TarInfo(name)
        ti.size, ti.mtime, ti.mode, ti.uid, ti.gid = len(files[name]), 0, 0o644, 0, 0
        tf.addfile(ti, io.BytesIO(files[name]))
out = ROOT / "Hidden/labs/R12/tasks.tar.age"
out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([str(AGE), "-r", recipient, "-o", str(out)], input=buf.getvalue(), check=True)
lines = ["# Hidden/labs/R12/SEALED.toml: the pins of Lab alpha's sealed R13/R14-derived tasks",
         "# (Solutions/plans/drafts/R12/lab-corpus-v2/seal_sealed.py; plan section 3.5, D-L3 (a)).",
         "schema = 1", 'lab = "R12"', 'archive = "Hidden/labs/R12/tasks.tar.age"',
         f'archive_sha256 = "{sha(out.read_bytes())}"', f'recipient = "{recipient}"',
         f"files = {len(files)}", f'manifest_sha256 = "{sha(manifest)}"']
for r in rows:
    lines += ["", "[[task]]"] + [f"{k} = {json.dumps(v)}" for k, v in r.items()]
(ROOT / "Hidden/labs/R12/SEALED.toml").write_text("\n".join(lines) + "\n")
print(f"sealed {len(rows)} task(s), {len(files)} file(s) -> {out.relative_to(ROOT)}")
