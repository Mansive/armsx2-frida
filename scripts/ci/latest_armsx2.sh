#!/usr/bin/env bash
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to parse JSON." >&2
  exit 1
fi

metadata_json=$(python src/armsx2_upstream.py --check --json)

release_tag=$(printf '%s' "$metadata_json" | jq -r '.release_tag')
release_name=$(printf '%s' "$metadata_json" | jq -r '.release_name')
release_id=$(printf '%s' "$metadata_json" | jq -r '.release_id')
prerelease=$(printf '%s' "$metadata_json" | jq -r '.prerelease')
published_at=$(printf '%s' "$metadata_json" | jq -r '.published_at')
target_commitish=$(printf '%s' "$metadata_json" | jq -r '.target_commitish')
apk_name=$(printf '%s' "$metadata_json" | jq -r '.apk_name')
apk_url=$(printf '%s' "$metadata_json" | jq -r '.apk_url')

{
  echo "release_tag=${release_tag}"
  echo "release_name=${release_name}"
  echo "release_id=${release_id}"
  echo "prerelease=${prerelease}"
  echo "published_at=${published_at}"
  echo "target_commitish=${target_commitish}"
  echo "apk_name=${apk_name}"
  echo "apk_url=${apk_url}"
} >> "${GITHUB_OUTPUT}"
