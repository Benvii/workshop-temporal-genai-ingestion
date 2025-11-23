import asyncio
import logging
import os
from datetime import timedelta
from typing import List

from temporalio import workflow

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.IngestionWorkflowInput import IngestionWorkflowInput
from avelbot_ingestion.models.Source import Source
from avelbot_ingestion.workflows.utils import split_sources_by_error

logger = get_app_logger(__name__)

WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT= int(os.getenv("WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT", 300)) # Default 300s, 5min

@workflow.defn(name="IngestionWorkflow")
class IngestionWorkflow:
    @workflow.run
    async def run(self, ingestion_workflow_input: IngestionWorkflowInput) -> str:

        logging.info("IngestionWorkflow started.")
        sources = ingestion_workflow_input.sources
        sources_with_errors : List[Source] = [] # Contiendra les sources en erreur.

        # -- Démarrage d'un pool d'activitées en parallèle sur toutes les sources --
        printing_tasks = [
            # NE PAS AWAIT ICI
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

        # COMPLETER ICI / Décommenter ici - START (partie 2)
        # - Décommenter les lignes suivantes
        # - Compléter l'activitée index_source_no_chunk_activity
        indexing_tasks = [
            workflow.execute_activity(
                activity="PY-index_source_no_chunk_activity",
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
