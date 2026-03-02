#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${PACKAGE_NAME:-}" ]]; then
  echo "PACKAGE_NAME is required." >&2
  exit 1
fi

if [[ -z "${RELEASE_ID:-}" ]]; then
  echo "RELEASE_ID is required." >&2
  exit 1
fi

if [[ -z "${APK_PATH:-}" ]]; then
  echo "APK_PATH is required." >&2
  exit 1
fi

if [[ -z "${APKTOOL_JAR:-}" ]]; then
  echo "APKTOOL_JAR is required." >&2
  exit 1
fi

unsigned_apk="${RUNNER_TEMP}/${PACKAGE_NAME}_${RELEASE_ID}_frida-unsigned.apk"

python src/repack.py \
  --apk "$APK_PATH" \
  --out "$unsigned_apk" \
  --apktool-jar "$APKTOOL_JAR" \
  --android-version-code "$RELEASE_ID"

echo "unsigned_apk=$unsigned_apk" >> "${GITHUB_OUTPUT}"
