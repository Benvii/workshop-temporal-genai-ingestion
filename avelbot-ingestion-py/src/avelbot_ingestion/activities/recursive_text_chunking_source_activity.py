import os
from pathlib import Path
from typing import List

import yaml
from temporalio import activity

import aiofiles

from langchain_text_splitters import RecursiveCharacterTextSplitter

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.Chunk import Chunk
from avelbot_ingestion.models.RecursiveChunkingStageConfiguration import RecursiveChunkingStageConfiguration
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum
from avelbot_ingestion.models.Source import Source
from avelbot_ingestion.models.StageEnum import StageEnum

logger = get_app_logger(__name__)

async def save_chunks_yaml(chunks: List[Chunk], output_path: Path):
    """
    Saves chunks to a yaml file.

    :chunks: list of Chunk objects
    :output_path: chunk output file.
    """
    # Convertir en objets Python natifs
    data = [c.model_dump() for c in chunks]

    # Convertir en YAML (string)
    yaml_str = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        indent=2,
    )

    # Écriture asynchrone
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(yaml_str)

    logger.debug("Saved chunks to %s", output_path)

@activity.defn(name="PY-recursive_text_chunking_source_activity")
async def recursive_text_chunking_source_activity(source: Source, recursive_chunking_stage_config: RecursiveChunkingStageConfiguration) -> Source:
    """
    Activitée de chunking RecursiveCharacterTextSplitter qui produit le fichier yaml de chunk d'une source.

    :param source: Source avec l'état mis à jour et l'emplacement du fichier de chunk.
    """
    logger.info(" ---- Chunking source %s ----", source.uri)

    # Temporal Context & chunking working directory
    workflow_id = activity.info().workflow_id
    workflow_chunk_dir = Path("temporal_workdir") / workflow_id / "chunking"
    os.makedirs(workflow_chunk_dir, exist_ok=True)
    source_chunks_file_path = workflow_chunk_dir / Path(source.converted_md_path).with_suffix(".yaml").name


    # Guard, s'assure que le contenu converti en MD est disponible
    if source.converted_md_path is None:
        source.error = "converted_md_path is None, can't do chunking"
        source.current_stage = StageEnum.CHUNKING
        source.current_status = SourceStatusEnum.COMPLETED
        return source

    source_content = ""
    chunks: List[Chunk] = []

    # COMPLETER ICI - START (partie 5)
    # COMPLETER ICI - END (partie 5)

    # Update de l'état de la source
    source.current_stage = StageEnum.CHUNKING
    source.current_status = SourceStatusEnum.COMPLETED

    return  source
