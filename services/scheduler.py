from typing import Optional, Callable

import rx

from models.communication import Action
import rx.operators as ops


def init_scheduler(get_metadata: Callable[[], Action], interval=1) -> rx.Observable:
    return rx.interval(interval).pipe(
        ops.map(lambda i: get_metadata()),
    )
