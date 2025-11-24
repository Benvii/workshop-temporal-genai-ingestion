from typing import List
from pathlib import Path

from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.Source import Source
from pydantic import TypeAdapter

import yaml
import celpy


logger = get_app_logger(__name__)

@activity.defn(name="PY-fetch_sources_activity")
async def fetch_sources_activity(cel_expression: str, max_sources: int) -> List[Source]:
    """
    Activitée qui fetch des sources depuis la base de sources et les filtre avec une expression CEL.

    La base est un fichier YAML spécifique au workflow :
        temporal_workdir/<workflow_id>/sources_db.yaml

    :param cel_expression: Expression CEL (common-expression-language) appliquée à chaque source.
                           L'expression est évaluée avec une variable `source` contenant la
                           représentation sérialisée Pydantic (dict) de la source.
    :param max_sources: Le maximum de sources à retourner.
    :return: La liste des sources filtrées.
    """
    info = activity.info()
    workflow_id = info.workflow_id

    logger.info(
        " ---- fetch_sources_activity for workflow %s with CEL '%s' ----",
        workflow_id,
        cel_expression,
    )

    db_path = Path("temporal_workdir") / workflow_id / "sources_db.yaml"
    if not db_path.exists():
        logger.info("Sources DB not found at %s, returning empty list", db_path)
        return []

    # Chargement des sources existantes via Pydantic
    try:
        with db_path.open("r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or []
        adapter = TypeAdapter(List[Source])
        all_sources: List[Source] = adapter.validate_python(raw_data)
    except Exception:
        logger.exception("Failed to load sources from %s", db_path)
        raise

    # Si pas d'expression CEL, on renvoie tout
    if not cel_expression:
        logger.info(
            "No CEL expression provided, returning all %d sources", len(all_sources)
        )
        return all_sources

    # Compilation de l'expression CEL
    try:
        env = celpy.Environment()
        ast = env.compile(cel_expression)
        program = env.program(ast)
    except Exception:
        logger.exception("Failed to compile CEL expression: %s", cel_expression)
        raise

    filtered_sources: List[Source] = []

    for src in all_sources:
        # On travaille sur la forme dict sérialisée (Enum -> valeur, etc.)
        source_data = src.model_dump(mode="json")
        try:
            activation = {"source": celpy.json_to_cel(source_data)}
            result = program.evaluate(activation)
            if bool(result):
                filtered_sources.append(src)

                if len(filtered_sources) >= max_sources:
                    return filtered_sources
        except Exception as exc:
            logger.warning(
                "Error evaluating CEL expression on source '%s': %s",
                getattr(src, "uri", "<no-uri>"),
                exc,
            )

    logger.info(
        "CEL filtering kept %d sources out of %d",
        len(filtered_sources),
        len(all_sources),
    )

    return filtered_sources
