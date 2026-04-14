import asyncio
import logging
import time

import httpx

from app.schemas.workout import ExternalWorkoutResponse

logger = logging.getLogger(__name__)


class ExerciseSearchService:
    def __init__(
        self,
        api_key: str | None,
        host: str,
        base_url: str = "https://edb-with-videos-and-images-by-ascendapi.p.rapidapi.com",
        cache_ttl_seconds: int = 300,
        cache_max_entries: int = 256,
    ):
        self.api_key = api_key
        self.host = host
        self.base_url = base_url.rstrip("/")
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_max_entries = cache_max_entries
        self._search_cache: dict[tuple[str, str, str, str, str, int], tuple[float, list[ExternalWorkoutResponse]]] = {}
        self._detail_cache: dict[str, tuple[float, dict]] = {}
        self._logged_disabled_warning = False

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def search_exercises(
        self,
        *,
        name: str = "",
        muscle: str = "",
        exercise_type: str = "",
        equipment: str = "",
        difficulty: str = "",
        limit: int = 10,
    ) -> list[ExternalWorkoutResponse]:
        if not self.enabled:
            if not self._logged_disabled_warning:
                logger.warning("Ascend external search disabled because ASCEND_RAPIDAPI_KEY is not configured")
                self._logged_disabled_warning = True
            return []

        now = time.time()
        cache_key = (
            name.strip().lower(),
            muscle.strip().lower(),
            exercise_type.strip().lower(),
            equipment.strip().lower(),
            difficulty.strip().lower(),
            limit,
        )
        cached = self._search_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]

        self._evict_expired(now)

        search_parts = [part.strip() for part in [name, muscle, exercise_type, equipment, difficulty] if part and part.strip()]
        use_search_endpoint = bool(search_parts)
        params = {"search": " ".join(search_parts)} if use_search_endpoint else {}
        params["limit"] = str(limit)

        try:
            results = await self._fetch_results(
                endpoint="/api/v1/exercises/search" if use_search_endpoint else "/api/v1/exercises",
                params=params,
            )
        except httpx.HTTPError as exc:
            logger.warning("Exercise API request failed: %s", exc)
            return []

        results = await self._hydrate_tags(results)

        if len(self._search_cache) >= self.cache_max_entries:
            self._search_cache.pop(next(iter(self._search_cache)))
        self._search_cache[cache_key] = (now + self.cache_ttl_seconds, results)
        return results

    async def get_preview_gif(self, exercise_id: str, resolution: int = 180) -> bytes | None:
        if not self.enabled:
            return None

        for endpoint in ("/api/v1/image", "/image"):
            try:
                api_key = self.api_key or ""
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        params={
                            "exerciseId": exercise_id,
                            "resolution": str(resolution),
                        },
                        headers={
                            "x-rapidapi-key": api_key,
                            "x-rapidapi-host": self.host,
                        },
                    )
                    response.raise_for_status()

                content_type = response.headers.get("content-type", "")
                if content_type.startswith("image/"):
                    return response.content
            except httpx.HTTPError:
                continue

        return None

    async def get_exercise_detail(self, exercise_id: str) -> dict | None:
        if not self.enabled:
            return None

        now = time.time()
        cached = self._detail_cache.get(exercise_id)
        if cached and cached[0] > now:
            return cached[1]

        for endpoint in (
            f"/api/v1/exercises/{exercise_id}",
            f"/api/v1/exercises/exercise/{exercise_id}",
        ):
            try:
                payload = await self._fetch_json(endpoint=endpoint, params={})
                detail = self._extract_detail(payload)
                if not detail:
                    continue
                self._detail_cache[exercise_id] = (now + self.cache_ttl_seconds, detail)
                return detail
            except httpx.HTTPError:
                continue

        return None

    async def _fetch_results(self, endpoint: str, params: dict[str, str]) -> list[ExternalWorkoutResponse]:
        payload = await self._fetch_json(endpoint=endpoint, params=params)
        rows = payload.get("data", []) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return []
        return [self._to_external_workout(item) for item in rows]

    async def _fetch_json(self, endpoint: str, params: dict[str, str]) -> dict | list:
        api_key = self.api_key or ""
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers={
                    "x-rapidapi-key": api_key,
                    "x-rapidapi-host": self.host,
                },
            )
            response.raise_for_status()
        return response.json()

    def _extract_detail(self, payload: dict | list) -> dict | None:
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, dict):
                return data
            if isinstance(data, list) and data:
                first = data[0]
                return first if isinstance(first, dict) else None
            return payload
        if isinstance(payload, list) and payload:
            first = payload[0]
            return first if isinstance(first, dict) else None
        return None

    def _evict_expired(self, now: float) -> None:
        expired = [key for key, (expires_at, _) in self._search_cache.items() if expires_at <= now]
        for key in expired:
            self._search_cache.pop(key, None)

        detail_expired = [key for key, (expires_at, _) in self._detail_cache.items() if expires_at <= now]
        for key in detail_expired:
            self._detail_cache.pop(key, None)

    def _to_external_workout(self, item: dict) -> ExternalWorkoutResponse:
        instructions_list = item.get("instructions") or []
        overview = item.get("overview") or ""
        body_parts = item.get("bodyParts") or []
        exercise_type = item.get("exerciseType")
        equipments = item.get("equipments") or []
        exercise_id = item.get("exerciseId") or item.get("id")

        primary_muscle_raw = self._pick_primary_text(body_parts) or "Unknown"
        category_raw = self._pick_primary_text(exercise_type) or "Strength"

        return ExternalWorkoutResponse(
            id=str(exercise_id) if exercise_id is not None else None,
            name=(item.get("name") or "Unknown Exercise").strip().title(),
            description=overview[:240],
            muscle_group=str(primary_muscle_raw).replace("_", " ").title(),
            category=str(category_raw).replace("_", " ").title(),
            equipment=(", ".join([str(eq).replace("_", " ").title() for eq in equipments]) or None),
            difficulty=(item.get("difficultyLevel") or None),
            instructions=(" ".join(instructions_list) if instructions_list else None),
            image_url=item.get("imageUrl") or None,
            video_url=item.get("videoUrl") or None,
        )

    def _pick_primary_text(self, value: str | list | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            for item in value:
                text = str(item).strip()
                if text:
                    return text
            return None
        text = str(value).strip()
        return text or None

    async def _hydrate_tags(self, rows: list[ExternalWorkoutResponse]) -> list[ExternalWorkoutResponse]:
        candidates = [row for row in rows if row.id and self._needs_tag_hydration(row)]
        if not candidates:
            return rows

        details = await asyncio.gather(*(self.get_exercise_detail(row.id) for row in candidates))
        detail_map = {row.id: detail for row, detail in zip(candidates, details) if detail}

        hydrated: list[ExternalWorkoutResponse] = []
        for row in rows:
            detail = detail_map.get(row.id) if row.id else None
            if not detail:
                hydrated.append(row)
                continue
            hydrated.append(self._merge_detail_tags(row, detail))
        return hydrated

    def _needs_tag_hydration(self, row: ExternalWorkoutResponse) -> bool:
        return not self._is_meaningful_value(row.muscle_group) or not self._is_meaningful_value(row.category)

    def _is_meaningful_value(self, value: str | None) -> bool:
        return bool(value and value.strip() and value.strip().lower() != "unknown")

    def _merge_detail_tags(self, row: ExternalWorkoutResponse, detail: dict) -> ExternalWorkoutResponse:
        primary_muscle = self._pick_primary_text(detail.get("bodyParts"))
        category = self._pick_primary_text(detail.get("exerciseType"))

        updates = {}
        if primary_muscle and not self._is_meaningful_value(row.muscle_group):
            updates["muscle_group"] = str(primary_muscle).replace("_", " ").title()
        if category and not self._is_meaningful_value(row.category):
            updates["category"] = str(category).replace("_", " ").title()
        if not updates:
            return row
        return row.model_copy(update=updates)
