from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.IndexingStageConfiguration import IndexingStageConfiguration
from avelbot_ingestion.models.Source import Source

from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

logger = get_app_logger(__name__)

@activity.defn(name="PY-index_source_no_chunk_activity")
async def index_source_no_chunk_activity(source: Source, stage_config: IndexingStageConfiguration) -> Source:
    """
    Activitée d'indexation d'une source non chunkée en base vectorielle.

    :param source: Source non chunkée à indexer en base vectorielle.
    """
    logger.info("Indexation de la source : %s", source.uri)

    # COMPLETER ICI - START
    # embedding = # Créer l'embedding
    # vector_store = # Créer le vector store
    # Lire le contenu de la page téléchargée présente à source.raw_file_path
    # Créer un Document (langchain) :
    # - avec le contenu comme page_content
    # - en metadata "source" qui vaut source.uri
    # En utilisant le vector_store ajouter le document créé.
    # COMPLETER ICI - END

    return  source
