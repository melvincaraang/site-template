"""Guards against the two deploy-only failures a local test run cannot see.

1. A route in api/app.py with no matching API Gateway event in template.yaml is
   unreachable in production (SAM enumerates events explicitly).
2. SAM installs dependencies from backend/requirements.txt (the CodeUri root),
   not api/requirements.txt, so the two must stay identical.
"""

import re
from pathlib import Path

from api import app

ROOT = Path(__file__).resolve().parents[2]


def _routes_from_code() -> set[tuple[str, str]]:
    """Convert each ROUTES regex into an API Gateway style (METHOD, /path/{param})."""
    out = set()
    for method, pattern, _handler_name in app.ROUTES:
        path = pattern.lstrip("^").rstrip("$")
        path = re.sub(r"\(\?P<(\w+)>[^)]*\)", r"{\1}", path)
        out.add((method, path))
    return out


def _routes_from_template() -> set[tuple[str, str]]:
    text = (ROOT / "template.yaml").read_text()
    events = re.findall(r"Path:\s*\"?([^\s\"]+)\"?\s*\n\s*Method:\s*(\w+)", text)
    return {(method.upper(), path) for path, method in events}


def test_every_route_has_a_sam_event_and_vice_versa():
    code, template = _routes_from_code(), _routes_from_template()
    assert code - template == set(), f"routes missing from template.yaml: {sorted(code - template)}"
    assert template - code == set(), f"template.yaml events with no handler: {sorted(template - code)}"


def test_sam_requirements_match_api_requirements():
    root_reqs = (ROOT / "requirements.txt").read_text().split()
    api_reqs = (ROOT / "api" / "requirements.txt").read_text().split()
    assert root_reqs == api_reqs, (
        "backend/requirements.txt must mirror api/requirements.txt (SAM reads the root one)"
    )


def test_template_param_names_match_handler_env_vars():
    """Every os.environ[...] key the handlers read must be wired in template.yaml Globals."""
    src = "".join(p.read_text() for p in (ROOT / "api").glob("*.py"))
    keys = set(re.findall(r'os\.environ(?:\.get)?\(?\["?([A-Z_]+)"?', src))
    keys |= set(re.findall(r'os\.environ\.get\("([A-Z_]+)"', src))
    template = (ROOT / "template.yaml").read_text()
    missing = {k for k in keys if f"{k}:" not in template}
    assert missing == set(), f"env vars read by handlers but not set in template.yaml: {sorted(missing)}"
