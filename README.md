## About

AWS Survival Kit is a set of functions that simplifies common tasks, such as parsing events from different sources.

## Install with Pipenv

```bash
pipenv install -e git+https://github.com/augustoerico/aws-survival-kit#egg=aws_survival_kit
```

## Modules

### API Gateway Middleware

*For Lambda proxy configuration*

### SNS, SQS, S3...
TODO

### DynamoDB toolbox
TODO

## Examples

See tests

## Development

### Setup

```bash
pipenv install --dev
```

### Running tests

```bash
python -m behave
```

```bash
python -m pytest tests\
```
