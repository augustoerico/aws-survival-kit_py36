Feature: AWS API Gateway middleware 

Scenario: event with valid JSON payload

    Given an APIGW event object with a valid JSON payload
    And a JSON parser
    
    When the middleware is invoked
    
    Then the resulting event object contains the parsed JSON
