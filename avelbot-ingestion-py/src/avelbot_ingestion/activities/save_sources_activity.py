import os
from typing import List
from pathlib import Path
from pydantic import TypeAdapter

from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum
from avelbot_ingestion.models.Source import Source

from avelbot_ingestion.models.StageEnum import StageEnum

import yaml

logger = get_app_logger(__name__)

def _deduplicate_sources(sources: List[Source]) -> List[Source]:
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

@activity.defn(name="PY-save_sources_activity")
async def save_sources_activity(sources_to_be_saved: List[Source]) -> int:
    """
    Sauvegarde et déduplique les sources dans la base YAML du workflow.

    - Charge les sources existantes depuis `temporal_workdir/<workflow_id>/sources_db.yaml`
    - Fusionne avec les `sources_to_be_saved`
    - Déduplique sur la base de l'URI en conservant la source la plus avancée
    - Persiste le résultat dans le fichier YAML

    :param sources_to_be_saved: Liste de sources à ajouter / mettre à jour.
    :return: Le nombre total de sources en base après déduplication.
    """
    info = activity.info()
    workflow_id = info.workflow_id
    logger.info(" ---- save_sources_activity for %i sources ----", len(sources_to_be_saved))

    sources: List[Source] = sources_to_be_saved

    # Sources database is a simple yaml file containing the list of sources located at : Path("temporal_workdir") / workflow_id / "sources_db.yaml"
    # Load existing sources add them to sources.
    workflow_directory = Path("temporal_workdir") / workflow_id
    db_path = workflow_directory / "sources_db.yaml"
    os.makedirs(workflow_directory, exist_ok=True)

    existing_sources: List[Source] = []
    if db_path.exists():
        try:
            with db_path.open("r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or []
            adapter = TypeAdapter(List[Source])
            existing_sources = adapter.validate_python(raw_data)
        except Exception:
            logger.exception("Failed to load existing sources from %s", db_path)

    # Add input sources to this
    sources.extend(existing_sources)

    # Deduplicate sources based on their uri, code this in a separate function
    # - keep sources that are at the most advanced :
    #     - primer factor - current_stage: StageEnum.INDEXING > StageEnum.CHUNKING > StageEnum.CONVERTION > StageEnum.SCRAPING > StageEnum.CRAWLING
    #     - second factor - courent_status: SourceStatusEnum.COMPLETED > SourceStatusEnum.IN_PROGRESS > SourceStatusEnum.DISCOVERED

    deduplicated_sources = _deduplicate_sources(sources)

    # Save all sources in Path("temporal_workdir") / workflow_id / "sources_db.yaml"
    # Sérialisation en dicts pour YAML via Pydantic (TypeAdapter)
    # On utilise `mode="json"` pour convertir les Enum et autres types non natifs
    adapter = TypeAdapter(List[Source])
    serializable_sources = adapter.dump_python(
        deduplicated_sources,
        mode="json",  # garantit uniquement des types natifs (str, int, float, bool, dict, list, None)
    )

    with db_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(serializable_sources, f, allow_unicode=True)

    logger.info("Saved %i sources after deduplication", len(deduplicated_sources))

    # Retourne le nombre total de sources persistées après déduplication
    return len(deduplicated_sources)