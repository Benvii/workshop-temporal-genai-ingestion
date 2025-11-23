import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from avelbot_ingestion.activities.index_source_no_chunk_activity import index_source_no_chunk_activity
from avelbot_ingestion.activities.print_source_activity import print_source_activity
from avelbot_ingestion.activities.scraping_activity import scraping_activity
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
    client: Client = await Client.connect("localhost:7233", namespace="workshop-ingestion")
    worker: Worker = Worker(
        client,
        task_queue="PY_WORKER_TASK_QUEUE", # Nom de la file sur laquelle écoute le worker
        workflows=[IngestionWorkflow], # Code des workflow qu'est capable d'exécuter le worker
        activities=[print_source_activity, index_source_no_chunk_activity, scraping_activity], # Liste des activités qu'est capable d'exécuter le worker
        debug_mode=True,
        workflow_runner=build_sandbox_worker_runner_vscode_debug_compatible() # Used to prevent VS Code issue
    )
    await worker.run()
    # COMPLETER ICI - END

if __name__ == "__main__":
    configure_logging(caller="main_worker") # Configurer un logger avec un peu de couleur
    asyncio.run(main())