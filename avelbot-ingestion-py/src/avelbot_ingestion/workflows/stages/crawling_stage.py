import os
import asyncio
from datetime import timedelta
from typing import List

from temporalio import workflow

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

    sources_to_be_crawled = sources
    crawled_sources_completed = []
    crawling_tasks = [
        workflow.execute_activity(
            activity=crawling_activity,
            task_queue="PY_WORKER_TASK_QUEUE",
            args=[source, 1],
            start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
        )
        for source in sources_to_be_crawled
    ]
    crawled_sources_lists = await asyncio.gather(*crawling_tasks)
    crawled_sources_result = [src for sublist in crawled_sources_lists for src in sublist]
    # La on a la source principal complètement crawlée en completed
    # Mais il reste les sources filles dont on dont on doit déterminer si elles sont bien des pages web
    # Elles auront un max_depth de 0, on peut rappeler crawling task dessus.
    sources_to_be_crawled = list(filter(lambda source: source.current_status == SourceStatusEnum.DISCOVERED , crawled_sources_result))
    logger.debug("sources_to_be_crawled (DISCOVERED): %i sources.", len(sources_to_be_crawled))
    crawled_sources_completed.extend(list(filter(lambda source: source.current_status == SourceStatusEnum.COMPLETED, crawled_sources_result)))
    logger.debug("crawled_sources_completed: %i sources.", len(crawled_sources_completed))

    logger.debug("Type sources_to_be_crawled[0] : %s", type(sources_to_be_crawled[0]))
    crawling_tasks = [workflow.execute_activity(
        activity=crawling_activity,
        task_queue="PY_WORKER_TASK_QUEUE",
        args=[source],  # sans page_size
        start_to_close_timeout=timedelta(seconds=WORKFLOW_ACTIVITY_START_TO_CLOSE_TIMEOUT),
    ) for source in sources_to_be_crawled]
    crawled_sources_lists = await asyncio.gather(*crawling_tasks)
    crawled_sources_result = [src for sublist in crawled_sources_lists for src in sublist]
    sources_to_be_crawled = list(
        filter(lambda source: source.current_status == SourceStatusEnum.DISCOVERED, crawled_sources_result))
    logger.debug("sources_to_be_crawled: %i sources.", len(sources_to_be_crawled))
    crawled_sources_completed.extend(
        list(filter(lambda source: source.current_status == SourceStatusEnum.COMPLETED, crawled_sources_result)))
    logger.debug("crawled_sources_completed: %i sources.", len(crawled_sources_completed))

    return sources