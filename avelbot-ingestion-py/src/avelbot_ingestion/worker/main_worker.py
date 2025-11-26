import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from avelbot_ingestion.activities.crawling_activity import crawling_activity
from avelbot_ingestion.activities.fetch_sources_activity import fetch_sources_activity
from avelbot_ingestion.activities.index_source_no_chunk_activity import index_source_no_chunk_activity
from avelbot_ingestion.activities.index_source_with_chunks_activity import index_source_with_chunks_activity
from avelbot_ingestion.activities.print_source_activity import print_source_activity
from avelbot_ingestion.activities.recursive_text_chunking_source_activity import recursive_text_chunking_source_activity
from avelbot_ingestion.activities.save_sources_activity import save_sources_activity
# from avelbot_ingestion.activities.scraping_activity import scraping_activity
from avelbot_ingestion.helpers.logging_config import get_app_logger, configure_logging
from avelbot_ingestion.worker.utils import build_sandbox_worker_runner_vscode_debug_compatible
from avelbot_ingestion.workflows.ingestion_workflow import IngestionWorkflow

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = get_app_logger(__name__)

async def main() -> None:
    logger.info("Starting main python worker ...")

    # COMPLETER ICI - START
    # - Initialiser le client temporal
    # - Créer le Worker
    # - Démarrer le worker
    # COMPLETER ICI - END

if __name__ == "__main__":
    configure_logging(caller="main_worker") # Configurer un logger avec un peu de couleur
    asyncio.run(main())