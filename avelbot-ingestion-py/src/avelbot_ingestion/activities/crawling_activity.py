from typing import List

from temporalio import activity

from avelbot_ingestion.helpers.logging_config import get_app_logger
from avelbot_ingestion.models.SourceStatusEnum import SourceStatusEnum
from avelbot_ingestion.models.MimeTypesEnum import MimeTypesEnum
from avelbot_ingestion.models.Source import Source

import requests

from avelbot_ingestion.models.StageEnum import StageEnum

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urldefrag

logger = get_app_logger(__name__)

@activity.defn(name="PY-crawling_activity")
async def crawling_activity(source: Source, page_size: int) -> List[Source]:
    """
    Crawl une source / page web de manière paginée.

    :param source: Source à télécharger.
    :param page_size: Nombre de sources max à retourner en plus de la source en cours d'exploration.
    """
    logger.info(" ---- crawling_activity for %s ----", source.uri)

    sources = [source]

    try:
        response = requests.get(source.uri, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        source.error = str(e)
        source.current_status = SourceStatusEnum.ERROR
        source.current_stage = StageEnum.CRAWLING
        return sources

    # -- Always determine mime type --
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        source.mime_type = MimeTypesEnum.text_html
    else:
        source.error = f"Unsupported mime type: {content_type}"
        source.current_status = SourceStatusEnum.ERROR
        source.current_stage = StageEnum.CRAWLING
        return sources

    # -- Check if we crawl links or not --
    if source.max_depth is not None and source.max_depth <= 0:
        source.current_status = SourceStatusEnum.COMPLETED
        source.current_stage = StageEnum.CRAWLING
        return sources

    soup = BeautifulSoup(response.text, "html.parser")

    # Optional crawling prefix filters: list of URL startswith patterns
    crawling_prefixes = source.options.crawling_url_startswith if (source.options
                                                                   and source.options.crawling_url_startswith
                                                                   and len(source.options.crawling_url_startswith) > 0) else None

    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue

        full_url = urljoin(source.uri, href)
        full_url, _ = urldefrag(full_url) # Remove URL fragments url#quelqueschose

        # If prefixes are configured, keep only URLs starting with at least one of them
        if crawling_prefixes and not any(full_url.startswith(p) for p in crawling_prefixes):
            continue

        links.append(full_url)

    # Deduplicate links while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    if source.metadata is None:
        source.metadata = {}

    offset = int(source.metadata.get("crawling_page_last_link_index", 0))

    if not unique_links or offset >= len(unique_links):
        source.current_status = SourceStatusEnum.COMPLETED
        source.current_stage = StageEnum.CRAWLING
        return sources

    page_links = unique_links[offset : offset + page_size]

    for link in page_links:
        new_source = Source(
            uri=link,
            current_status=SourceStatusEnum.DISCOVERED,
            current_stage=StageEnum.CRAWLING,
            max_depth=source.max_depth - 1 if source.max_depth is not None else None,
            options=source.options,
        )
        sources.append(new_source)

    new_offset = offset + len(page_links)

    if new_offset >= len(unique_links):
        if "crawling_page_last_link_index" in source.metadata:
            del source.metadata["crawling_page_last_link_index"]
        source.current_status = SourceStatusEnum.COMPLETED
    else:
        source.metadata["crawling_page_last_link_index"] = new_offset
        source.current_status = SourceStatusEnum.IN_PROGRESS

    source.current_stage = StageEnum.CRAWLING

    return sources