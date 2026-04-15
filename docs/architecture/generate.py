#!/usr/bin/env python
"""
Allay Architecture Generator — reads the codebase and produces:
  1. Mermaid diagrams (.mmd) from plugin.json, hooks.json, SKILL.md, agents
  2. An interactive HTML architecture explorer (dark-themed, single page)
  3. SVG renders if mmdc (mermaid-cli) is available

Usage: python generate.py [repo_root]

These diagrams can never go stale — they're generated from the source of truth.
"""

import json
import os
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def find_repo_root(start=None):
    p = Path(start) if start else Path(__file__).resolve().parent.parent.parent
    if (p / "shared" / "constants.sh").exists():
        return p
    return p


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def parse_frontmatter(path):
    """Extract YAML frontmatter from .md files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    end = content.find("---", 3)
    if end == -1:
        return {}

    fm = {}
    for line in content[3:end].strip().split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("-"):
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    return fm


def scan_plugins(repo):
    """Scan all plugins and extract structure."""
    plugins = []
    plugins_dir = repo / "plugins"
    if not plugins_dir.exists():
        return plugins

    for pdir in sorted(plugins_dir.iterdir()):
        if not pdir.is_dir():
            continue

        pjson = load_json(pdir / ".claude-plugin" / "plugin.json")
        if not pjson:
            continue

        plugin = {
            "name": pjson.get("name", pdir.name),
            "short": pdir.name,
            "description": pjson.get("description", ""),
            "version": pjson.get("version", "?"),
            "dir": pdir,
            "hooks": [],
            "skills": [],
            "agents": [],
            "commands": [],
        }

        # Hooks
        hooks_json = load_json(pdir / "hooks" / "hooks.json")
        for phase, matchers in hooks_json.get("hooks", {}).items():
            for matcher_block in matchers:
                matcher = matcher_block.get("matcher", "*")
                for hook in matcher_block.get("hooks", []):
                    cmd = hook.get("command", "")
                    script = cmd.split("/")[-1].replace('"', "").strip()
                    plugin["hooks"].append({
                        "phase": phase,
                        "matcher": matcher,
                        "script": script,
                        "timeout": hook.get("timeout", "?"),
                    })

        # Skills
        skills_dir = pdir / "skills"
        if skills_dir.exists():
            for sdir in sorted(skills_dir.iterdir()):
                skill_md = sdir / "SKILL.md"
                if skill_md.exists():
                    fm = parse_frontmatter(skill_md)
                    plugin["skills"].append({
                        "name": fm.get("name", sdir.name),
                        "description": fm.get("description", ""),
                        "allowed_tools": fm.get("allowed-tools", ""),
                    })

        # Agents
        agents_dir = pdir / "agents"
        if agents_dir.exists():
            for afile in sorted(agents_dir.glob("*.md")):
                fm = parse_frontmatter(afile)
                plugin["agents"].append({
                    "name": fm.get("name", afile.stem),
                    "model": fm.get("model", "?"),
                    "context": fm.get("context", "?"),
                })

        # Commands
        cmds_dir = pdir / "commands"
        if cmds_dir.exists():
            for cfile in sorted(cmds_dir.glob("*.md")):
                fm = parse_frontmatter(cfile)
                plugin["commands"].append({
                    "name": fm.get("name", cfile.stem),
                    "description": fm.get("description", ""),
                })

        plugins.append(plugin)

    return plugins


# ── Mermaid generation ────────────────────────────────────────────────

def gen_highlevel_mermaid(plugins):
    """High-level: 3 hook phases → 3 plugins → outputs."""
    lines = [
        "graph TD",
        '    CC["Claude Code<br/>Tool Calls"]',
    ]

    phase_colors = {
        "PreToolUse": "#58a6ff",
        "PostToolUse": "#3fb950",
        "PreCompact": "#d29922",
    }

    # Collect phases per plugin
    for p in plugins:
        pid = p["short"].replace("-", "_")
        phases = set(h["phase"] for h in p["hooks"])
        phase_str = " + ".join(sorted(phases)) if phases else "—"

        lines.append(f'    {pid}["{p["short"]}<br/><small>{phase_str}</small>"]')
        lines.append(f'    CC --> {pid}')

        # Outputs
        lines.append(f'    {pid}_out(["state/metrics.jsonl"])')
        lines.append(f'    {pid} --> {pid}_out')

        # Style — use first phase color, or blend for multi-phase
        if phases:
            color = phase_colors.get(sorted(phases)[0], "#8b949e")
            if len(phases) > 1:
                color = "#bc8cff"  # purple for multi-phase
            lines.append(f'    style {pid} fill:#161b22,stroke:{color},color:#e6edf3')

    lines.append('    style CC fill:#0d1117,stroke:#bc8cff,color:#e6edf3')

    return "\n".join(lines)


def gen_hooks_mermaid(plugins):
    """Detailed hook flow: which scripts fire on which tools."""
    lines = ["graph LR"]

    for p in plugins:
        pid = p["short"].replace("-", "_")
        lines.append(f'    subgraph {pid}["{p["short"]}"]')

        for i, h in enumerate(p["hooks"]):
            hid = f'{pid}_h{i}'
            tools = h["matcher"].replace("|", " | ")
            lines.append(f'        {hid}_trigger["{h["phase"]}<br/>{tools}"]')
            lines.append(f'        {hid}_script["{h["script"]}<br/><small>timeout: {h["timeout"]}s</small>"]')
            lines.append(f'        {hid}_trigger --> {hid}_script')

        lines.append("    end")

    return "\n".join(lines)


def gen_dataflow_mermaid(plugins):
    """Metrics data flow: what events each plugin logs."""
    lines = [
        "graph TB",
        '    subgraph inputs["Tool Calls"]',
        '        Bash["Bash"]',
        '        Read["Read"]',
        '        Write["Write / Edit"]',
        '        Glob["Glob / Grep"]',
        "    end",
    ]

    events_map = {
        "context-guard": ["turn (token est.)", "drift_detected"],
        "token-saver": ["bash_compressed", "duplicate_blocked", "delta_read", "result_aged"],
        "state-keeper": ["checkpoint_saved"],
    }

    for p in plugins:
        pid = p["short"].replace("-", "_")
        events = events_map.get(p["short"], [])
        evt_str = "<br/>".join(events)
        lines.append(f'    {pid}_metrics["{p["short"]}/state/metrics.jsonl<br/><small>{evt_str}</small>"]')

        for h in p["hooks"]:
            for tool in h["matcher"].split("|"):
                tool = tool.strip()
                if tool in ("Bash", "Read", "Write", "Edit", "Glob", "Grep", "MultiEdit"):
                    src = {"Edit": "Write", "MultiEdit": "Write"}.get(tool, tool)
                    if src == "Grep":
                        src = "Glob"
                    lines.append(f'    {src} --> {pid}_metrics')
                    break

    lines.append('    report["📊 /allay:report<br/>Aggregates all metrics"]')
    for p in plugins:
        pid = p["short"].replace("-", "_")
        lines.append(f'    {pid}_metrics --> report')

    return "\n".join(lines)


def gen_session_lifecycle_mermaid(plugins):
    """Session lifecycle: auto-detect phases from plugins."""
    # Collect which plugins own which phases
    phase_plugins = {}
    for p in plugins:
        for h in p["hooks"]:
            phase_plugins.setdefault(h["phase"], []).append(p["short"])

    lines = ["graph TD", '    start(["Session Start"]) --> turns']
    lines.append('    subgraph turns["Active Session"]')
    lines.append('        t1["Turn N: Tool Call"]')

    if "PreToolUse" in phase_plugins:
        names = ", ".join(sorted(set(phase_plugins["PreToolUse"])))
        lines.append(f'        t1 --> pre["PreToolUse<br/>{names}"]')
        lines.append('        pre --> exec["Tool Executes"]')
    else:
        lines.append('        t1 --> exec["Tool Executes"]')

    if "PostToolUse" in phase_plugins:
        names = ", ".join(sorted(set(phase_plugins["PostToolUse"])))
        lines.append(f'        exec --> post["PostToolUse<br/>{names}"]')
        lines.append('        post --> t1')
    else:
        lines.append('        exec --> t1')

    lines.append("    end")

    if "PreCompact" in phase_plugins:
        names = ", ".join(sorted(set(phase_plugins["PreCompact"])))
        lines.append(f'    turns -->|"Context full"| compact["⚠️ Compaction"]')
        lines.append(f'    compact --> precompact["PreCompact<br/>{names}"]')
        lines.append('    precompact --> wipe["Context Wiped"]')
        lines.append('    wipe --> restore["Restore context"]')
        lines.append('    restore --> resume(["Session Continues"])')
        lines.append('    style compact fill:#f85149,color:#0d1117')
        lines.append('    style precompact fill:#d29922,color:#0d1117')
        lines.append('    style restore fill:#3fb950,color:#0d1117')

    return "\n".join(lines)


# ── HTML generation ───────────────────────────────────────────────────

def gen_html(plugins, mermaid_diagrams, repo):
    """Interactive architecture explorer — single HTML page, dark theme."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Build plugin cards
    plugin_cards = ""
    for p in plugins:
        hooks_html = ""
        for h in p["hooks"]:
            hooks_html += f'<div class="hook"><span class="phase">{h["phase"]}</span> <span class="matcher">{h["matcher"]}</span> → <code>{h["script"]}</code> <span class="dim">({h["timeout"]}s)</span></div>'

        skills_html = "".join(
            f'<div class="item"><strong>{s["name"]}</strong></div>' for s in p["skills"]
        )
        agents_html = "".join(
            f'<div class="item"><strong>{a["name"]}</strong> <span class="dim">({a["model"]}, {a["context"]})</span></div>' for a in p["agents"]
        )
        commands_html = "".join(
            f'<div class="item"><code>{c["name"]}</code></div>' for c in p["commands"]
        )

        plugin_cards += f"""
        <div class="plugin-card">
          <h3>{p["short"]}</h3>
          <p class="desc">{p["description"]}</p>
          <div class="section-label">Hooks</div>
          {hooks_html or '<div class="dim">None</div>'}
          <div class="section-label">Skills</div>
          {skills_html or '<div class="dim">None</div>'}
          <div class="section-label">Agents</div>
          {agents_html or '<div class="dim">None</div>'}
          <div class="section-label">Commands</div>
          {commands_html or '<div class="dim">None</div>'}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Allay — Architecture Explorer</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 0;
  }}
  .brand-bar {{ height: 3px; background: #39d353; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  h1 {{ font-size: 32px; margin-bottom: 4px; }}
  h1 span {{ color: #8b949e; font-size: 14px; font-weight: 400; margin-left: 12px; }}
  .subtitle {{ color: #484f58; font-size: 12px; margin-bottom: 32px; }}
  h2 {{
    font-size: 18px;
    margin: 32px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #30363d;
  }}
  .tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 0;
    border-bottom: 1px solid #30363d;
  }}
  .tab {{
    padding: 8px 16px;
    cursor: pointer;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    color: #8b949e;
    font-size: 13px;
    background: transparent;
    transition: all 0.15s;
  }}
  .tab:hover {{ color: #e6edf3; background: #161b22; }}
  .tab.active {{
    color: #e6edf3;
    background: #161b22;
    border-color: #30363d;
    border-bottom-color: #161b22;
    margin-bottom: -1px;
  }}
  .diagram-panel {{
    display: none;
    background: #161b22;
    border: 1px solid #30363d;
    border-top: none;
    border-radius: 0 0 8px 8px;
    padding: 24px;
    min-height: 300px;
    overflow-x: auto;
  }}
  .diagram-panel.active {{ display: block; }}
  .mermaid {{ background: transparent; }}
  .mermaid svg {{ max-width: 100%; }}
  .plugins-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 16px;
    margin-top: 16px;
  }}
  .plugin-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 20px;
  }}
  .plugin-card h3 {{
    font-size: 16px;
    margin-bottom: 4px;
    color: #58a6ff;
  }}
  .plugin-card .desc {{
    color: #8b949e;
    font-size: 12px;
    margin-bottom: 12px;
  }}
  .section-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #484f58;
    margin-top: 12px;
    margin-bottom: 4px;
  }}
  .hook {{
    font-size: 12px;
    padding: 4px 0;
    border-bottom: 1px solid #21262d;
  }}
  .phase {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 600;
    background: #1c2333;
    color: #58a6ff;
  }}
  .matcher {{ color: #3fb950; font-size: 11px; }}
  .item {{ font-size: 12px; padding: 2px 0; }}
  .dim {{ color: #484f58; }}
  code {{
    background: #1c2333;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
    color: #e6edf3;
  }}
  .footer {{
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #30363d;
    font-size: 11px;
    color: #484f58;
    display: flex;
    justify-content: space-between;
  }}
</style>
</head>
<body>
<div class="brand-bar"></div>
<div class="container">
  <h1>Allay <span>Architecture Explorer</span></h1>
  <div class="subtitle">Auto-generated from codebase — {now}</div>

  <h2>System Diagrams</h2>
  <div class="tabs">
    <div class="tab active" onclick="showTab('highlevel')">High Level</div>
    <div class="tab" onclick="showTab('hooks')">Hook Detail</div>
    <div class="tab" onclick="showTab('dataflow')">Data Flow</div>
    <div class="tab" onclick="showTab('lifecycle')">Session Lifecycle</div>
  </div>

  <div id="panel-highlevel" class="diagram-panel active">
    <pre class="mermaid">{mermaid_diagrams['highlevel']}</pre>
  </div>
  <div id="panel-hooks" class="diagram-panel">
    <pre class="mermaid">{mermaid_diagrams['hooks']}</pre>
  </div>
  <div id="panel-dataflow" class="diagram-panel">
    <pre class="mermaid">{mermaid_diagrams['dataflow']}</pre>
  </div>
  <div id="panel-lifecycle" class="diagram-panel">
    <pre class="mermaid">{mermaid_diagrams['lifecycle']}</pre>
  </div>

  <h2>Plugin Components</h2>
  <div class="plugins-grid">
    {plugin_cards}
  </div>

  <div class="footer">
    <span>Generated by docs/architecture/generate.py from plugin.json, hooks.json, SKILL.md, agents/*.md</span>
    <span>Allay v2.0.0</span>
  </div>
</div>

<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: 'dark',
    themeVariables: {{
      darkMode: true,
      background: '#161b22',
      primaryColor: '#1c2333',
      primaryTextColor: '#e6edf3',
      primaryBorderColor: '#30363d',
      lineColor: '#484f58',
      secondaryColor: '#161b22',
      tertiaryColor: '#1c2333',
    }}
  }});

  function showTab(id) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.diagram-panel').forEach(p => p.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('panel-' + id).classList.add('active');

    // Re-render mermaid for newly visible panels
    const panel = document.getElementById('panel-' + id);
    const pre = panel.querySelector('.mermaid');
    if (pre && !pre.getAttribute('data-processed')) {{
      mermaid.run({{ nodes: [pre] }});
    }}
  }}
</script>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────

def main():
    repo = find_repo_root(sys.argv[1] if len(sys.argv) > 1 else None)
    out_dir = repo / "docs" / "architecture"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {repo} ...")
    plugins = scan_plugins(repo)
    print(f"Found {len(plugins)} plugins")

    # Generate mermaid diagrams
    diagrams = {
        "highlevel": gen_highlevel_mermaid(plugins),
        "hooks": gen_hooks_mermaid(plugins),
        "dataflow": gen_dataflow_mermaid(plugins),
        "lifecycle": gen_session_lifecycle_mermaid(plugins),
    }

    # Write .mmd files
    for name, content in diagrams.items():
        mmd_path = out_dir / f"{name}.mmd"
        with open(mmd_path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"  {mmd_path.name}")

    # Write interactive HTML
    html_path = out_dir / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(gen_html(plugins, diagrams, repo))
    print(f"  {html_path.name}")

    # Try SVG generation via mmdc (mermaid-cli)
    mmdc = None
    for cmd in ("mmdc", "npx mmdc", "npx -y @mermaid-js/mermaid-cli mmdc"):
        try:
            subprocess.run(cmd.split()[0:1], capture_output=True, timeout=5)
            mmdc = cmd
            break
        except Exception:
            continue

    if mmdc:
        for name in diagrams:
            mmd_path = out_dir / f"{name}.mmd"
            svg_path = out_dir / f"{name}.svg"
            try:
                subprocess.run(
                    f'{mmdc} -i "{mmd_path}" -o "{svg_path}" -t dark -b transparent'.split(),
                    capture_output=True, timeout=30
                )
                if svg_path.exists():
                    print(f"  {svg_path.name} (SVG)")
            except Exception:
                pass
    else:
        print("  (mmdc not found — SVG generation skipped. Install: npm i -g @mermaid-js/mermaid-cli)")

    print(f"\nOpen {html_path} in a browser for the interactive explorer.")
    print(html_path)


if __name__ == "__main__":
    main()
