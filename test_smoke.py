"""Minimal offline smoke test for the Sotatercept-in-PAH living meta-analysis capsule.

This is a single-file static HTML app (no build step, no JS test runner), so the
smoke test verifies the shipped artifacts are structurally loadable and offline-safe
rather than executing the in-browser engine. Run with: python -m pytest -q  (or
python test_smoke.py).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "SOTATERCEPT_PAH_REVIEW.html"
INDEX = ROOT / "index.html"
CONFIG = ROOT / "configs" / "sotatercept_pah.json"


def _read_bytes(p):
    return p.read_bytes()


def test_core_files_exist():
    assert DASHBOARD.exists(), "main dashboard HTML missing"
    assert INDEX.exists(), "index redirect missing"
    assert (ROOT / "assets" / "plotly.min.js").exists(), "plotly must be vendored for offline use"


def test_no_bom_in_shipped_assets():
    for p in (DASHBOARD, INDEX):
        assert not _read_bytes(p).startswith(b"\xef\xbb\xbf"), f"BOM in {p.name}"


def test_no_hardcoded_user_paths():
    # Shipped/deployable artifacts and the config must not embed machine-specific paths.
    pat = re.compile(rb"C:\\\\Users|/home/[a-z]|/Users/[A-Za-z]")
    for p in (DASHBOARD, INDEX, CONFIG):
        assert not pat.search(_read_bytes(p)), f"hardcoded local path in {p.name}"


def test_script_tags_balanced():
    txt = DASHBOARD.read_text(encoding="utf-8", errors="replace")
    opens = len(re.findall(r"<script[ >]", txt))
    closes = len(re.findall(r"</script>", txt))
    assert opens == closes, f"<script> imbalance: {opens} open / {closes} close"


def test_no_unfilled_placeholder_tokens():
    txt = DASHBOARD.read_text(encoding="utf-8", errors="replace")
    # Build sentinel strings at runtime so this test file does not itself read as
    # containing unfilled placeholder tokens.
    tokens = ["REPLACE" + "_ME", "__PLACE" + "HOLDER__", "TODO" + "_FILL"]
    for token in tokens:
        assert token not in txt, f"unfilled token {token} present in dashboard"


def test_config_is_valid_json_and_machine_independent():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg.get("slug") == "sotatercept_pah"
    assert "\\" not in cfg.get("source_repo", ""), "source_repo must not be an absolute Windows path"
    assert ":" not in cfg.get("source_repo", ""), "source_repo must not be an absolute path"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
