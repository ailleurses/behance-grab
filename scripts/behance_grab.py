import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125 Safari/537.36"
)
CONNECT_TIMEOUT_SECONDS = 40
MAX_TIME_SECONDS = 600
PAGE_MAX_TIME_SECONDS = 180
IMAGE_RE = re.compile(
    r"https://mir-s3-cdn-cf\.behance\.net/project_modules/[^\s\"'<>),]+",
    re.IGNORECASE,
)
PROJECT_MODULE_RE = re.compile(
    r"^(https://mir-s3-cdn-cf\.behance\.net/project_modules)/([^/]+)/([^?#]+)",
    re.IGNORECASE,
)
IMAGE_EXT_RE = re.compile(r"\.(jpe?g|png|webp|gif|bmp)$", re.IGNORECASE)
MOODBOARD_ID_RE = re.compile(r"/moodboard/(\d+)")
PROJECT_ID_RE = re.compile(r"/gallery/(\d+)")
SIZE_PREFERENCE = [
    "source",
    "max_3840",
    "3840",
    "2800",
    "max_2800",
    "hd",
    "1400",
    "max_1400",
    "max_1200",
    "fs",
    "max_808",
    "max_632",
    "max_316",
]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ORDER_FILE_NAME = "project_order.json"


def run(cmd, quiet=False):
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 and not quiet:
        print(safe_console_text(proc.stdout))
    return proc


def safe_console_text(value):
    return str(value).encode("ascii", errors="replace").decode("ascii")


def curl_download(url, out_path, referer=None, fail=True, max_time=MAX_TIME_SECONDS):
    cmd = [
        "curl.exe",
        "-L",
        "--retry",
        "3",
        "--connect-timeout",
        str(CONNECT_TIMEOUT_SECONDS),
        "--max-time",
        str(max_time),
        "-A",
        UA,
    ]
    if fail:
        cmd.append("-f")
    if referer:
        cmd += ["-e", referer]
    cmd += ["-o", str(out_path), url]
    return run(cmd, quiet=True)


def fetch_text(url, out_path, referer=None, refresh=True):
    if refresh or not out_path.exists() or out_path.stat().st_size == 0:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(out_path.suffix + ".download")
        if tmp_path.exists():
            tmp_path.unlink()
        proc = curl_download(url, tmp_path, referer=referer, fail=True, max_time=PAGE_MAX_TIME_SECONDS)
        if proc.returncode == 0 and tmp_path.exists() and tmp_path.stat().st_size > 0:
            tmp_path.replace(out_path)
        elif out_path.exists() and out_path.stat().st_size > 0:
            print(f"  Warning: refresh failed; using cached page {out_path.name}")
            if tmp_path.exists():
                tmp_path.unlink()
        else:
            if tmp_path.exists():
                tmp_path.unlink()
            raise RuntimeError(f"Failed to fetch {url}\n{proc.stdout}")
    return out_path.read_text(encoding="utf-8", errors="replace")


def is_moodboard_url(url):
    return MOODBOARD_ID_RE.search(url) is not None


def is_project_url(url):
    return PROJECT_ID_RE.search(url) is not None


def moodboard_id_from_url(url):
    match = MOODBOARD_ID_RE.search(url)
    return match.group(1) if match else "unknown"


def project_id_from_url(url):
    match = PROJECT_ID_RE.search(url)
    return match.group(1) if match else "unknown"


def safe_name(value, fallback):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "")
    value = re.sub(r"\s+", " ", value).strip(" .")
    if not value:
        value = fallback
    return value[:120].rstrip(" .")


def normalize_html_for_urls(text):
    return html.unescape(text).replace("\\/", "/")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_moodboard_items(text):
    data = None
    key = '"moodboard":'
    idx = text.find(key)
    if idx >= 0:
        start = text.find("{", idx + len(key))
        if start >= 0:
            data, _ = json.JSONDecoder().raw_decode(text[start:])
    if data is None:
        data = parse_object_containing_items(text)

    items = []
    for item in data.get("items", []):
        entity = item.get("entity") or {}
        if item.get("entityType") != "project" or not entity.get("url"):
            continue
        item_id = entity.get("id") or item.get("id")
        if item_id is None:
            continue
        items.append(
            {
                "id": int(item_id),
                "name": entity.get("name") or f"project-{item_id}",
                "url": entity["url"].replace("\\/", "/"),
                "owner": ", ".join(
                    owner.get("displayName", "")
                    for owner in entity.get("owners", [])
                    if owner.get("displayName")
                ),
            }
        )
    return items


