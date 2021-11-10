from typing import Any, Generic, TypeVar

T = TypeVar('T')


class Action(Generic[T]):
    def __init__(self, action_type: str, data: T):
        self.action_type = action_type
        self.data = data
