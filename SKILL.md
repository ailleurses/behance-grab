---
name: behance-grab
description: Download, organize, check, incrementally sync, and zip public Behance project or moodboard URLs. Use when the user provides a public Behance project link or moodboard link and wants local image extraction, update checks, incremental downloads, stable moodboard folders, or ZIP packaging.
---

# Behance Grab

Use this skill for public Behance project and moodboard capture workflows.

## Required User Confirmation

Before downloading any Behance content, tell the user:

> Behance project assets are usually copyrighted by their creators. Download only for personal reference, study, or local archival use. Do not use the downloaded files commercially, redistribute them, publish them elsewhere, or imply ownership unless you have explicit permission from the rights holder.

If the user is Chinese or another non-English language is clearly preferred, translate the notice into that language.

Then get the user's acknowledgement before running a download command.

Before every download, also confirm the target output directory with the user. Use an absolute path when possible. Do not download until the directory is confirmed.

For update checks that only inspect remote pages and local metadata, directory confirmation is still required, but the copyright acknowledgement can be shorter.

## Script

Use the bundled script:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py <command>
```

The script uses `curl.exe`; request network approval when needed.

If the user reports network issues or the page is slow, run a quick connectivity test first:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py probe
```

Use `probe --remind` when you want the script to print a short network reminder after a successful check.

## Commands

Download a single public Behance project into the confirmed folder:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<project-folder>"
```

Download or incrementally update a public Behance moodboard:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<moodboard-folder>"
```

Check whether a project or moodboard has updates:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py check "<project-or-moodboard-url>" --output "<existing-folder>"
```

Download and create a ZIP package in one run:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py project "<project-url>" --output "<project-folder>" --zip
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py moodboard "<moodboard-url>" --output "<moodboard-folder>" --zip
```

Zip an existing downloaded project or moodboard folder:

```powershell
python C:\Users\lenovo\.codex\skills\behance-grab\scripts\behance_grab.py zip "<folder>"
```

Use `--zip-path "<zip-file>"` when the user wants a specific ZIP location.

## Behavior

- Project mode downloads one public Behance project into the confirmed output folder.
- Moodboard mode creates one folder per Behance project.
- Moodboard project folders are named `NN_Project Title`.
- Moodboard image files are named `001.jpg`, `002.png`, etc.
- Moodboard ordering is stable in `project_order.json`.
- New moodboard projects are appended with increasing numbers, even if Behance inserts them earlier on the web page.
- Per-project source tracking is stored in `metadata.json`.
- Moodboard summary is stored in `summary.json`.
- Local image files no longer present in the current project page are moved into `_removed` inside that project folder.
- ZIP packages include the selected root folder and its contents.

## Notes

- Use `--use-cache` only when the user explicitly wants local cached inspection and does not need a live Behance update check.
- Use `--force-images` only when the user wants existing local images redownloaded.
- The script uses longer curl timeouts and extra retries to reduce false failures on slow connections.
- Behance pages can intermittently fail or return simplified HTML. Cached pages are used only when refresh fails or when `--use-cache` is requested.
- This skill does not grant reuse rights; it only automates local download and organization.