def parse_object_containing_items(text):
    marker_index = text.find('"itemsLastCursor"')
    if marker_index < 0:
        raise RuntimeError("Could not find moodboard item cursor in HTML.")
    search_start = text.rfind('"items":[', 0, marker_index)
    if search_start < 0:
        raise RuntimeError("Could not find moodboard items array in HTML.")

    decoder = json.JSONDecoder()
    for start in range(search_start, -1, -1):
        if text[start] != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if (
            isinstance(candidate, dict)
            and isinstance(candidate.get("items"), list)
            and "itemsLastCursor" in candidate
        ):
            return candidate
    raise RuntimeError("Could not decode the moodboard collection object.")


def parse_meta_title(text):
    for tag in re.findall(r"<meta\b[^>]*>", text, re.IGNORECASE):
        attrs = dict(
            (key.lower(), html.unescape(value))
            for key, value in re.findall(
                r'([A-Za-z_:-]+)\s*=\s*["\']([^"\']*)["\']',
                tag,
                re.IGNORECASE,
            )
        )
        key = attrs.get("property") or attrs.get("name")
        if key in {"og:title", "twitter:title"} and attrs.get("content"):
            return clean_project_title(attrs["content"])

    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if match:
        return clean_project_title(html.unescape(re.sub(r"\s+", " ", match.group(1))))
    return None


def clean_project_title(title):
    title = title.strip()
    title = re.sub(r"\s+on Behance\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*::\s*Behance\s*$", "", title, flags=re.IGNORECASE)
    return title.strip()


def title_from_project_url(url):
    parts = [part for part in urlparse(url).path.split("/") if part]
    title_part = ""
    if "gallery" in parts:
        index = parts.index("gallery")
        if len(parts) > index + 2:
            title_part = parts[index + 2]
    if not title_part and parts:
        title_part = parts[-1]
    title = unquote(title_part).replace("-", " ").replace("_", " ").strip()
    return title or f"project-{project_id_from_url(url)}"


def extract_project_image_groups(text):
    normalized = normalize_html_for_urls(text)
    groups = {}
    for raw in IMAGE_RE.findall(normalized):
        url = raw.rstrip("\\")
        filename = Path(urlparse(url).path).name
        if IMAGE_EXT_RE.search(filename):
            groups.setdefault(filename, set()).add(url)
    return groups


def score_observed_url(url):
    lowered = url.lower()
    for index, size in enumerate(SIZE_PREFERENCE):
        if f"/{size}/" in lowered:
            return index
    if "_webp/" in lowered:
        return len(SIZE_PREFERENCE) + 5
    return len(SIZE_PREFERENCE) + 1


def candidate_urls(filename, observed_urls):
    candidates = []
    parsed = None
    for url in sorted(observed_urls):
        match = PROJECT_MODULE_RE.match(url)
        if match:
            parsed = match
            break
    if parsed:
        prefix = parsed.group(1)
        for size in SIZE_PREFERENCE:
            candidates.append(f"{prefix}/{size}/{filename}")
    for url in sorted(observed_urls, key=score_observed_url):
        candidates.append(url)
        candidates.append(url.replace("_webp/", "/"))

    seen = set()
    result = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


def download_one_image(candidates, destination, referer):
    tmp = destination.with_suffix(destination.suffix + ".part")
    if tmp.exists():
        tmp.unlink()
    for url in candidates:
        proc = curl_download(url, tmp, referer=referer, fail=True, max_time=MAX_TIME_SECONDS)
        if proc.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            if destination.exists():
                destination.unlink()
            tmp.replace(destination)
            return url, destination.stat().st_size
        if tmp.exists():
            tmp.unlink()
    return None, 0


def image_destination(folder, index, source_filename):
    ext = Path(source_filename).suffix.lower() or ".img"
    return folder / f"{index:03d}{ext}"


