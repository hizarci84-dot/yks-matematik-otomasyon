import os
import re
import json
import hashlib
import subprocess
import unicodedata


TURKISH_CHAR_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "İ": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})

INITIAL_PUBLISHED_TEST = {
    "slug": "357_yillik_hatayi_duzeltmek",
    "title": "357 Yıllık Hatayı Düzeltmek",
    "source_file": "357_Yıllık_Hatayı_Düzeltmek.mp4",
    "sha256": "bf656789304fa1b398af44c6e91d3a41e82599c8c78b39b785f3008b1a928f1a",
    "video_path": "dist/stories/short_videos/357_yillik_hatayi_duzeltmek.mp4",
    "published_at": "2026-11-20 12:43:28",
    "result": {
        "status": "success",
        "method": "official_meta_graph_api",
        "story_ids": ["17888965614504531"],
        "reels_id": None,
    },
}


def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify_filename(filename):
    """Convert a Turkish/arbitrary video filename into a URL-safe ASCII .mp4 filename."""
    stem, ext = os.path.splitext(filename)
    stem = stem.translate(TURKISH_CHAR_MAP)
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    stem = re.sub(r"[^a-zA-Z0-9]+", "_", stem).strip("_").lower()
    return f"{stem}{ext.lower() or '.mp4'}"


def _is_copy_filename(filename):
    """Return True for browser duplicate suffixes like 'Video (1).mp4'."""
    stem = os.path.splitext(filename)[0]
    return bool(re.search(r"\s\(\d+\)$", stem))


def deduplicate_source_files(input_dir):
    """Return unique source .mp4 entries sorted canonically, preferring non-(N) filenames."""
    candidates = sorted(
        (f for f in os.listdir(input_dir) if f.lower().endswith(".mp4")),
        key=lambda f: (_is_copy_filename(f), f.lower()),
    )
    unique_items = []
    seen_hashes = {}
    duplicates = []

    for fname in candidates:
        full_path = os.path.join(input_dir, fname)
        file_hash = compute_sha256(full_path)
        if file_hash in seen_hashes:
            duplicates.append((fname, seen_hashes[file_hash]))
            continue
        seen_hashes[file_hash] = fname
        unique_items.append((fname, full_path, file_hash))

    # Re-sort final unique list deterministically by canonical filename
    unique_items.sort(key=lambda item: item[0].lower())
    return unique_items, duplicates


