from typing import List

from temporalio import activity

import yaml
import aiofiles

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.Chunk import Chunk
from avelbot_ingestion.models.IndexingStageConfiguration import IndexingStageConfiguration
from avelbot_ingestion.models.Source import Source

from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

logger = get_app_logger(__name__)

async def load_chunks_yaml(filepath: str) -> List[Chunk]:
    # Lecture async du YAML
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()

    # Parse du YAML → Python (dict / list)
    raw_data = yaml.safe_load(content)

    if raw_data is None:
        logger.warning("File %s has no content / chunks", filepath)
        return []

    # Conversion : dict → Pydantic Chunk
    return [Chunk.model_validate(item) for item in raw_data]

@activity.defn(name="PY-index_source_with_chunks_activity")
async def index_source_with_chunks_activity(source: Source, stage_config: IndexingStageConfiguration) -> Source:
    """
    Activitée d'indexation d'une source non chunkée en base vectorielle.

    :param source: Source avec chunk file à indexer en base vectorielle.
    """
    logger.info("Indexation des chunks de la source: %s", source.uri)

    logger.debug("Creating OpenAI embedding using model : %s", stage_config.openai_embedding_model)
    embedding = OpenAIEmbeddings(model=stage_config.openai_embedding_model)
    vector_store = PGVector(
        connection=stage_config.database_uri,
        collection_name=stage_config.collection_name,
        embeddings=embedding,
    )

    chunks = await load_chunks_yaml(source.chunking_file_path)
    documents: List[Document] = []

    for chunk in chunks:
        doc = Document(
            page_content=chunk.text,
            metadata={
                **chunk.metadata,

                "source": source.uri,
                "title": source.metadata.get("title"),
            },
        )
        documents.append(doc)

    vector_store.add_documents(documents)

    return  source