def metadata_source_map(metadata):
    mapping = {}
    if not metadata:
        return mapping
    for record in metadata.get("downloaded", []):
        source = record.get("source_filename")
        file_name = record.get("file")
        if source and file_name:
            mapping[source] = file_name
    return mapping


def unique_path(base):
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = base.with_name(f"{base.name}_{counter}")
        if not candidate.exists():
            return candidate
        counter += 1


def find_existing_image(folder, index, source_filename, destination, source_map):
    candidates = []
    if source_filename in source_map:
        candidates.append(folder / source_map[source_filename])
    candidates.extend(
        [
            folder / f"{index:03d}_{source_filename}",
            folder / source_filename,
            destination,
        ]
    )
    candidates.extend(sorted(folder.glob(f"*_{source_filename}")))

    seen = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
            return candidate
    return None


def move_to_removed(path, project_folder):
    removed_dir = project_folder / "_removed"
    removed_dir.mkdir(exist_ok=True)
    destination = unique_path(removed_dir / path.name)
    path.rename(destination)
    return destination


def prepare_existing_images(project_folder, desired, metadata):
    source_map = metadata_source_map(metadata)
    temp_by_source = {}
    used_paths = set()

    for index, (source_filename, destination) in enumerate(desired, start=1):
        existing = find_existing_image(
            project_folder,
            index,
            source_filename,
            destination,
            source_map,
        )
        if not existing:
            continue
        resolved = existing.resolve()
        if resolved in used_paths:
            continue
        used_paths.add(resolved)
        temp = unique_path(project_folder / f"__imgtmp_{index:03d}{existing.suffix.lower()}")
        if existing != temp:
            existing.rename(temp)
        temp_by_source[source_filename] = temp

    for source_filename, destination in desired:
        temp = temp_by_source.get(source_filename)
        if not temp:
            continue
        if destination.exists() and destination != temp:
            move_to_removed(destination, project_folder)
        temp.rename(destination)


def prune_extra_images(project_folder, desired_destinations):
    desired_names = {path.name for path in desired_destinations}
    moved = []
    for path in project_folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if path.name not in desired_names:
            moved.append(str(move_to_removed(path, project_folder).name))
    return moved


def parse_project_page(url, output_root, referer=None, refresh=True):
    project_id = project_id_from_url(url)
    page_path = output_root / "_pages" / f"project_{project_id}.html"
    page_text = fetch_text(url, page_path, referer=referer, refresh=refresh)
    title = parse_meta_title(page_text) or title_from_project_url(url)
    groups = extract_project_image_groups(page_text)
    project = {
        "id": int(project_id) if project_id.isdigit() else project_id,
        "name": title,
        "url": url,
        "owner": "",
    }
    return project, groups


def sync_project_folder(project, groups, folder, refresh_existing_images=False):
    folder.mkdir(parents=True, exist_ok=True)
    if not groups:
        raise RuntimeError("No project image modules found.")

    metadata = read_json(folder / "metadata.json")
    desired = [
        (filename, image_destination(folder, img_index, filename))
        for img_index, filename in enumerate(groups.keys(), start=1)
    ]
    prepare_existing_images(folder, desired, metadata)

    downloads = []
    failures = []
    total = len(groups)
    for img_index, (filename, urls) in enumerate(groups.items(), start=1):
        dest = image_destination(folder, img_index, filename)
        if dest.exists() and dest.stat().st_size > 0 and not refresh_existing_images:
            downloads.append(
                {
                    "file": dest.name,
                    "bytes": dest.stat().st_size,
                    "source_filename": filename,
                    "source_url": None,
                    "cached": True,
                }
            )
            continue

        chosen_url, size = download_one_image(
            candidate_urls(filename, urls),
            dest,
            referer=project["url"],
        )
        if chosen_url:
            downloads.append(
                {
                    "file": dest.name,
                    "bytes": size,
                    "source_filename": filename,
                    "source_url": chosen_url,
                    "cached": False,
                }
            )
            print(f"    {img_index:03d}/{total} ok {dest.name}")
        else:
            failures.append({"filename": filename, "observed_urls": sorted(urls)})
            print(f"    {img_index:03d}/{total} failed {filename}")
        time.sleep(0.05)

    removed_files = prune_extra_images(folder, [dest for _, dest in desired])
    project_metadata = {
        "project": project,
        "image_modules_found": len(groups),
        "downloaded": downloads,
        "failed": failures,
        "moved_to_removed": removed_files,
    }
    write_json(folder / "metadata.json", project_metadata)
    return project_metadata


