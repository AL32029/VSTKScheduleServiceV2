from collections.abc import Callable, Coroutine, Iterable
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WatchFilesItem(BaseModel):
    name: str = Field("WatchFiles model item")

    path_list: Iterable[str]

    rotation_action: Callable[[], Coroutine[Any, Any, Any]]

    @field_validator("path_list", mode="after")
    @classmethod
    def validate_path_list(cls, v: Iterable[str]):
        if not v:
            raise ValueError("The list of paths to the tracked files is not specified")

        return set(v)
