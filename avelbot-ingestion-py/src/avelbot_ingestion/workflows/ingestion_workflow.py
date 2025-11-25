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
        # sources_to_be_crawled = sources
        # crawled_sources_completed = []
        # crawling_tasks = [
        #     # NE PAS AWAIT ICI
        #     workflow.execute_activity(
        #         activity="PY-crawling_activity",
        #         task_queue="PY_WORKER_TASK_QUEUE",
        #         args=[source, 1],
        #         start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        #     )
        #     for source in sources_to_be_crawled
        # ]
        # crawled_sources_lists = await asyncio.gather(*crawling_tasks)
        # crawled_sources_result = [src for sublist in crawled_sources_lists for src in sublist]
        # # La on a la source principal complètement crawlée en completed
        # # Mais il reste les sources filles dont on dont on doit déterminer si elles sont bien des pages web
        # # Elles auront un max_depth de 0, on peut rappeler crawling task dessus.
        # sources_to_be_crawled = list(filter(lambda source: source.current_status == SourceStatusEnum.DISCOVERED , crawled_sources_result))
        # logger.debug("sources_to_be_crawled (DISCOVERED): %i sources.", len(sources_to_be_crawled))
        # crawled_sources_completed.extend(list(filter(lambda source: source.current_status == SourceStatusEnum.COMPLETED, crawled_sources_result)))
        # logger.debug("crawled_sources_completed: %i sources.", len(crawled_sources_completed))
        #
        # crawling_tasks = [workflow.execute_activity(
        #     activity="PY-crawling_activity",
        #     task_queue="PY_WORKER_TASK_QUEUE",
        #     args=[source],  # sans page_size
        #     start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        # ) for source in sources_to_be_crawled]
        # crawled_sources_lists: List[List[Source]] = await asyncio.gather(*crawling_tasks)
        # crawled_sources_result = [src for sublist in crawled_sources_lists for src in sublist]
        # sources_to_be_crawled = list(
        #     filter(lambda source: source.current_status == SourceStatusEnum.DISCOVERED, crawled_sources_result))
        # logger.debug("sources_to_be_crawled: %i sources.", len(sources_to_be_crawled))
        # crawled_sources_completed.extend(
        #     list(filter(lambda source: source.current_status == SourceStatusEnum.COMPLETED, crawled_sources_result)))
        # logger.debug("crawled_sources_completed: %i sources.", len(crawled_sources_completed))

        # crawled_sources_lists_raw: list[list[dict]] = await asyncio.gather(*crawling_tasks)
        # crawled_sources_lists: list[list[Source]] = [
        #     [Source.model_validate(s) for s in sublist]
        #     for sublist in crawled_sources_lists_raw
        # ]

        # Part 4.b - Crawling simplified - END

        # Part 4.b - Crawling - START
        # total_sources = await workflow.execute_activity(
        #         activity="PY-save_sources_activity",
        #         task_queue="PY_WORKER_TASK_QUEUE",
        #         args=[sources],
        #         start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        # )
        # logging.debug("Saved initial total sources %i", total_sources)
        #
        # while total_sources < 10 and len(sources) > 0: # Limite max de source à 20
        #     crawling_tasks = [
        #         workflow.execute_activity(
        #             activity="PY-crawling_activity",
        #             task_queue="PY_WORKER_TASK_QUEUE",
        #             args=[source, 3], # page_size 3, c'est-à-dire qu'on pagine l'exécution à la création de 3 sources
        #             start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        #         )
        #         for source in sources
        #     ]
        #     results_task = await asyncio.gather(*crawling_tasks)
        #     sources_flat = [src for sublist in results_task for src in sublist]
        #     sources, err_sources = split_sources_by_error(sources_flat)
        #     sources_with_errors.extend(err_sources)
        #
        #     # Save new sources
        #     total_sources = await workflow.execute_activity(
        #         activity="PY-save_sources_activity",
        #         task_queue="PY_WORKER_TASK_QUEUE",
        #         args=[sources],
        #         start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        #     )
        #
        #     # Fetch sources to be crawled
        #     sources = await workflow.execute_activity( # TODO prioritise max_depth: 0, IN_PROGRESS
        #         activity="PY-fetch_sources_activity",
        #         task_queue="PY_WORKER_TASK_QUEUE",
        #         args=['source.current_stage == "CRAWLING" && (source.current_status == "DISCOVERED" || source.current_status == "IN_PROGRESS")', 5],
        #         start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        #     )
        #
        # sources = await workflow.execute_activity(
        #     activity="PY-fetch_sources_activity",
        #     task_queue="PY_WORKER_TASK_QUEUE",
        #     args=[
        #         'source.current_stage == "CRAWLING" && source.current_status == "COMPLETED"', # + IN_PROGRESS
        #         10], # Fetch Max of 10 sources
        #     start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        # )
        # Part 4.b - Crawling - END



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