def load_order_records(order_path):
    data = read_json(order_path)
    if not isinstance(data, list):
        return []

    records = []
    used_ids = set()
    used_indexes = set()
    for fallback_index, item in enumerate(data, start=1):
        if isinstance(item, int):
            project_id = item
            record = {"id": int(project_id), "index": fallback_index}
        elif isinstance(item, dict) and item.get("id") is not None:
            project_id = int(item["id"])
            record = dict(item)
            record["id"] = project_id
            record["index"] = int(item.get("index") or fallback_index)
        else:
            continue
        if record["id"] in used_ids:
            continue
        if record["index"] in used_indexes:
            record["index"] = max(used_indexes or {0}) + 1
        used_ids.add(record["id"])
        used_indexes.add(record["index"])
        records.append(record)
    return sorted(records, key=lambda item: item["index"])


def update_project_order(projects, order_path, write_order=True):
    by_id = {int(project["id"]): project for project in projects}
    records = load_order_records(order_path)
    record_by_id = {int(record["id"]): record for record in records}
    max_index = max([int(record["index"]) for record in records] or [0])

    for project_id, project in by_id.items():
        if project_id in record_by_id:
            record = record_by_id[project_id]
            record["name"] = project["name"]
            record["url"] = project["url"]
        else:
            max_index += 1
            record = {
                "id": project_id,
                "index": max_index,
                "name": project["name"],
                "url": project["url"],
            }
            records.append(record)
            record_by_id[project_id] = record

    records = sorted(records, key=lambda item: int(item["index"]))
    active = [
        (int(record["index"]), by_id[int(record["id"])])
        for record in records
        if int(record["id"]) in by_id
    ]
    if write_order:
        write_json(order_path, records)
    return active, records


def project_folder_name(index, project):
    return safe_name(f"{index:02d}_{project['name']}", f"{index:02d}_project")


def discover_project_folders(output_root, projects=None):
    folders = {}
    if not output_root.exists():
        return folders

    title_to_project_id = {}
    if projects:
        for project in projects:
            title = safe_name(project["name"], f"project-{project['id']}")
            title_to_project_id.setdefault(title.casefold(), int(project["id"]))

    for folder in output_root.iterdir():
        if not folder.is_dir() or folder.name == "_pages" or folder.name.startswith("__"):
            continue
        project_id = None
        metadata = read_json(folder / "metadata.json")
        if metadata:
            project = metadata.get("project") or {}
            project_id = project.get("id")
        if project_id is None:
            title_match = re.match(r"^\d+_(.+)$", folder.name)
            if title_match:
                project_id = title_to_project_id.get(title_match.group(1).casefold())
        if project_id is not None and int(project_id) not in folders:
            folders[int(project_id)] = folder
    return folders


def reconcile_project_folders(output_root, existing_folders, indexed_projects):
    targets = {
        int(project["id"]): output_root / project_folder_name(index, project)
        for index, project in indexed_projects
    }
    moved = {}

    for project_id, existing in list(existing_folders.items()):
        target = targets.get(project_id)
        if target is None or existing == target or not existing.exists():
            continue
        temp = unique_path(output_root / f"__renaming_{project_id}")
        existing.rename(temp)
        moved[project_id] = (temp, target)
        existing_folders[project_id] = temp

    for project_id, (temp, target) in moved.items():
        if target.exists():
            backup = unique_path(output_root / f"__unmatched_{target.name}")
            target.rename(backup)
            print(f"  Moved unmatched folder aside: {target.name} -> {backup.name}")
        temp.rename(target)
        existing_folders[project_id] = target
        print(f"  Renamed folder: {temp.name} -> {target.name}")

    for project_id, target in targets.items():
        target.mkdir(parents=True, exist_ok=True)
        existing_folders[project_id] = target

    return existing_folders


