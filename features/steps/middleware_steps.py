import simplejson as json
from behave import given, then, when

valid_json_payload = {
    "a_string": "value1",
    "an_integer": 123,
    "a_float": 4.56,
    "a_boolean": True,
    "null": None,
    "a_list": [
        1, "a", False
    ],
    "an_object": {
        "another_string": "value2"
    }
}


@given('an APIGW event object with a valid JSON payload')
def given_api_gw_event_with_valid_json(context):
    context.event = {
        "body": json.dumps(valid_json_payload)
    }


@given('a JSON parser')
def given_json_parser(context):
    context.payload_parser = json.loads


@when('the middleware is invoked')
def invoke_middleware(context):
    from aws_survival_kit.api_gw import middleware

    optional_args = {}
    if context.payload_parser:
        optional_args = {
            **optional_args,
            "payload_parser": context.payload_parser
        }

    if optional_args:
        event_, _ = middleware(context.event, None, **optional_args)
    else:
        event_, _ = middleware(context.event, None)
    context.event = event_


@then('the resulting event object contains the parsed JSON')
def event_contains_parsed_json(context):
    assert context.event['middleware']['body'] == valid_json_payload
