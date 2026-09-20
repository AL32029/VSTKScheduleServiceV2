import asyncio
import logging
from collections.abc import Iterable
from itertools import chain
from pathlib import Path

from watchfiles import awatch
from watchfiles._rust_notify import WatchfilesRustInternalError

from .item_models import WatchFilesItem

logger = logging.getLogger(__name__)


class WatchFilesManager:
    async def watch(self, settings_path: Iterable[WatchFilesItem]):
        logger.info("Launching tracking of changes in secrets")
        all_paths = set(chain.from_iterable(x.path_list for x in settings_path))
        watch_dirs = {str(Path(p).parent) for p in all_paths}

        retry_delay = 1
        max_delay = 60

        while True:
            if asyncio.current_task().cancelled():
                logger.info("Watch task cancelled before restart")
                break

            try:
                await self._watch_once(watch_dirs, all_paths, settings_path)
                retry_delay = 1
            except asyncio.CancelledError:
                logger.info("Watch task cancelled, exiting")
                break
            except (
                    WatchfilesRustInternalError,
                    PermissionError,
                    OSError,
                    RuntimeError,
            ):
                logger.exception("Watch error, restarting in %ss", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            except Exception:
                logger.exception("Unexpected error, restarting in %ss", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

        logger.info("Tracking of changes in secrets has been discontinued")

    async def _watch_once(
            self,
            watch_dirs: set[str],
            all_paths: set[str],
            settings_path: Iterable[WatchFilesItem],
    ) -> None:
        async for changes in awatch(
                *watch_dirs,
                watch_filter=lambda change, path: path in all_paths,  # noqa: ARG005
                debounce=2000,
        ):
            if asyncio.current_task().cancelled():
                logger.info("Watch task cancelled during event processing")
                return

            logger.info("Changes have been detected in the tracked secrets")
            certs_changes = {p for _, p in changes}

            tasks_run = []
            for item in settings_path:
                if item.path_list & certs_changes:
                    logger.info("Initializing the rotation for item %s", item.name)
                    tasks_run.append(asyncio.create_task(item.rotation_action()))

            await asyncio.gather(*tasks_run, return_exceptions=True)

        logger.warning("Watch loop exited unexpectedly, restarting")
