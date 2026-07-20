#!/usr/bin/env python3
"""Robustness gate for the four hardening fixes.

1. Binary formats are refused, not decoded to mojibake and sent to the API.
2. BOM-declared UTF-16/32 decodes to real text instead of NUL-riddled garbage.
3. Pipeline state files (meta/inbox.md, meta/log.md) are not model-writable.
4. Permanently unprocessable files are recorded so they stop retrying forever;
   transient failures stay retryable.

Exits non-zero on regression.
"""
import codecs
import importlib.util
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

os.environ.setdefault("ANTHROPIC_API_KEY", "dummy-for-import")
spec = importlib.util.spec_from_file_location(
    "abap_ingest", os.path.join(os.path.dirname(HERE), "abap-ingest.py")
)
ing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ing)

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    line = f"  {'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  — {detail}"
    print(line)


print("\n=== 1. Binary formats refused, not fed to the API ===")
tmp = tempfile.mkdtemp(prefix="robust-")
zip_path = os.path.join(tmp, "archive.zip")
with zipfile.ZipFile(zip_path, "w") as z:
    z.writestr("a.txt", "hello" * 200)
check("ZIP refused", ing.read_as_text(zip_path, "archive.zip") is None)

png_path = os.path.join(tmp, "raw.bin")
with open(png_path, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 20)
check("binary blob refused", ing.read_as_text(png_path, "raw.bin") is None)

# an ELF-ish / control-heavy file with no NULs must still be caught by ratio
ctrl_path = os.path.join(tmp, "ctrl.bin")
with open(ctrl_path, "wb") as f:
    f.write(bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07] * 500))
check("control-byte-heavy blob refused", ing.read_as_text(ctrl_path, "ctrl.bin") is None)

print("\n=== 1b. Real text is NOT falsely refused ===")
for name, data, label in [
    ("utf8.txt", "Decision: use BAPI. Owner: Anna Larsen.".encode("utf-8"), "utf-8"),
    ("latin1.txt", "Café Müller GmbH - naming".encode("latin-1"), "latin-1"),
    ("tabs.csv", b"a\tb\tc\r\nOTC\t5\t7\r\n", "utf-8"),
    ("abap.txt", b"REPORT zsd_order_check.\nWRITE: / 'x'.\n", "utf-8"),
]:
    p = os.path.join(tmp, name)
    open(p, "wb").write(data)
    got = ing.read_as_text(p, name)
    check(f"{name} still read", got is not None and len(got) > 5)

empty = os.path.join(tmp, "empty.txt")
open(empty, "wb").write(b"")
check("empty file is not misjudged binary", ing.read_as_text(empty, "empty.txt") == "")

print("\n=== 2. BOM-declared encodings decode to real text ===")
SAMPLE = "Decision: use BAPI approach\nOwner: Anna Larsen"
for label, enc in [("utf-16", "utf-16"), ("utf-16-be", "utf-16-be"),
                   ("utf-32", "utf-32"), ("utf-8-sig", "utf-8-sig")]:
    p = os.path.join(tmp, f"{label}.txt")
    raw = SAMPLE.encode(enc)
    if enc == "utf-16-be":
        raw = codecs.BOM_UTF16_BE + raw
    open(p, "wb").write(raw)
    got = ing.read_as_text(p, f"{label}.txt") or ""
    check(f"{label} decodes cleanly",
          "Decision: use BAPI approach" in got and "\x00" not in got,
          repr(got[:40]))

check("UTF-32-LE not mis-read as UTF-16",
      "Anna Larsen" in (ing.read_as_text(os.path.join(tmp, "utf-32.txt"), "x") or ""))

print("\n=== 3. Pipeline state files are not model-writable ===")
check("meta/inbox.md blocked", not ing.is_valid_vault_path("meta/inbox.md"))
check("meta/log.md blocked", not ing.is_valid_vault_path("meta/log.md"))
check("./meta/inbox.md blocked (normalized)", not ing.is_valid_vault_path("./meta/inbox.md"))
check("meta/x/../inbox.md blocked (normalized)",
      not ing.is_valid_vault_path("meta/x/../inbox.md"))
check("meta/entities.md still allowed", ing.is_valid_vault_path("meta/entities.md"))
check("meta/index.md still allowed", ing.is_valid_vault_path("meta/index.md"))
check("normal vault page still allowed",
      ing.is_valid_vault_path("02-workstreams/Workstreams/OTC.md"))
check("CLAUDE.md still blocked", not ing.is_valid_vault_path("CLAUDE.md"))
check("traversal still blocked", not ing.is_valid_vault_path("../../etc/passwd"))

print("\n=== 3b. apply_vault_changes refuses to write protected paths ===")
sandbox = tempfile.mkdtemp(prefix="robust-vault-")
cwd = os.getcwd()
os.chdir(sandbox)
try:
    os.makedirs("meta", exist_ok=True)
    os.makedirs("raw/inbox", exist_ok=True)
    open("meta/inbox.md", "w").write("| File | Date | Hash | Updated | Created |\n")
    open("meta/log.md", "w").write("# Log\n")
    before_inbox = open("meta/inbox.md").read()
    ing.apply_vault_changes({
        "updates": [{"path": "meta/inbox.md", "content": "CLOBBERED"},
                    {"path": "meta/log.md", "content": "CLOBBERED"}],
        "creates": [{"path": "02-workstreams/Workstreams/OTC.md", "content": "ok"}],
        "index_entries": [], "log_entry": "",
    }, "some-file.txt", log_only=True)
    check("inbox.md not clobbered", open("meta/inbox.md").read() == before_inbox)
    check("log.md not clobbered", "CLOBBERED" not in open("meta/log.md").read())
    check("legitimate page still written",
          os.path.exists("02-workstreams/Workstreams/OTC.md"))

    print("\n=== 4. Permanent vs transient unprocessable ===")
    open("raw/inbox/broken.vsd", "wb").write(b"\x00\x01binary")
    ing.log_unprocessable("broken.vsd", "unsupported format", permanent=True)
    recs = ing.get_processed_records()
    check("permanent failure recorded in inbox.md", "broken.vsd" in recs)
    check("recorded with real hash (so a replacement re-triggers)",
          recs.get("broken.vsd") not in (None, "", "—"))
    check("permanent failure will be skipped next run",
          ing.is_already_processed("broken.vsd", "raw/inbox/broken.vsd"))
    check("permanent failure not in unprocessed sweep",
          "broken.vsd" not in ing.scan_inbox_for_unprocessed())

    log_after_first = open("meta/log.md").read()
    check("permanent failure logged once", log_after_first.count("broken.vsd") == 1)

    open("raw/inbox/flaky.txt", "wb").write(b"real text content here")
    ing.log_unprocessable("flaky.txt", "ingest agent failed", permanent=False)
    check("transient failure NOT recorded in inbox.md",
          "flaky.txt" not in ing.get_processed_records())
    check("transient failure still retried",
          "flaky.txt" in ing.scan_inbox_for_unprocessed())

    # replacing a permanently-failed file makes it eligible again
    open("raw/inbox/broken.vsd", "wb").write(b"now it is real text, fixed by curator")
    check("replaced file becomes eligible again",
          "broken.vsd" in ing.scan_inbox_for_unprocessed())
finally:
    os.chdir(cwd)
    shutil.rmtree(sandbox, ignore_errors=True)
    shutil.rmtree(tmp, ignore_errors=True)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{'=' * 55}\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
if failed:
    print("FAILED: " + "; ".join(failed))
sys.exit(1 if failed else 0)
