# COMPLETER ICI - START (partie 4)
import os
from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.helpers.url_helpers import url_to_file_name
from avelbot_ingestion.models.MimeTypesEnum import MimeTypesEnum
from avelbot_ingestion.models.Source import Source

import requests
from pathlib import Path

from avelbot_ingestion.models.StageEnum import StageEnum

logger = get_app_logger(__name__)

@activity.defn(name="PY-scraping_activity")
async def scraping_activity(source: Source) -> Source:
    """
    Activitée qui télécharge une page web.

    :param source: Source a télécharger.
    """
    logger.info(" ---- scraping_activity for %s ----", source.uri)

    if source.mime_type != MimeTypesEnum.text_html:
        source.error = "Not and HTML mime type, can't be scraped."
        return source

    source.current_stage = StageEnum.SCRAPING

    # Ensure output directory exists
    workflow_id = activity.info().workflow_id
    scraping_directory = Path("temporal_workdir") / workflow_id / "scraping"
    os.makedirs(scraping_directory, exist_ok=True)
    output_raw_file_path = Path(scraping_directory) / f"{url_to_file_name(source.uri)}.html"

    # Download page
    try:
        resp = requests.get(source.uri, timeout=10)
        resp.raise_for_status()

        output_raw_file_path.write_text(resp.text, encoding="utf-8")
        source.raw_file_path = str(output_raw_file_path)
    except Exception as e:
        source.error = f"Failed to download page: {e}"

    return  source

# COMPLETER ICI - END (partie 4)