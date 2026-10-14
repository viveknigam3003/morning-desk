from conftest import assistant, user, write_session

import scan_sessions as ss


def test_scan_summarises_a_session(projects):
    p = write_session(projects, "aaaaaaaa-1111", [
        {"type": "ai-title", "aiTitle": "Fix login bug"},
        user("Fix the login bug", "2026-10-14T08:00:00.000Z"),
        assistant("Opened https://github.com/acme/app/pull/42 for it.", "2026-10-14T08:05:00.000Z"),
    ])
    s = ss.scan(p)
    assert s["title"] == "Fix login bug"
    assert s["repo"] == "app"
    assert s["branch"] == "main"
    assert s["prs"] == ["https://github.com/acme/app/pull/42"]
    assert s["resume"] == 'cd "/home/u/code/app" && claude --resume aaaaaaaa-1111'


def test_meta_and_sidechain_prompts_are_ignored(projects):
    p = write_session(projects, "bbbb", [
        user("<command-name>/foo</command-name>", "2026-10-14T08:00:00Z"),
        user("internal", "2026-10-14T08:01:00Z", isMeta=True),
        user("subagent work", "2026-10-14T08:02:00Z", isSidechain=True),
    ])
    assert ss.scan(p) is None


def test_malformed_lines_are_skipped(projects):
    p = write_session(projects, "cccc", [
        "{not json",
        user("Real prompt", "2026-10-14T08:00:00Z"),
        '{"type": "user", "timestamp": "2026-10-14T08:0',
    ])
    s = ss.scan(p)
    assert s["promptCount"] == 1


def test_timestamp_formats():
    a = ss.parse_ts("2026-10-14T08:00:00.123Z")
    b = ss.parse_ts("2026-10-14T08:00:00+00:00")
    c = ss.parse_ts("2026-10-14T13:30:00+05:30")
    assert a is not None and abs(a - b) < 1 and abs(b - c) < 1
    assert ss.parse_ts("garbage") is None


def test_redacts_modern_token_shapes():
    for secret in ["github_pat_11ABCDEFG0123456789_abcdefghijklmnopqrstuvwxyz",
                   "xapp-1-A0123-4567-abcdef", "sk-ant-api03-abcdefghijklmnop",
                   "ghp_abcdefghijklmnopqrstuvwxyz0123", "AKIAABCDEFGHIJKLMNOP"]:
        assert secret not in ss.clean(f"token {secret} here", 500)


def test_collect_filters_by_activity_and_ignore_list(projects):
    write_session(projects, "old1", [user("old work", "2026-10-01T08:00:00Z")])
    write_session(projects, "new1", [user("new work", "2026-10-14T08:00:00Z")])
    write_session(projects, "skip", [user("personal", "2026-10-14T09:00:00Z")])
    since = ss.parse_ts("2026-10-10T00:00:00Z")
    out = ss.collect(projects.parent, since, {"skip"})
    assert [s["id"] for s in out] == ["new1"]


def test_odd_shaped_lines_do_not_crash(projects):
    p = write_session(projects, "dddd", [
        {"type": "user", "timestamp": "2026-10-14T08:00:00Z", "message": "hi"},
        {"type": "assistant", "timestamp": "2026-10-14T08:01:00Z",
         "message": {"content": [{"type": "text", "text": None}, {"type": "tool_use", "name": "Edit", "input": "x"},
                                 {"type": "tool_use", "name": "Write", "input": {"file_path": 7}}]}},
        user("Real prompt", "2026-10-14T08:02:00Z"),
    ])
    s = ss.scan(p)
    assert s["promptCount"] == 1 and s["filesTouched"] == []


def test_collect_survives_an_unreadable_file(projects, monkeypatch):
    write_session(projects, "good", [user("work", "2026-10-14T08:00:00Z")])
    write_session(projects, "bad1", [user("work", "2026-10-14T08:00:00Z")])
    real = ss.scan
    monkeypatch.setattr(ss, "scan", lambda f: (_ for _ in ()).throw(RuntimeError("boom")) if "bad1" in str(f) else real(f))
    out = ss.collect(projects.parent, ss.parse_ts("2026-10-10T00:00:00Z"), set())
    assert [s["id"] for s in out] == ["good"]


def test_corrupt_state_falls_back_and_commit_is_separate(projects, tmp_path, monkeypatch, capsys):
    home = tmp_path / "desk"
    home.mkdir()
    (home / "last_scan.json").write_text("{corrupt")
    monkeypatch.setattr(ss, "DESK_HOME", home)
    monkeypatch.setattr(ss, "STATE", home / "last_scan.json")
    monkeypatch.setattr(ss, "PENDING", home / "last_scan.pending.json")
    monkeypatch.setattr(ss, "IGNORE", home / "ignore.txt")
    monkeypatch.setattr(ss, "PROJECTS", projects.parent)
    ss.main([])
    assert (home / "last_scan.json").read_text() == "{corrupt"  # not advanced until --commit
    assert (home / "last_scan.pending.json").exists()
    ss.main(["--commit"])
    assert "scannedAt" in (home / "last_scan.json").read_text()


def test_since_hours_without_value_is_an_error():
    import pytest
    with pytest.raises(SystemExit):
        ss.main(["--since-hours"])
