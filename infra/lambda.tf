data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "lambda_logging" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }
}

data "aws_iam_policy_document" "lambda_s3" {
  statement {
    effect = "Allow"

    actions = [
      "s3:*Object"
    ]

    resources = [
        "${aws_s3_bucket.weatherbot_pictureframe_cache_bucket.arn}/*",
        "${aws_s3_bucket.weatherbot_pictureframe_bucket.arn}/*"
    ]
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_parameters" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:DescribeParameter*",
      "ssm:GetParameter*"
    ]

    resources = [
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${var.tomorrow_api_parameter}",
        "arn:aws:ssm:${var.region}:${data.aws_caller_identity.current.account_id}:parameter/${var.openai_api_parameter}"
    ]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"
  policy      = data.aws_iam_policy_document.lambda_logging.json
}

resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

resource "aws_iam_policy" "lambda_s3" {
  name        = "lambda_s3"
  path        = "/"
  description = "IAM policy for s3 from a lambda"
  policy      = data.aws_iam_policy_document.lambda_s3.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_s3.arn
}

resource "aws_iam_policy" "lambda_parameters" {
  name        = "lambda_parametrs"
  path        = "/"
  description = "IAM policy for parameters from a lambda"
  policy      = data.aws_iam_policy_document.lambda_parameters.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_parameters.arn
}

resource "aws_s3_bucket" "weatherbot_pictureframe_cache_bucket" {
  bucket = "${var.s3_bucket_name}-cache"

  tags = {
    Name        = "${var.s3_bucket_name}-cache"
    Environment = var.environment_name
  }
}

locals {
  iteration_hours = 6
}

resource "aws_lambda_function" "image_gen_lambda" {
  filename      = "${path.module}/../lambda-packages.zip"
  function_name = "weather_image_gen"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "handler.lambda_handler"

  source_code_hash = filesha256("${path.module}/../lambda-packages.zip")

  runtime = "python3.10"
  timeout = 40
  memory_size = 256

  environment {
    variables = {
      S3_CACHE_BUCKET = aws_s3_bucket.weatherbot_pictureframe_cache_bucket.id
      S3_IMAGE_BUCKET = aws_s3_bucket.weatherbot_pictureframe_bucket.id
      TOMORROW_API_PARAMETER = var.tomorrow_api_parameter
      OPENAI_API_PARAMETER = var.openai_api_parameter
      FONTCONFIG_PATH = "/var/task/fonts"
      HEADING_FONT_SIZE = 32
      SUBHEADING_FONT_SIZE = 28
      ITERATION_HOURS = local.iteration_hours
    }
  }
}

resource "aws_cloudwatch_event_rule" "iteration_hours" {
  name        = "every_${local.iteration_hours}_hours_rule"
  description = "trigger lambda every ${local.iteration_hours} hours"

  schedule_expression = "cron(0 */${local.iteration_hours} * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.iteration_hours.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.image_gen_lambda.arn
  input     = "{\"location\":\"Bellevue WA\",\"is_metric\":\"False\"}"
}


resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_gen_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.iteration_hours.arn
}