from typing import  Generic, TypeVar

T = TypeVar('T')


class Action(Generic[T]):
    def __init__(self, action_type: str, payload: T):
        self.action_type = action_type
        self.payload = payload