def probe_video_info(video_path):
    """Return duration (seconds) and resolution (width, height) via ffmpeg stderr parsing."""
    res = subprocess.run(
        ["ffmpeg", "-i", video_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    stderr = res.stderr

    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if not dur_match:
        raise RuntimeError(f"Could not determine duration for {video_path}")
    hours, mins, secs = map(float, dur_match.groups())
    duration = hours * 3600 + mins * 60 + secs

    dim_match = re.search(r"Video:.*?,\s*(\d+)x(\d+)\b", stderr)
    width, height = (int(dim_match.group(1)), int(dim_match.group(2))) if dim_match else (None, None)

    return {"duration": duration, "width": width, "height": height}


def build_atempo_filter(speed):
    """Build a valid ffmpeg atempo filter chain (each stage within 0.5..2.0)."""
    if abs(speed - 1.0) < 1e-4:
        return None
    stages = []
    remaining = speed
    while remaining > 2.0:
        stages.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        stages.append("atempo=0.5")
        remaining /= 0.5
    stages.append(f"atempo={remaining:.6f}")
    return ",".join(stages)


def _adopt_legacy_numbered_output(output_dir, out_name):
    """Rename earlier short_XX_<slug>.mp4 output to stable <slug>.mp4 to avoid re-encoding."""
    target_path = os.path.join(output_dir, out_name)
    if os.path.exists(target_path) or not os.path.isdir(output_dir):
        return
    pattern = re.compile(rf"^short_\d+_{re.escape(out_name)}$")
    for existing in os.listdir(output_dir):
        if pattern.match(existing):
            os.replace(os.path.join(output_dir, existing), target_path)
            break


def process_video(input_path, output_path, target_duration=58.5, overwrite=False):
    """Speed up a 9:16 short video cleanly to fit strictly under Instagram Story's 60s limit."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    info = probe_video_info(input_path)
    orig_duration = info["duration"]

    if os.path.exists(output_path) and not overwrite:
        out_info = probe_video_info(output_path)
        if out_info["duration"] <= 59.8:
            return {
                "input_path": input_path.replace("\\", "/"),
                "output_path": output_path.replace("\\", "/"),
                "original_duration": orig_duration,
                "output_duration": out_info["duration"],
                "speed": orig_duration / target_duration if orig_duration > target_duration else 1.0,
                "width": out_info["width"],
                "height": out_info["height"],
                "size_bytes": os.path.getsize(output_path),
                "skipped_existing": True,
            }

    speed = orig_duration / target_duration if orig_duration > target_duration else 1.0

    cmd = ["ffmpeg", "-y", "-i", input_path]

    vf_parts = []
    if speed > 1.0:
        vf_parts.append(f"setpts=PTS/{speed:.8f}")
    vf_parts.append("setsar=1")
    cmd.extend(["-vf", ",".join(vf_parts)])

    af = build_atempo_filter(speed)
    if af:
        cmd.extend(["-af", af])

    cmd.extend([
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "21",
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-movflags", "+faststart",
        output_path,
    ])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed for {input_path}:\n{result.stderr[-1000:]}")

    out_info = probe_video_info(output_path)
    if out_info["duration"] >= 60.0:
        raise RuntimeError(
            f"Output video {output_path} duration ({out_info['duration']:.2f}s) is still >= 60s!"
        )

    return {
        "input_path": input_path.replace("\\", "/"),
        "output_path": output_path.replace("\\", "/"),
        "original_duration": orig_duration,
        "output_duration": out_info["duration"],
        "speed": speed,
        "width": out_info["width"],
        "height": out_info["height"],
        "size_bytes": os.path.getsize(output_path),
        "skipped_existing": False,
    }


def process_all_videos(
    input_dir="hikaye videolari",
    output_dir="dist/stories/short_videos",
    target_duration=58.5,
    overwrite=False,
):
    """Deduplicate and process all unique .mp4 files into Instagram-Story-ready <=58.5s clips."""
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    unique_items, duplicates = deduplicate_source_files(input_dir)
    if not unique_items:
        raise RuntimeError(f"No .mp4 files found in {input_dir}")

    for dup_name, orig_name in duplicates:
        print(f"Skipping duplicate file: {dup_name} (identical to {orig_name})")

    results = []
    for idx, (fname, in_path, file_hash) in enumerate(unique_items, start=1):
        out_name = slugify_filename(fname)
        slug = os.path.splitext(out_name)[0]
        _adopt_legacy_numbered_output(output_dir, out_name)
        out_path = os.path.join(output_dir, out_name)

        print(f"[{idx}/{len(unique_items)}] Processing {fname} -> {out_name} ...")
        meta = process_video(in_path, out_path, target_duration=target_duration, overwrite=overwrite)
        meta["slug"] = slug
        meta["source_file"] = fname
        meta["sha256"] = file_hash
        meta["title"] = os.path.splitext(fname)[0].replace("_", " ").strip()
        results.append(meta)

        status_tag = "cached" if meta["skipped_existing"] else "encoded"
        print(
            f"   -> [{status_tag}] {meta['original_duration']:.2f}s -> {meta['output_duration']:.2f}s "
            f"({meta['speed']:.2f}x, {meta['size_bytes'] / (1024*1024):.2f} MB)"
        )

    return results


def sync_short_video_queue(manifest_items, state_path="data/short_video_state.json"):
    """Update short_video_state.json queue without disturbing published history or order."""
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        # Seed with the live test video already published on 2026-11-20
        seed_entry = dict(INITIAL_PUBLISHED_TEST)
        for item in manifest_items:
            if item["slug"] == seed_entry["slug"]:
                seed_entry["sha256"] = item["sha256"]
                seed_entry["video_path"] = item["output_path"]
                break
        state = {
            "last_published_date": seed_entry["published_at"],
            "published_history": [seed_entry],
            "queue": [],
        }

    published_hashes = {e.get("sha256") for e in state.get("published_history", []) if e.get("sha256")}
    published_slugs = {e.get("slug") for e in state.get("published_history", []) if e.get("slug")}

    by_slug = {item["slug"]: item for item in manifest_items}
    existing_queue = state.get("queue", [])

    # Keep existing pending queue items in their current order, refreshing metadata
    new_queue = []
    queued_slugs = set()
    for q in existing_queue:
        slug = q.get("slug")
        sha = q.get("sha256")
        if slug in published_slugs or (sha and sha in published_hashes):
            continue
        if slug in by_slug:
            item = by_slug[slug]
            new_queue.append({
                "slug": item["slug"],
                "title": item["title"],
                "source_file": item["source_file"],
                "sha256": item["sha256"],
                "video_path": item["output_path"],
                "duration": round(item["output_duration"], 2),
                "speed": round(item["speed"], 2),
            })
            queued_slugs.add(slug)

    # Append newly added items to the end of the queue
    for item in manifest_items:
        slug = item["slug"]
        if slug in published_slugs or item["sha256"] in published_hashes or slug in queued_slugs:
            continue
        new_queue.append({
            "slug": slug,
            "title": item["title"],
            "source_file": item["source_file"],
            "sha256": item["sha256"],
            "video_path": item["output_path"],
            "duration": round(item["output_duration"], 2),
            "speed": round(item["speed"], 2),
        })
        queued_slugs.add(slug)

    state["queue"] = new_queue
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return state


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Speed up 9:16 short videos to fit Instagram Stories (<60s)")
    parser.add_argument("--input-dir", default="hikaye videolari")
    parser.add_argument("--output-dir", default="dist/stories/short_videos")
    parser.add_argument("--target-duration", type=float, default=58.5)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--manifest", default="data/short_videos_manifest.json")
    parser.add_argument("--state", default="data/short_video_state.json")
    args = parser.parse_args()

    items = process_all_videos(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        target_duration=args.target_duration,
        overwrite=args.overwrite,
    )
    if args.manifest:
        os.makedirs(os.path.dirname(args.manifest), exist_ok=True)
        with open(args.manifest, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"\nSaved manifest: {args.manifest} ({len(items)} unique videos)")

    if args.state:
        queue_state = sync_short_video_queue(items, state_path=args.state)
        print(
            f"Synced queue state: {args.state} "
            f"(published={len(queue_state['published_history'])}, queued={len(queue_state['queue'])})"
        )
        import sys as _sys
        _sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from engine.youtube_bridge import sync_to_youtube_automation
        sync_to_youtube_automation(args.state)
