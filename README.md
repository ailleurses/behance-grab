[中文](README_zh.md) | English

# behance-grab

Download, organize, check, and zip public Behance project or moodboard URLs.

## What it does

- Download one public Behance project into a chosen folder.
- Download or incrementally update a public Behance moodboard.
- Check whether a project or moodboard has updates.
- Package a downloaded project or moodboard as a ZIP file.
- Test whether Behance is reachable before starting a download.

## Usage

Use the bundled script:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py <command>
```

Common commands:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py check "<url>" --output "<existing-folder>"
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py probe --remind
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py zip "<folder>"
```

## Install

### Codex

Copy this skill folder to:

```text
C:\Users\lenovo\.codex\skills\behance-grab
```

Then restart or reload Codex so it picks up the new skill files.

### Other agents

For other agents that support local skills, custom instructions, or tool packs, copy the same folder structure into that agent's skill or custom prompt directory, then reload the agent. Keep these files together:

- `SKILL.md`
- `README.md`
- `README_zh.md`
- `scripts/behance_grab.py`
- `agents/openai.yaml`

## Notes

- Downloaded Behance assets are usually copyrighted.
- Use the content only with the rights holder's permission and follow local law.
- The script requires `curl.exe` and uses longer timeouts to handle slower networks.
