import subprocess

import assistants as a


def test_no_tools_no_hooks_and_only_the_question_is_sent():
    cmd = a.ask_cmd("claude", "hava nasıl?", "tr")
    assert cmd[cmd.index("-p") + 1] == "hava nasıl?"
    assert cmd[cmd.index("--tools") + 1] == ""
    assert "--restricted" in cmd and "--bare" not in cmd  # --bare would skip the user's login
    assert not any("dangerously" in c or "bypass" in c for c in cmd)


def test_missing_or_failing_claude_gives_none():
    assert a.ask_claude("x", which=lambda _: None) is None
    fail = lambda *a_, **k: subprocess.CompletedProcess([], 1, "", "not logged in")
    assert a.ask_claude("x", which=lambda _: "claude", run=fail) is None


def test_long_answers_are_cut_for_the_bubble():
    assert a.short("one two") == "one two"
    assert a.short(" ".join(["w"] * 100)).endswith("…")


def test_task_link_is_prefilled_not_sent():
    link = a.task_link("fix the tests & push", r"D:\proj")
    assert link.startswith("claude-cli://open?cwd=D%3A%5Cproj&q=")
    assert "fix%20the%20tests%20%26%20push" in link


def test_task_link_without_folder_lets_claude_choose():
    assert a.task_link("hi") == "claude-cli://open?q=hi"


def test_no_max_turns_flag():
    assert "--max-turns" not in a.ask_cmd("claude", "x", "en")  # not in claude --help any more


def test_failure_is_logged(capsys):
    fail = lambda *a_, **k: subprocess.CompletedProcess([], 1, "", "not logged in")
    a.ask_claude("x", which=lambda _: "claude", run=fail)
    assert "not logged in" in capsys.readouterr().err
