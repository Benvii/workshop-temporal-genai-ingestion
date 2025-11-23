import logging

from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.Source import Source

logger = get_app_logger(__name__)

@activity.defn(name="PY-PRINT-SOURCE-ACTIVITY")
async def print_source_activity(source: Source):
    """
    Activitée d'exemple super basique qui affiche une source.

    :param source: Source à afficher.
    """
    logger.info(" ---- Printing source %s ----", source.uri)
    logger.info(" %r ", source)
