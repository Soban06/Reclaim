"""Download the original ASOS GraphReturns files and record provenance.

Usage: python "data scripts/download_data.py" [--split training|testing|all]
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.osf.io/v2/nodes/c793h/files/osfstorage/"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["training", "testing", "all"], default="training")
    args = parser.parse_args()
    raw = ROOT / "data" / "raw"
    evidence = ROOT / "reports" / "evidence"
    raw.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    with urlopen(API, timeout=60) as response:
        listing = json.load(response)
    (evidence / "osf_file_listing.json").write_text(json.dumps(listing, indent=2), encoding="utf-8")
    with urlopen("https://api.osf.io/v2/nodes/c793h/", timeout=60) as response:
        node = json.load(response)
    license_url = node["data"]["relationships"]["license"]["links"]["related"]["href"]
    with urlopen(license_url, timeout=60) as response:
        license_info = json.load(response)
    (evidence / "dataset_metadata.json").write_text(
        json.dumps({"node": node, "license": license_info}, indent=2), encoding="utf-8")
    manifest = []
    for item in listing["data"]:
        attrs = item["attributes"]
        name = attrs["name"]
        if not name.endswith(".p") or (args.split != "all" and args.split not in name):
            continue
        path = raw / name
        expected = attrs["extra"]["hashes"]["sha256"]
        if not path.exists() or digest(path) != expected:
            print("Downloading", name, attrs["size"], "bytes", flush=True)
            partial = path.with_suffix(".partial")
            with urlopen(item["links"]["download"], timeout=120) as response, partial.open("wb") as out:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(chunk)
            if digest(partial) != expected:
                raise ValueError(f"SHA256 mismatch: {name}")
            partial.replace(path)
        manifest.append({"file": name, "source": item["links"]["download"],
                         "bytes": path.stat().st_size, "sha256": digest(path),
                         "verified_utc": datetime.now(timezone.utc).isoformat()})
        print("Verified", name, flush=True)
        (evidence / f"download_manifest_{args.split}.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
