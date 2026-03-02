from pathlib import Path

import pytest

import armsx2_upstream


class FakeResponse:
    def __init__(self, *, json_data=None, chunks=None):
        self._json_data = json_data
        self._chunks = chunks or []

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size: int = 8192):
        del chunk_size
        for chunk in self._chunks:
            yield chunk


def _sample_releases_payload() -> list[dict]:
    return [
        {
            "id": 100,
            "tag_name": "draft-release",
            "name": "Draft Release",
            "draft": True,
            "prerelease": False,
            "assets": [
                {
                    "name": "ignored.apk",
                    "browser_download_url": "https://example.com/ignored.apk",
                }
            ],
        },
        {
            "id": 101,
            "tag_name": "come.nanodata.armsx2-nightly-1.0.8-20260302-2027",
            "name": "Nightly Build (DEBUG - 1.0.8) - 20260302-2027",
            "draft": False,
            "prerelease": True,
            "published_at": "2026-03-02T20:27:00Z",
            "target_commitish": "master",
            "assets": [
                {
                    "name": "android-nightly.apk",
                    "browser_download_url": "https://github.com/Mansive/ARMSX2/releases/download/x/android-nightly.apk",
                    "size": 42,
                }
            ],
        },
    ]


def test_fetch_latest_armsx2_metadata_selects_first_non_draft_release() -> None:
    payload = _sample_releases_payload()

    def fake_get(url: str, timeout: int = 300):
        assert url == armsx2_upstream.RELEASES_API_URL
        assert timeout == 300
        return FakeResponse(json_data=payload)

    metadata = armsx2_upstream.fetch_latest_armsx2_metadata(http_get=fake_get)

    assert metadata["release_id"] == 101
    assert metadata["release_tag"] == "come.nanodata.armsx2-nightly-1.0.8-20260302-2027"
    assert metadata["prerelease"] is True
    assert metadata["apk_name"] == "android-nightly.apk"


def test_build_metadata_raises_when_apk_asset_missing() -> None:
    release = {
        "id": 101,
        "tag_name": "tag",
        "draft": False,
        "assets": [{"name": "notes.txt", "browser_download_url": "https://example.com/notes.txt"}],
    }

    with pytest.raises(ValueError):
        armsx2_upstream.build_metadata_from_release(release)


def test_download_latest_apk_writes_binary_chunks(tmp_path: Path) -> None:
    metadata = {
        "package_name": "come.nanodata.armsx2",
        "release_tag": "come.nanodata.armsx2-nightly-1.0.8-20260302-2027",
        "apk_url": "https://github.com/Mansive/ARMSX2/releases/download/x/android-nightly.apk",
    }

    def fake_get(url: str, stream: bool = True, timeout: int = 300):
        assert url.endswith("android-nightly.apk")
        assert stream is True
        assert timeout == 300
        return FakeResponse(chunks=[b"abc", b"123"])

    apk_path = armsx2_upstream.download_latest_apk(
        metadata,
        download_dir=tmp_path,
        http_get=fake_get,
    )

    assert apk_path == tmp_path / "come.nanodata.armsx2_come.nanodata.armsx2-nightly-1.0.8-20260302-2027.apk"
    assert apk_path.read_bytes() == b"abc123"
