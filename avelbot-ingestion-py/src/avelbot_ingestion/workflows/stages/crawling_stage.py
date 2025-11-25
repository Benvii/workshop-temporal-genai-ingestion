import os
import asyncio
from datetime import timedelta
from typing import List

from temporalio import workflow

from avelbot_ingestion.helpers.deduplicate_sources import deduplicate_sources
from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.Source import Source
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from avelbot_ingestion.activities.crawling_activity import crawling_activity

logger = get_app_logger(__name__)

WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT= int(os.getenv("WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT", 300)) # Default 300s, 5min

async def crawling_stage(sources: List[Source]) -> List[Source]:
    """
    Run web crawling activity.

    :param sources: List of sources to be chunked.
    """

    # Ensure only sources without status and stage, meaning initial ones are crawled
    sources_to_be_crawled = list(
        filter(lambda source: source.current_stage == None and source.current_status == None, sources))
    crawled_sources_completed = list(
        filter(lambda source: not(source.current_stage == None and source.current_status == None), sources))

    # A améliorer, ajouter de la deduplication
    while len(sources_to_be_crawled) > 0:
        crawling_tasks = [
            workflow.execute_activity(
                activity=crawling_activity,
                task_queue="PY_WORKER_TASK_QUEUE",
                args=[source, None],
                start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
            )
            for source in sources_to_be_crawled
        ]
        crawled_sources_lists = await asyncio.gather(*crawling_tasks)
        crawled_sources_result = [src for sublist in crawled_sources_lists for src in sublist]

        sources_to_be_crawled = list(
            filter(lambda source: source.current_status == SourceStatusEnum.DISCOVERED, crawled_sources_result))
        crawled_sources_completed.extend(
            list(filter(lambda source: source.current_status == SourceStatusEnum.COMPLETED, crawled_sources_result)))

        logger.debug("sources_to_be_crawled (DISCOVERED): %i sources.", len(sources_to_be_crawled))
        logger.debug("crawled_sources_completed (COMPLETED): %i sources.", len(crawled_sources_completed))

    return crawled_sources_completed