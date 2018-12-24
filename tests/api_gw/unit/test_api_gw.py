import simplejson as json

from aws_survival_kit.api_gw import middleware


def assert_common_conditions(response: dict) -> None:
    assert isinstance(response, dict)

    assert response.get('statusCode') and isinstance(response['statusCode'], int)

    if response.get('body'):
        assert isinstance(response['body'], str)

    assert not any(key not in ['statusCode', 'body', 'headers'] for key in response)


def test_middleware_should_not_cause_any_effect():
    # given
    @middleware()
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200
        }

    # when
    response = any_lambda_handler(None, None)

    # then
    assert_common_conditions(response)


def test_middleware_should_parse_dict_body_to_str():
    # given
    response_body = {
        "attr1": "value1",
        "attr2": 123,
        "attr3": 12.34
    }

    # and
    @middleware()
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200,
            "body": response_body
        }

    # when
    response = any_lambda_handler(dict(), None)

    # then
    assert_common_conditions(response)

    # and
    assert json.loads(response['body']) == response_body


def test_middleware_should_do_nothing_on_str_body():
    # given
    response_body = {
        "attr1": "value1",
        "attr2": 123,
        "attr3": 12.34
    }

    # and
    @middleware()
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200,
            "body": json.dumps(response_body)
        }

    # when
    response = any_lambda_handler(dict(), None)

    # then
    assert_common_conditions(response)

    # and
    assert json.loads(response['body']) == response_body


def test_middleware_should_handle_unhandled_exception_on_lambda_implementation():
    # given
    e_message = 'Unhandled exception'

    # and
    @middleware()
    def any_lambda_handler(_, __):
        raise Exception(e_message)

    # when
    response = any_lambda_handler(dict(), None)  # pylint: disable=E1111

    # then
    assert_common_conditions(response)
    assert response['statusCode'] == 500

    # and
    rsp_body = json.loads(response['body'])
    assert rsp_body.get('errors') and isinstance(rsp_body['errors'], list)
    assert any(
        e_message in e.get('message')
        for e in rsp_body['errors']
    )


# now with handlers ====================================================================================================

def test_middleware_should_parse_body_and_add_attr():
    # given
    def payload_parser(body: str, _, __):
        return {**json.loads(body), "attr0": "value0"}

    # and
    @middleware(
        payload_parser=(payload_parser, None)
    )
    def any_lambda_handler(event_, _):
        return {
            "statusCode": 200,
            "body": event_['middleware']['body']
        }

    # and
    event = {
        "body": json.dumps({"attr1": 1}),
        "requestContext": {
            "authorizer": {
                "attr1": "value1"
            }
        }
    }

    # when
    response = any_lambda_handler(event, None)

    # then
    assert_common_conditions(response)

    # and
    rsp_body = json.loads(response['body'])
    assert rsp_body == {"attr1": 1, "attr0": "value0"}


def test_middleware_should_handle_exception_on_payload_parser():
    # given
    def payload_parser(_, __, ___):
        raise Exception("Unhandled exception in parser")

    # and
    @middleware(
        payload_parser=(payload_parser, None)
    )
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200
        }

    # when
    response = any_lambda_handler(dict(), None)

    # then
    assert_common_conditions(response)
    assert response['statusCode'] == 500


def test_middleware_should_invoke_on_error_on_payload_parser_exception():
    # given
    def payload_parser(_, __, ___):
        raise Exception()

    def on_error(_):
        return {
            "statusCode": 202,
            "body": {
                "message": "Accepted"
            }
        }

    # and
    @middleware(
        payload_parser=(payload_parser, on_error)
    )
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200
        }

    # when
    response = any_lambda_handler(dict(), None)

    # then
    assert_common_conditions(response)
    assert response['statusCode'] == 202


# exception on error handler
def test_middleware_should_handle_exception_raised_on_payload_parser_error_handler():
    # given
    def payload_parser(_):
        raise Exception()

    def on_error(_):
        raise Exception('Unexpected error on auth error handler')

    # and
    @middleware(
        payload_parser=(payload_parser, on_error)
    )
    def any_lambda_handler(_, __):
        return {
            "statusCode": 200
        }

    # when
    response = any_lambda_handler(dict(), None)

    # then
    assert_common_conditions(response)
    assert response['statusCode'] == 500
