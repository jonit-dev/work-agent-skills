"""Self-check for burn.py leak detection. Run: python3 test_burn.py"""

import datetime
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def record(kind, when, **extra):
    return json.dumps({"type": kind, "timestamp": when.isoformat(), **extra})


def assistant(when, context, calls=()):
    content = [{"type": "tool_use", "name": n, "input": {"command": c}} for n, c in calls]
    usage = {"input_tokens": 10, "cache_read_input_tokens": context, "output_tokens": 50}
    return record("assistant", when, message={"model": "claude-opus-5-5", "usage": usage,
                                              "content": content})


def user(when, text):
    return record("user", when, message={"content": text})


def run(config_dir, env_extra=None):
    env = dict(os.environ, CLAUDE_CONFIG_DIR=config_dir, XDG_CACHE_HOME=config_dir)
    env.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)
    env.update(env_extra or {})
    return subprocess.run([sys.executable, os.path.join(HERE, "burn.py"), "2",
                           "--source", "claude", "--html",
                           os.path.join(config_dir, "report.html")], env=env, capture_output=True,
                          text=True, check=True).stdout


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    with tempfile.TemporaryDirectory() as root:
        project = os.path.join(root, "projects", "demo")
        os.makedirs(os.path.join(project, "memory"))
        with open(os.path.join(project, "memory", "MEMORY.md"), "w") as fh:
            fh.write("- line\n" * 250)

        lines = [user(now - datetime.timedelta(hours=13), "fix the bug")]
        for i in range(300):
            when = now - datetime.timedelta(hours=13) + datetime.timedelta(seconds=i * 150)
            if i % 5 == 0:
                lines.append(user(when, "<task-notification>done</task-notification>"))
            lines.append(assistant(when, 400_000, [("Bash", "cd /x && sed -n 1,9p f")]))
        with open(os.path.join(project, "aaaaaaaa-leak.jsonl"), "w") as fh:
            fh.write("\n".join(lines) + "\n")

        out = run(root)
        for expected in ("late compaction: peak 400k", "caller reads: 300",
                         "wakeups: 60 (teammate 0, task 60", "loop: 300 turns for 1 human",
                         "long-lived: 12h", "autoCompactWindow is unset",
                         "has 250 lines"):
            assert expected in out, "missing %r in:\n%s" % (expected, out)
        with open(os.path.join(root, "report.html")) as fh:
            page = fh.read()
        assert "<title>Claude Token Doctor</title>" in page
        prefix = "window.__REPORT__ = "
        suffix = "</script>"
        start = page.index(prefix) + len(prefix)
        end = page.index(suffix, start)
        json_part = page[start:end]
        assert "</script" not in json_part
        report_data = json.loads(json_part.replace("<\\/", "</"))
        assert report_data["issues"]
        assert "caller reads: 300" in json.dumps(report_data)
        assert any("compact too late" in issue["title"] for issue in report_data["issues"])
        assert all(1 <= issue["priority"] <= 3 for issue in report_data["issues"])
        assert [issue["priority"] for issue in report_data["issues"]] == sorted(
            issue["priority"] for issue in report_data["issues"]
        )
        assert any("transcript: " in issue.get("prompt", "") for issue in report_data["issues"])
        assert "2-day average" in report_data["burn"]["basis"]
        assert isinstance(report_data["active"], list)
        assert report_data["burndown"]
        assert report_data["kpis"]
        assert report_data["timeline"]
        assert report_data["baseline"]

        doctor = subprocess.run([os.path.join(HERE, "doctor"), "2", "--source", "claude"],
                                env=dict(os.environ, CLAUDE_CONFIG_DIR=root,
                                         XDG_CACHE_HOME=root, TOKEN_DOCTOR_PORT="0"), capture_output=True, text=True)
        assert doctor.returncode == 1, doctor.stdout + doctor.stderr
        assert "Verdict: 7 leaks found" in doctor.stdout, doctor.stdout
        assert os.path.exists(os.path.join(root, "claude-token-doctor", "report.html"))

        with open(os.path.join(root, "settings.json"), "w") as fh:
            json.dump({"autoCompactWindow": 200000}, fh)
        assert "autoCompactWindow is 200k (from settings): ok." in run(root)
        assert "autoCompactWindow is 800k (from env)" in run(
            root, {"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "800k"})
    print("test_burn: ok")


def check_codex_week():
    """Codex's weekly window comes from the rate_limits it logs; a finished week is ignored."""
    sys.path.insert(0, HERE)
    import burn
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    with tempfile.TemporaryDirectory() as home:
        path = os.path.join(home, "sessions", "2026", "rollout-x.jsonl")
        os.makedirs(os.path.dirname(path))
        os.environ["CODEX_HOME"] = home
        for resets, expected in ((now + 3600, 40.0), (now - 3600, None)):
            limits = {"primary": {"used_percent": 9, "window_minutes": 300, "resets_at": now},
                      "secondary": {"used_percent": 40, "window_minutes": 10080, "resets_at": resets}}
            with open(path, "w") as fh:
                fh.write(json.dumps({"type": "event_msg", "payload": {"rate_limits": limits}}) + "\n")
            week = burn.codex_week()
            assert (week and week["used"]) == expected, week
        del os.environ["CODEX_HOME"]


if __name__ == "__main__":
    main()
    check_codex_week()
