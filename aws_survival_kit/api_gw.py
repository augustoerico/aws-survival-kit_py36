from typing import Callable, Any

def middleware(
    event_: dict, context: Any = None,
    payload_parser: Callable[[str], Any] = None
) -> (dict, Any):
    if payload_parser:
        event_ = {
            **event_,
            "middleware": {
                "body": payload_parser(event_['body'])
            }
        }
    return event_, context
