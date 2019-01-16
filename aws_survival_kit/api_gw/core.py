from functools import wraps, partial
from typing import Callable, Any, Tuple

import simplejson as json

ExceptionHandler = Callable[[Exception], dict]
LambdaHandler = Callable[[dict, Any], dict]

PayloadParser = Tuple[
    Callable[
        [str, dict, Any],
        Any
    ],
    ExceptionHandler
]

exception_messages = {
    "invalid_return_type":
        "LambdaHandlerResponseError: invalid return type; `lambda_handler` must return a `dict` instance",
    "invalid_headers":
        "LambdaHandlerResponseError: invalid `headers`",
    "invalid_status_code":
        "LambdaHandlerResponseError: invalid `statusCode`",
    "invalid_body":
        "LambdaHandlerResponseError: invalid `body`"
}


def decorator(
        lambda_handler: LambdaHandler,
        payload_parser: PayloadParser
):
    @wraps(lambda_handler)
    def wrapper(event_: dict, context: Any):

        try:

            if not isinstance(event_, dict):
                raise Exception('`event` must be a dictionary')

            auth_context = (event_.get('requestContext') or {}).get('authorizer')

            if not payload_parser or not payload_parser[0]:
                response = lambda_handler(event_, context)

            else:
                try:
                    mw_body = payload_parser[0](
                        event_.get('body'),
                        event_.get('headers'),
                        auth_context
                    )

                except Exception as e:
                    if payload_parser[1]:
                        response = payload_parser[1](e)
                    else:
                        raise e

                else:
                    event_ = {
                        **event_,
                        "middleware": {"body": mw_body}
                    }
                    response = lambda_handler(event_, context)

            if not isinstance(response, dict):
                raise Exception(exception_messages['invalid_return_type'])

        except Exception as e:
            response = {
                "statusCode": 500,
                "body": {
                    "errors": [
                        {"message": str(e)}
                    ],
                    "lambda_handler": {
                        "event": event_
                    }
                }
            }

        return to_api_gw_response(response)

    return wrapper


def middleware(
        payload_parser: PayloadParser = None
):
    return partial(decorator, payload_parser=payload_parser)


def to_api_gw_response(response: dict):
    errors = []
    status_code = 502
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": True
    }
    body = None

    if response:
        status_code = response.get('statusCode')
        if not (status_code and isinstance(status_code, int)):
            errors = [*errors, {"message": exception_messages['invalid_status_code']}]

        if response.get('headers'):
            if isinstance(response['headers'], dict):
                headers = {
                    **headers,
                    **response['headers']   # response headers can overwrite defaults
                }
            else:
                errors = [*errors, {"message": exception_messages['invalid_headers']}]

        body = response.get('body')
        if body and isinstance(body, dict):
            try:
                body = json.dumps(body)
            except TypeError:
                errors = [*errors, {"message": exception_messages['invalid_body']}]

    else:
        errors = [{"message": "Malformed lambda response"}]

    if errors:
        body = json.dumps({"errors": errors})

    api_response = {
        "statusCode": status_code,
        "headers": headers
    }
    if body:
        response = {
            **api_response,
            "body": body
        }

    return response
