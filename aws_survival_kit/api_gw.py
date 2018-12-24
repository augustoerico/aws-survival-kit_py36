from typing import Callable, Any, Tuple, Dict, Optional, Tuple
from functools import wraps, partial

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

            if not payload_parser:
                response = lambda_handler(event_, context)
            
            elif payload_parser[0]:
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
                },
                "headers": {}  # TODO add those nice headers Web Browsers like
            }

        return to_api_gw_response(response)

    return wrapper


def middleware(
    payload_parser: PayloadParser = None
):
    return partial(decorator, payload_parser=payload_parser)


def to_api_gw_response(response: dict):

    errors = []

    if response:

        if not isinstance(response, dict):
            errors = [
                *errors, {"message": "LambdaHandlerResponseError: invalid return type; `lambda_handler` must return a `dict` instance"}]

        status_code = response.get('statusCode')
        if not (status_code and isinstance(status_code, int)):
            errors = [
                *errors, {"message": "LambdaHandlerResponseError: invalid `statusCode`"}]

        headers = response.get('headers')
        if headers and not isinstance(headers, dict):
            errors = [
                *errors, {"message": "LambdaHandlerResponseError: invalid `headers`"}]

        body = response.get('body')
        if body:
            if isinstance(body, dict):
                try:
                    response = {
                        **response,
                        "body": json.dumps(body)
                    }
                except TypeError:
                    errors = [
                        *errors, {"message": "LambdaHandlerResponseError: invalid `body`"}]

    else:
        errors = [*errors, {"message": "Malformed lambda response"}]

    if errors:

        if response.get('headers'):
            response = {
                "headers": response['headers']
            }
        else:
            response = {}

        response = {
            **response,
            "statusCode": 502,
            "body": json.dumps({"errors": errors}),
        }

    return response
