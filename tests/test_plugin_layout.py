import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def frontmatter(path):
    """Parse the simple `key: value` YAML frontmatter used by commands and skills."""
    text = pathlib.Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def test_manifests_are_valid_json_and_consistent():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    assert plugin["name"] == "morning-desk"
    assert plugin["license"] == "MIT"
    assert market["plugins"][0]["name"] == plugin["name"]
    assert market["plugins"][0]["source"] == "./"


SKILLS = ["morning-desk", "desk-setup", "desk-refresh", "desk-sync", "daily-update"]
COMMANDS = ["desk-setup", "desk-refresh", "desk-sync"]


def test_skills_have_frontmatter():
    for name in SKILLS:
        fm = frontmatter(ROOT / f"skills/{name}/SKILL.md")
        assert fm.get("name") == name
        assert len(fm.get("description", "")) > 40


def test_commands_have_descriptions():
    for name in COMMANDS:
        assert frontmatter(ROOT / f"commands/{name}.md").get("description")


def test_every_skill_states_the_never_send_rule():
    for name in SKILLS:
        assert "Never send" in (ROOT / f"skills/{name}/SKILL.md").read_text(), name


def test_refresh_skill_handles_missing_tracker():
    text = (ROOT / "skills/desk-refresh/SKILL.md").read_text()
    assert "If no tracker is configured, skip tickets" in text
    assert "Jira" not in text.split("Tracker")[0], "refresh must not assume Jira before the tracker section"


def test_config_example_lists_all_keys():
    text = (ROOT / "templates/config.example.yaml").read_text()
    for key in ["desk_url", "slack_user_id", "slack_workspace", "update_channel", "update_cadence",
                "timezone", "github_orgs", "tracker", "close_merged_tickets"]:
        assert key in text, key


def test_refresh_owns_the_scan_window_and_commits_after_writing():
    text = (ROOT / "skills/desk-refresh/SKILL.md").read_text()
    assert "--since-hours 168" in text
    assert "scan_sessions.py --commit" in text


def test_setup_uses_plugin_root_for_bundled_files():
    text = (ROOT / "skills/desk-setup/SKILL.md").read_text()
    for f in ["templates/config.example.yaml", "templates/style.default.md", "templates/morning-desk.html"]:
        for line in text.splitlines():
            if f in line:
                assert "${CLAUDE_PLUGIN_ROOT}/" + f in line, line


def test_sync_prompt_uses_absolute_scanner_path():
    text = (ROOT / "skills/desk-sync/SKILL.md").read_text()
    assert "absolute path" in text and "--commit" in text
