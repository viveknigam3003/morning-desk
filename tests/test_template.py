import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / "templates/morning-desk.html"


def script_of(html):
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert blocks, "template has no inline script"
    return blocks[0]


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_template_script_parses(tmp_path):
    js = tmp_path / "page.js"
    js.write_text(script_of(HTML.read_text()))
    subprocess.run(["node", "--check", str(js)], check=True)


def test_template_reads_meta_config():
    html = HTML.read_text()
    assert 'db.doc("meta/config")' in html


def test_template_has_neutral_defaults():
    html = HTML.read_text()
    for default in ["DEFAULT_CONFIG", 'ownerName: "the user"', 'channelName: ""',
                    'updateHeader: "Daily Update for {date}:"']:
        assert default in html, default


def test_template_keeps_core_sections():
    html = HTML.read_text()
    for marker in ['id="duCopy"', 'id="duRefresh"', 'id="sessPanel"', 'data-act="wontdo"', 'id="sortBy"', 'id="addForm"']:
        assert marker in html, marker


def run_pure(js_expr):
    """Evaluate an expression against the template's pure helpers (between /* pure:start */ and /* pure:end */)."""
    html = HTML.read_text()
    m = re.search(r"/\* pure:start \*/(.*?)/\* pure:end \*/", html, re.S)
    assert m, "template has no pure helper block"
    out = subprocess.run(["node", "-e", m.group(1) + f"\nconsole.log(JSON.stringify({js_expr}));"],
                         capture_output=True, text=True, check=True)
    import json
    return json.loads(out.stdout)


needs_node = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")


@needs_node
def test_partial_config_falls_back_per_field():
    c = run_pure('normalizeConfig({githubOrgs: null, updateHeader: null, channelName: 5, ownerName: "Sam"})')
    assert c["githubOrgs"] == [] and c["updateHeader"] == "Daily Update for {date}:"
    assert c["channelName"] == "" and c["ownerName"] == "Sam"


@needs_node
def test_org_prefix_escapes_and_ignores_case():
    r = run_pure('orgPrefix(["my.org"]).test("https://GITHUB.com/my.org/x") && !orgPrefix(["my.org"]).test("https://github.com/myXorg/x")')
    assert r is True


@needs_node
def test_desk_with_no_data_is_not_auto_drafted():
    assert run_pure("hasDeskData([], [])") is False
    assert run_pure('hasDeskData([{id: "a"}], [])') is True


def test_refresh_prompt_is_neutral_and_reads_style_rules():
    html = HTML.read_text()
    for gendered in ["he pastes", "WHAT HE", "what he actually", "lowercase 'i'"]:
        assert gendered not in html, gendered
    assert "CONFIG.styleRules" in html
    assert "for the your team channel" not in html
