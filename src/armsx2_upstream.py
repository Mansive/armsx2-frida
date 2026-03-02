import argparse
import json
import re
from pathlib import Path
from typing import Any, Callable

import requests


PACKAGE_NAME = "come.nanodata.armsx2"
RELEASES_API_URL = "https://api.github.com/repos/Mansive/ARMSX2/releases"
DEFAULT_TIMEOUT_SECONDS = 300

APK_NAME_PATTERN = re.compile(r"\.apk$", flags=re.IGNORECASE)
SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

HttpGet = Callable[..., Any]


def fetch_releases(
    *,
    http_get: HttpGet = requests.get,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    response = http_get(RELEASES_API_URL, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError("Unexpected GitHub API payload: expected a release list")

    return payload


def select_latest_release(releases: list[dict[str, Any]]) -> dict[str, Any]:
    for release in releases:
        if not release.get("draft", False):
            return release

    raise ValueError("No non-draft releases were found for Mansive/ARMSX2")


def extract_apk_asset(release: dict[str, Any]) -> dict[str, Any]:
    assets = release.get("assets") or []
    for asset in assets:
        name = str(asset.get("name") or "")
        if APK_NAME_PATTERN.search(name) and asset.get("browser_download_url"):
            return asset

    raise ValueError("No APK asset was found in the selected ARMSX2 release")


def _sanitize_fragment(fragment: str) -> str:
    sanitized = SAFE_FILENAME_CHARS.sub("_", fragment.strip())
    return sanitized.strip("._-") or "unknown"


def build_metadata_from_release(release: dict[str, Any]) -> dict[str, Any]:
    asset = extract_apk_asset(release)

    tag_name = str(release.get("tag_name") or "")
    if not tag_name:
        raise ValueError("Selected ARMSX2 release has no tag_name")

    release_id = int(release.get("id") or 0)
    if release_id <= 0:
        raise ValueError("Selected ARMSX2 release has an invalid id")

    return {
        "package_name": PACKAGE_NAME,
        "release_tag": tag_name,
        "release_name": str(release.get("name") or tag_name),
        "release_id": release_id,
        "prerelease": bool(release.get("prerelease", False)),
        "published_at": release.get("published_at"),
        "target_commitish": release.get("target_commitish"),
        "apk_name": asset["name"],
        "apk_url": asset["browser_download_url"],
        "apk_size": asset.get("size"),
    }


def fetch_latest_armsx2_metadata(
    *,
    http_get: HttpGet = requests.get,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    releases = fetch_releases(http_get=http_get, timeout=timeout)
    latest = select_latest_release(releases)
    return build_metadata_from_release(latest)


def create_download_filename(metadata: dict[str, Any]) -> str:
    package_name = _sanitize_fragment(str(metadata["package_name"]))
    release_tag = _sanitize_fragment(str(metadata["release_tag"]))
    return f"{package_name}_{release_tag}.apk"


def download_latest_apk(
    metadata: dict[str, Any],
    *,
    download_dir: Path = Path("downloads"),
    http_get: HttpGet = requests.get,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Path:
    apk_url = metadata["apk_url"]
    apk_name = create_download_filename(metadata)
    apk_path = Path(download_dir) / apk_name

    apk_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = apk_path.with_suffix(".apk.part")

    response = http_get(apk_url, stream=True, timeout=timeout)
    response.raise_for_status()

    with temp_path.open("wb") as output_file:
        if hasattr(response, "iter_content"):
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output_file.write(chunk)
        else:
            output_file.write(response.content)

    temp_path.replace(apk_path)
    return apk_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check and download the latest ARMSX2 APK from GitHub releases"
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--check", action="store_true", help="Only check for latest release metadata"
    )
    action_group.add_argument(
        "--download", action="store_true", help="Download the latest release APK"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print machine-readable JSON",
    )
    parser.add_argument(
        "--downloads-dir",
        default="downloads",
        help="Output directory for downloaded APKs",
    )
    return parser.parse_args()


def _print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload))
        return

    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    args = parse_args()

    metadata = fetch_latest_armsx2_metadata()

    if args.check:
        _print_payload(metadata, as_json=args.as_json)
        return 0

    apk_path = download_latest_apk(metadata, download_dir=Path(args.downloads_dir))
    payload = {
        **metadata,
        "download_name": create_download_filename(metadata),
        "download_path": str(apk_path),
    }
    _print_payload(payload, as_json=args.as_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