def fetch_moodboard_projects(url, output_root, refresh):
    moodboard_id = moodboard_id_from_url(url)
    page_path = output_root / f"moodboard_{moodboard_id}.html"
    text = fetch_text(url, page_path, refresh=refresh)
    projects = parse_moodboard_items(text)
    if not projects:
        raise RuntimeError("No projects found in moodboard.")
    return projects


def compare_sources(remote_sources, metadata):
    local_sources = [
        item.get("source_filename")
        for item in (metadata or {}).get("downloaded", [])
        if item.get("source_filename")
    ]
    added = [source for source in remote_sources if source not in set(local_sources)]
    removed = [source for source in local_sources if source not in set(remote_sources)]
    order_changed = (
        not added
        and not removed
        and bool(local_sources)
        and bool(remote_sources)
        and local_sources != remote_sources
    )
    return added, removed, order_changed


def sync_project_command(args):
    output_root = Path(args.output).expanduser()
    refresh = not args.use_cache
    project, groups = parse_project_page(args.url, output_root, refresh=refresh)
    print(f"Syncing project: {project['name']}")
    print(f"  Found {len(groups)} image modules.")
    metadata = sync_project_folder(project, groups, output_root, args.force_images)
    print(
        f"Done. Images present {len(metadata['downloaded'])}, "
        f"failed {len(metadata['failed'])}."
    )
    print(output_root)
    if args.zip:
        zip_file = zip_directory(output_root, args.zip_path)
        print(f"ZIP: {zip_file}")
    return 2 if metadata["failed"] else 0


def sync_moodboard_command(args):
    output_root = Path(args.output).expanduser()
    refresh = not args.use_cache
    output_root.mkdir(parents=True, exist_ok=True)

    projects = fetch_moodboard_projects(args.url, output_root, refresh=refresh)
    if args.limit:
        projects = projects[: args.limit]

    existing_folders = discover_project_folders(output_root, projects)
    indexed_projects, order_records = update_project_order(
        projects,
        output_root / ORDER_FILE_NAME,
        write_order=True,
    )
    existing_folders = reconcile_project_folders(output_root, existing_folders, indexed_projects)
    write_json(output_root / "projects.json", projects)

    print(f"Found {len(projects)} projects.")
    summary = []
    for position, (folder_index, project) in enumerate(indexed_projects, start=1):
        folder = existing_folders[int(project["id"])]
        print(f"[{position}/{len(indexed_projects)}] Syncing project: {project['name']}")
        project_info, groups = parse_project_page(
            project["url"],
            output_root,
            referer=args.url,
            refresh=refresh,
        )
        project.update(project_info)
        print(f"  Found {len(groups)} image modules.")
        metadata = sync_project_folder(project, groups, folder, args.force_images)
        summary.append(
            {
                "project": project,
                "folder": str(folder.relative_to(output_root.parent)),
                "order_index": folder_index,
                "image_modules_found": len(groups),
                "downloaded_count": len(metadata["downloaded"]),
                "failed_count": len(metadata["failed"]),
                "moved_to_removed_count": len(metadata["moved_to_removed"]),
            }
        )

    write_json(output_root / "summary.json", summary)
    write_json(output_root / ORDER_FILE_NAME, order_records)
    total_downloaded = sum(item["downloaded_count"] for item in summary)
    total_failed = sum(item["failed_count"] for item in summary)
    print(f"Done. Images present {total_downloaded}, failed {total_failed}.")
    print(output_root)
    if args.zip:
        zip_file = zip_directory(output_root, args.zip_path)
        print(f"ZIP: {zip_file}")
    return 2 if total_failed else 0


