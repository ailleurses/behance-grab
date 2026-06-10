# behance-grab

Download, organize, check, and zip public Behance project or moodboard URLs.

## Overview

`behance-grab` is a Behance capture skill for local archival and reference workflows. It can:

- download one public Behance project into a folder you choose
- download or incrementally update a public Behance moodboard
- check whether a project or moodboard has changed
- package an existing download as a ZIP archive
- probe Behance connectivity before a download starts

The skill keeps project folders stable, names moodboard images in numeric order, and preserves update metadata for future checks.

## Usage

Use the bundled script from the skill folder:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py <command>
```

### Common commands

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py probe --remind
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py zip "<folder>"
```

### Command summary

| Command | Purpose |
| --- | --- |
| `project` | Download a single public Behance project. |
| `moodboard` | Download or incrementally update a public Behance moodboard. |
| `check` | Inspect a local download for remote updates. |
| `probe` | Test whether Behance is reachable from this machine. |
| `zip` | Create a ZIP file from an existing downloaded folder. |

## Install

### Codex

Copy this folder to:

```text
C:\Users\lenovo\.codex\skills\behance-grab
```

Then restart or reload Codex so it picks up the new skill files.

### Other agents

For other agents that support local skills, custom instructions, or tool packs, copy the same folder structure into that agent's skill or custom prompt directory, then reload the agent. Keep these files together:

- `SKILL.md`
- `README.md`
- `scripts/behance_grab.py`
- `agents/openai.yaml`

## Notes

- Downloaded Behance assets are usually copyrighted.
- Use the content only with the rights holder's permission and follow local law.
- The script requires `curl.exe`.
- It uses longer timeouts and extra retries to reduce false failures on slow connections.
- Before a download, the skill asks for a copyright acknowledgement and a target output folder.
