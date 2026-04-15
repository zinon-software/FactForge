"""
utils/video_sources.py — Background video downloading for FactForge.

Source priority per segment: Pexels → Coverr → Pixabay.
Deduplication is tracked per-provider per VideoSources instance so no two
segments within the same video share an identical clip.

Usage:
    from utils.video_sources import VideoSources
    vs = VideoSources()
    count = vs.download_all("S01234", segments)
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests

from utils.config import cfg

logger = logging.getLogger(__name__)


class VideoSources:
    """Downloads unique background video clips for Short video segments."""

    # ── Fallback query chains per segment type ────────────────────────────────
    _TYPE_FALLBACKS: dict[str, list[str]] = {
        "hook":   ["dramatic reveal", "cinematic landscape", "aerial city"],
        "fact":   ["documentary footage", "world map", "research data"],
        "impact": ["explosion effect", "shock wave", "dramatic moment"],
        "number": ["financial data", "statistics screen", "stock market"],
        "cta":    ["subscribe notification", "social media phone", "modern city"],
    }
    _GENERIC_FALLBACKS: list[str] = [
        "city aerial",
        "nature landscape",
        "technology abstract",
        "ocean waves",
        "crowd people",
    ]

    def __init__(self) -> None:
        self._used_pexels:  set = set()
        self._used_coverr:  set = set()
        self._used_pixabay: set = set()

    # ── Public interface ──────────────────────────────────────────────────────

    def fetch_pexels(
        self, query: str, out_path: Path, fallbacks: Optional[list] = None
    ) -> bool:
        """
        Download a unique HD portrait video from Pexels.

        Tries ``query`` first, then each entry of ``fallbacks`` in order.
        Skips video IDs that were already downloaded in this session.
        Returns True on success.
        """
        api_key = cfg.pexels_key()
        headers = {"Authorization": api_key}
        all_queries = [query] + (fallbacks or [])

        for attempt_query in all_queries:
            params = {
                "query": attempt_query,
                "per_page": 15,
                "size": "medium",
                "orientation": "portrait",  # required for Shorts
            }
            try:
                r = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers=headers,
                    params=params,
                    timeout=30,
                )
            except requests.RequestException as exc:
                logger.warning("Pexels request error for '%s': %s", attempt_query, exc)
                continue

            if r.status_code != 200:
                logger.warning("Pexels API %d for '%s'", r.status_code, attempt_query)
                continue

            videos = r.json().get("videos", [])
            if not videos:
                logger.debug("No Pexels results for '%s'", attempt_query)
                continue

            for vid in videos:
                pexels_id = vid["id"]
                if pexels_id in self._used_pexels:
                    continue

                files = sorted(
                    vid.get("video_files", []),
                    key=lambda f: 1 if f.get("quality") == "hd" else 0,
                    reverse=True,
                )
                video_url = next(
                    (
                        f["link"]
                        for f in files
                        if f.get("quality") in ("hd", "sd")
                        and f.get("file_type") == "video/mp4"
                    ),
                    None,
                )
                if not video_url:
                    continue

                if self._download_stream(video_url, out_path):
                    self._used_pexels.add(pexels_id)
                    label = f" (fallback: '{attempt_query}')" if attempt_query != query else ""
                    logger.info(
                        "  ✓ %s — pexels#%s%s (%dKB)",
                        out_path.name, pexels_id, label,
                        out_path.stat().st_size // 1024,
                    )
                    return True

            logger.debug(
                "All %d Pexels results for '%s' already used",
                len(videos), attempt_query,
            )

        logger.warning("Pexels: no unique result for '%s' after all fallbacks", query)
        return False

    def fetch_coverr(
        self, query: str, out_path: Path, fallbacks: Optional[list] = None
    ) -> bool:
        """
        Download a unique non-premium video from Coverr.

        CDN pattern: https://cdn.coverr.co/videos/{slug}/{slug}.mp4
        Prefers non-premium clips. Returns True on success.
        """
        headers = {"Authorization": f"Bearer {cfg.coverr_key()}"}
        all_queries = [query] + (fallbacks or [])

        for attempt_query in all_queries:
            try:
                r = requests.get(
                    "https://api.coverr.co/videos",
                    headers=headers,
                    params={"query": attempt_query, "per_page": 15},
                    timeout=20,
                )
                if r.status_code != 200:
                    logger.warning("Coverr %d for '%s'", r.status_code, attempt_query)
                    continue

                videos = r.json().get("hits", [])
                if not videos:
                    continue

                sorted_vids = sorted(videos, key=lambda v: v.get("is_premium", True))

                for vid in sorted_vids:
                    vid_id = vid.get("slug") or str(vid.get("id", ""))
                    if vid_id in self._used_coverr:
                        continue
                    if vid.get("is_premium"):
                        continue

                    try:
                        rv = requests.get(
                            f"https://api.coverr.co/videos/{vid_id}",
                            headers=headers,
                            timeout=10,
                        )
                        if rv.status_code != 200:
                            continue
                        mp4_url = (
                            rv.json().get("urls", {}).get("mp4_preview")
                            or rv.json().get("urls", {}).get("mp4")
                        )
                        if not mp4_url:
                            continue
                    except Exception as exc:
                        logger.debug("Coverr detail fetch error: %s", exc)
                        continue

                    if self._download_stream(mp4_url, out_path):
                        self._used_coverr.add(vid_id)
                        logger.info(
                            "  ✓ %s — coverr/%s (query: '%s') (%dKB)",
                            out_path.name, vid_id, attempt_query,
                            out_path.stat().st_size // 1024,
                        )
                        return True

            except Exception as exc:
                logger.warning("Coverr error for '%s': %s", attempt_query, exc)

            time.sleep(0.3)

        logger.warning("Coverr: no unique result for '%s' after all fallbacks", query)
        return False

    def fetch_pixabay(
        self, query: str, out_path: Path, fallbacks: Optional[list] = None
    ) -> bool:
        """
        Download a unique video from Pixabay (commercial use, no attribution required).

        Prefers medium quality portrait clips. Returns True on success.
        """
        all_queries = [query] + (fallbacks or [])

        for attempt_query in all_queries:
            try:
                r = requests.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": cfg.pixabay_key(),
                        "q": attempt_query,
                        "per_page": 15,
                        "video_type": "film",
                        "safesearch": "true",
                        "orientation": "vertical",  # required for Shorts
                    },
                    timeout=20,
                )
                if r.status_code != 200:
                    logger.warning("Pixabay %d for '%s'", r.status_code, attempt_query)
                    continue

                videos = r.json().get("hits", [])
                if not videos:
                    continue

                for vid in videos:
                    vid_id = vid["id"]
                    if vid_id in self._used_pixabay:
                        continue

                    sizes = vid.get("videos", {})
                    clip = (
                        sizes.get("medium")
                        or sizes.get("small")
                        or sizes.get("large")
                        or sizes.get("tiny")
                    )
                    mp4_url = clip.get("url") if clip else None
                    if not mp4_url:
                        continue

                    if self._download_stream(mp4_url, out_path):
                        self._used_pixabay.add(vid_id)
                        logger.info(
                            "  ✓ %s — pixabay#%s (query: '%s') (%dKB)",
                            out_path.name, vid_id, attempt_query,
                            out_path.stat().st_size // 1024,
                        )
                        return True

            except Exception as exc:
                logger.warning("Pixabay error for '%s': %s", attempt_query, exc)

            time.sleep(0.3)

        logger.warning("Pixabay: no unique result for '%s' after all fallbacks", query)
        return False

    def fetch_segment(
        self, query: str, seg_type: str, out_path: Path
    ) -> bool:
        """
        Try Pexels → Coverr → Pixabay for a single segment clip.

        ``query`` is the primary scene_query.  Appends type-specific and
        generic fallback terms automatically.  Returns True if any source
        succeeded.
        """
        fallbacks = self._TYPE_FALLBACKS.get(seg_type, []) + self._GENERIC_FALLBACKS

        ok = self.fetch_pexels(query, out_path, fallbacks)
        if not ok:
            logger.info("  ↳ Pexels failed — trying Coverr…")
            ok = self.fetch_coverr(query, out_path, fallbacks)
        if not ok:
            logger.info("  ↳ Coverr failed — trying Pixabay…")
            ok = self.fetch_pixabay(query, out_path, fallbacks)
        if not ok:
            logger.warning(
                "  ✗ All sources (Pexels, Coverr, Pixabay) failed for '%s'", query
            )
        return ok

    def download_all(self, video_id: str, segments: list) -> int:
        """
        Download background clips for every segment in ``segments``.

        Reads ``backgroundVideo`` and ``scene_query`` / filename stem from
        each segment dict.  Skips files that already exist and are > 10 KB.

        Returns the number of successfully downloaded clips.
        """
        bg_dir = cfg.OUTPUT_DIR / video_id / "bg_videos"
        bg_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Fetching %d unique background clips (Pexels → Coverr → Pixabay)…",
            len(segments),
        )
        success = 0

        for i, seg in enumerate(segments):
            bg_path_str: str = seg.get("backgroundVideo", "")
            if not bg_path_str:
                continue

            out_filename = Path(bg_path_str).name
            out_path     = bg_dir / out_filename

            if out_path.exists() and out_path.stat().st_size > 10_000:
                logger.debug("  [SKIP] %s already downloaded", out_filename)
                success += 1
                continue

            primary_query = seg.get("scene_query") or self._query_from_filename(bg_path_str)
            seg_type      = seg.get("type", "fact")

            logger.info(
                "  [%d/%d] '%s' → %s",
                i + 1, len(segments), primary_query, out_filename,
            )

            if self.fetch_segment(primary_query, seg_type, out_path):
                success += 1

            time.sleep(0.4)

        total_mp4 = len(list(bg_dir.glob("*.mp4")))
        logger.info(
            "bg_videos ready in %s (%d unique clips, %d/%d fetched this run)",
            bg_dir, total_mp4, success, len(segments),
        )
        return success

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _query_from_filename(bg_video_path: str) -> str:
        """
        Derive a human-readable search query from a segment's backgroundVideo
        path, e.g. ``"S00893/bg_videos/mosque_dome.mp4"`` → ``"mosque dome"``.
        """
        name  = Path(bg_video_path).stem
        query = re.sub(r"[_\-]+", " ", name)
        return re.sub(r"\s+", " ", query).strip()

    @staticmethod
    def _download_stream(url: str, out_path: Path) -> bool:
        """Stream-download ``url`` to ``out_path``. Returns True on success."""
        try:
            dl = requests.get(url, timeout=120, stream=True)
            if dl.status_code != 200:
                return False
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as fh:
                for chunk in dl.iter_content(chunk_size=1024 * 256):
                    fh.write(chunk)
            return True
        except Exception as exc:
            logger.debug("Stream download failed (%s): %s", url[:60], exc)
            return False