def check_project(url, output_root, refresh, as_json):
    project, groups = parse_project_page(url, output_root, refresh=refresh)
    metadata = read_json(output_root / "metadata.json")
    remote_sources = list(groups.keys())
    report = {
        "kind": "project",
        "output": str(output_root),
        "project": project,
        "added_images": [],
        "removed_images": [],
        "order_changed": False,
        "missing_metadata": metadata is None,
    }
    if metadata:
        added, removed, order_changed = compare_sources(remote_sources, metadata)
        report["added_images"] = added
        report["removed_images"] = removed
        report["order_changed"] = order_changed

    has_updates = (
        report["missing_metadata"]
        or bool(report["added_images"])
        or bool(report["removed_images"])
        or bool(report["order_changed"])
    )
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not has_updates:
        print("No updates found.")
    else:
        print(f"Updates found for project: {project['name']}")
        if report["missing_metadata"]:
            print("  Missing local metadata.")
        if report["added_images"]:
            print(f"  Added images: {len(report['added_images'])}")
        if report["removed_images"]:
            print(f"  Removed images: {len(report['removed_images'])}")
        if report["order_changed"]:
            print("  Image order changed.")
    return 0


def check_moodboard(url, output_root, refresh, as_json):
    projects = fetch_moodboard_projects(url, output_root, refresh=refresh)
    existing_folders = discover_project_folders(output_root, projects)
    records = load_order_records(output_root / ORDER_FILE_NAME)
    known_ids = {int(record["id"]) for record in records}
    remote_ids = {int(project["id"]) for project in projects}

    report = {
        "kind": "moodboard",
        "output": str(output_root),
        "moodboard_url": url,
        "new_projects": [],
        "removed_from_moodboard": [],
        "project_image_updates": [],
    }

    for project in projects:
        project_id = int(project["id"])
        if project_id not in known_ids:
            report["new_projects"].append(project)

        project_info, groups = parse_project_page(
            project["url"],
            output_root,
            referer=url,
            refresh=refresh,
        )
        project.update(project_info)
        remote_sources = list(groups.keys())
        folder = existing_folders.get(project_id)
        metadata = read_json(folder / "metadata.json") if folder else None
        if not metadata:
            if project_id in known_ids:
                report["project_image_updates"].append(
                    {
                        "project": project,
                        "reason": "missing local metadata",
                        "remote_count": len(remote_sources),
                    }
                )
            continue

        added, removed, order_changed = compare_sources(remote_sources, metadata)
        if added or removed or order_changed:
            report["project_image_updates"].append(
                {
                    "project": project,
                    "added_images": len(added),
                    "removed_images": len(removed),
                    "order_changed": order_changed,
                }
            )

    for project_id in known_ids:
        if project_id not in remote_ids:
            report["removed_from_moodboard"].append({"id": project_id})

    has_updates = any(
        [
            report["new_projects"],
            report["removed_from_moodboard"],
            report["project_image_updates"],
        ]
    )
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif not has_updates:
        print("No updates found.")
    else:
        print(f"Updates found for {url}")
        if report["new_projects"]:
            print(f"  New projects: {len(report['new_projects'])}")
            for project in report["new_projects"]:
                print(f"    - {project['name']} ({project['id']})")
        if report["project_image_updates"]:
            print(f"  Projects with image updates: {len(report['project_image_updates'])}")
            for item in report["project_image_updates"]:
                project = item["project"]
                details = []
                if item.get("reason"):
                    details.append(item["reason"])
                if item.get("added_images"):
                    details.append(f"+{item['added_images']} images")
                if item.get("removed_images"):
                    details.append(f"-{item['removed_images']} images")
                if item.get("order_changed"):
                    details.append("order changed")
                print(f"    - {project['name']} ({', '.join(details)})")
        if report["removed_from_moodboard"]:
            print(f"  Local projects not in remote moodboard: {len(report['removed_from_moodboard'])}")
    return 0


def check_command(args):
    output_root = Path(args.output).expanduser()
    refresh = not args.use_cache
    if is_moodboard_url(args.url):
        return check_moodboard(args.url, output_root, refresh, args.json)
    if is_project_url(args.url):
        return check_project(args.url, output_root, refresh, args.json)
    raise RuntimeError("URL must be a public Behance project or moodboard URL.")


