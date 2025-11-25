from typing import List

from avelbot_ingestion.models.Source import Source
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum
from avelbot_ingestion.models.StageEnum import StageEnum


def deduplicate_sources(sources: List[Source]) -> List[Source]:
    """
    Deduplicate sources based on their URI, keeping the one that is the most advanced.

    Priority rules:
    - Primary: current_stage
        INDEXING > CHUNKING > CONVERTION > SCRAPING > CRAWLING
    - Secondary: current_status
        COMPLETED > IN_PROGRESS > DISCOVERED
    """
    stage_rank = {
        StageEnum.CRAWLING: 0,
        StageEnum.SCRAPING: 1,
        StageEnum.CONVERTION: 2,
        StageEnum.CHUNKING: 3,
        StageEnum.INDEXING: 4,
    }

    status_rank = {
        SourceStatusEnum.DISCOVERED: 0,
        SourceStatusEnum.IN_PROGRESS: 1,
        SourceStatusEnum.COMPLETED: 2,
    }

    def _score(s: Source) -> tuple[int, int]:
        return (
            stage_rank.get(s.current_stage, -1),
            status_rank.get(s.current_status, -1),
        )

    best_by_uri: dict[str, Source] = {}
    for src in sources:
        existing = best_by_uri.get(src.uri)
        if existing is None or _score(src) > _score(existing):
            best_by_uri[src.uri] = src

    # L'ordre est déterministe et suit le premier passage de chaque URI dans la liste fournie
    return list(best_by_uri.values())
