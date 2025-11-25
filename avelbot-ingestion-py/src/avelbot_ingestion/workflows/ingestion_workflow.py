import asyncio
import logging
import os
from datetime import timedelta
from typing import List

from temporalio import workflow

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.IngestionWorkflowInput import IngestionWorkflowInput
from avelbot_ingestion.models.Source import Source
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum
from avelbot_ingestion.workflows.stages.crawling_stage import crawling_stage
from avelbot_ingestion.workflows.stages.recursive_text_chunking_stage import recursive_text_chunking_stage
from avelbot_ingestion.workflows.utils import split_sources_by_error

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from avelbot_ingestion.activities.index_source_no_chunk_activity import index_source_no_chunk_activity
    from avelbot_ingestion.activities.index_source_with_chunks_activity import index_source_with_chunks_activity

logger = get_app_logger(__name__)

WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT= int(os.getenv("WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT", 300)) # Default 300s, 5min

@workflow.defn(name="IngestionWorkflow")
class IngestionWorkflow:
    @workflow.run
    async def run(self, ingestion_workflow_input: IngestionWorkflowInput) -> str:

        logging.info("IngestionWorkflow started.")
        sources = ingestion_workflow_input.sources
        total_sources = len(sources)
        sources_with_errors : List[Source] = [] # Contiendra les sources en erreur.

        # Part 4.b - Crawling simplified - START
        sources = await crawling_stage(sources)
        sources, err_sources = split_sources_by_error(sources)
        sources_with_errors.extend(err_sources)
        # Part 4.b - Crawling simplified - END


        # -- Démarrage d'un pool d'activitées en parallèle sur toutes les sources --
        printing_tasks = [
            workflow.execute_activity(
                activity="PY-print_source_activity",
                task_queue="PY_WORKER_TASK_QUEUE",
                args=[source],
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in sources
        ]
        # Exécute toutes les tâches en parallèle sur chaques sources
        # Sépare les sources ayant une erreur pour les sortie de la suite des exécutions
        sources, err_sources = split_sources_by_error(await asyncio.gather(*printing_tasks))
        sources_with_errors.extend(err_sources)


        # COMPLETER ICI - START (partie 4.a)
        scraping_tasks = [
            workflow.execute_activity(
                activity="PY-scraping_activity",
                task_queue="PY_WORKER_TASK_QUEUE",
                args=[source],
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in sources
        ]
        sources, err_sources = split_sources_by_error(await asyncio.gather(*scraping_tasks))
        sources_with_errors.extend(err_sources)
        # COMPLETER ICI - END (partie 4.a)


        # COMPLETER ICI - START (partie 3)
        # - appeler l'activité "TS_CONVERSION_HTML"
        conversion_tasks = [
            workflow.execute_activity(
                activity="TS_CONVERSION_HTML",
                task_queue="TS_WORKER_TASK_QUEUE",
                args=[source],
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in sources
        ]
        sources, err_sources = split_sources_by_error(await asyncio.gather(*conversion_tasks))
        sources_with_errors.extend(err_sources)
        # COMPLETER ICI - END

        # COMPLETER ICI - START (partie 5)
        # Décommenter les lignes suivante
        sources = await recursive_text_chunking_stage(sources, ingestion_workflow_input.recursive_chunking_config)
        sources, err_sources = split_sources_by_error(sources)
        sources_with_errors.extend(err_sources)
        # Penser à changer l'activité d'indexing "index_source_no_chunk_activity" par "index_source_with_chunks_activity"
        # COMPLETER ICI - END (partie 5)

        # COMPLETER ICI / Décommenter ici - START (partie 2)
        # - Décommenter les lignes suivantes
        # - Compléter l'activitée index_source_no_chunk_activity
        indexing_tasks = [
            workflow.execute_activity(
                activity=index_source_with_chunks_activity,
                task_queue="PY_WORKER_TASK_QUEUE",
                args=[source, ingestion_workflow_input.indexing_config], # Ne pas oublier de passer le paramètre supplémentaire ici
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in sources
        ]
        sources = await asyncio.gather(*indexing_tasks)  # Exécute toutes les tâches en parallèle sur chaques sources
        logger.info("Nombre de sources indexés : %i", len(sources))
        # COMPLETER ICI - END

        return f"Handeled {len(sources)} sources, sources with errors: {len(err_sources)}"