def zip_directory(source, zip_path=None):
    source = Path(source).expanduser()
    if not source.exists() or not source.is_dir():
        raise RuntimeError(f"Folder not found: {source}")
    if zip_path:
        destination = Path(zip_path).expanduser()
    else:
        destination = source.with_suffix(".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()

    destination_abs = destination.resolve()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            if path.resolve() == destination_abs:
                continue
            rel = path.relative_to(source)
            archive.write(path, PurePosixPath(source.name, *rel.parts).as_posix())
    return destination


def zip_command(args):
    zip_file = zip_directory(args.folder, args.zip_path)
    print(f"ZIP: {zip_file}")
    return 0


def probe_command(args):
    url = args.url or "https://www.behance.net/"
    probe_root = Path(args.output).expanduser() if args.output else Path.cwd() / "_behance_probe"
    probe_root.mkdir(parents=True, exist_ok=True)
    probe_file = probe_root / "probe.html"
    print(f"Testing Behance connectivity: {url}")
    try:
        text = fetch_text(url, probe_file, refresh=True)
        if "behance" in text.lower() or len(text) > 0:
            print("Behance is reachable from this environment.")
            if args.remind:
                print("Reminder: if downloads are slow or fail, retry after checking the connection.")
            return 0
        print("Behance responded, but the page content looks unusual.")
        return 1
    except RuntimeError as exc:
        print(
            "Behance is not reachable or the request timed out: "
            + safe_console_text(exc)
        )
        print("Reminder: check the network before starting a large download.")
        return 1


def build_parser():
    parser = argparse.ArgumentParser(
        description="Download, check, and zip public Behance projects or moodboards."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    project_parser = subparsers.add_parser("project", help="Download or update one public Behance project.")
    project_parser.add_argument("url", help="Behance project URL.")
    project_parser.add_argument("--output", required=True, help="Confirmed output folder for this project.")
    project_parser.add_argument("--use-cache", action="store_true", help="Use cached HTML pages.")
    project_parser.add_argument("--force-images", action="store_true", help="Redownload images even if present.")
    project_parser.add_argument("--zip", action="store_true", help="Create a ZIP package after download.")
    project_parser.add_argument("--zip-path", help="ZIP file path when --zip is used.")

    moodboard_parser = subparsers.add_parser(
        "moodboard",
        help="Download or incrementally update one public Behance moodboard.",
    )
    moodboard_parser.add_argument("url", help="Behance moodboard URL.")
    moodboard_parser.add_argument("--output", required=True, help="Confirmed output folder for this moodboard.")
    moodboard_parser.add_argument("--use-cache", action="store_true", help="Use cached HTML pages.")
    moodboard_parser.add_argument("--force-images", action="store_true", help="Redownload images even if present.")
    moodboard_parser.add_argument("--limit", type=int, default=0, help="Limit projects for testing.")
    moodboard_parser.add_argument("--zip", action="store_true", help="Create a ZIP package after download.")
    moodboard_parser.add_argument("--zip-path", help="ZIP file path when --zip is used.")

    check_parser = subparsers.add_parser("check", help="Check a project or moodboard for updates.")
    check_parser.add_argument("url", help="Behance project or moodboard URL.")
    check_parser.add_argument("--output", required=True, help="Existing local output folder.")
    check_parser.add_argument("--use-cache", action="store_true", help="Use cached HTML pages.")
    check_parser.add_argument("--json", action="store_true", help="Print JSON report.")

    zip_parser = subparsers.add_parser("zip", help="Create a ZIP package from an existing folder.")
    zip_parser.add_argument("folder", help="Downloaded project or moodboard folder.")
    zip_parser.add_argument("--zip-path", help="ZIP file path. Defaults to <folder>.zip.")

    probe_parser = subparsers.add_parser("probe", help="Test whether Behance is reachable from this machine.")
    probe_parser.add_argument("url", nargs="?", help="Optional Behance URL to test. Defaults to the Behance homepage.")
    probe_parser.add_argument("--output", help="Folder for the probe cache. Defaults to a local temp folder.")
    probe_parser.add_argument("--remind", action="store_true", help="Print a reminder if Behance is reachable.")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "zip" and not shutil.which("curl.exe"):
        print("curl.exe not found.", file=sys.stderr)
        return 1
    try:
        if args.command == "project":
            return sync_project_command(args)
        if args.command == "moodboard":
            return sync_moodboard_command(args)
        if args.command == "check":
            return check_command(args)
        if args.command == "zip":
            return zip_command(args)
        if args.command == "probe":
            return probe_command(args)
    except RuntimeError as exc:
        print(safe_console_text(exc), file=sys.stderr)
        return 1
    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
