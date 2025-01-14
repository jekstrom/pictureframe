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

data "aws_iam_policy_document" "lambda_cloudfront" {
  statement {
    effect = "Allow"

    actions = [
      "cloudfront:CreateInvalidation"
    ]

    resources = [
        aws_cloudfront_distribution.s3_distribution.arn
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

resource "aws_iam_policy" "lambda_cloudfront" {
  name        = "lambda_cloudfront"
  path        = "/"
  description = "IAM policy for calling cloudfront from a lambda"
  policy      = data.aws_iam_policy_document.lambda_cloudfront.json
}

resource "aws_iam_role_policy_attachment" "lambda_cloudfront" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_cloudfront.arn
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
  cron_expression = "0 */${local.iteration_hours} * * ? *"
}

resource "aws_lambda_function" "image_gen_lambda" {
  filename      = "${path.module}/../lambda-packages.zip"
  function_name = "weather_image_gen"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "handler.lambda_handler"

  source_code_hash = filesha256("${path.module}/../lambda-packages.zip")

  runtime = "python3.12"
  timeout = 90
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
      CRON_EXPRESSION = local.cron_expression
      CLOUDFRONT_DISTRO_ID = aws_cloudfront_distribution.s3_distribution.id
    }
  }
}

resource "aws_cloudwatch_event_rule" "iteration_hours" {
  name        = "every_${local.iteration_hours}_hours_rule"
  description = "trigger lambda every ${local.iteration_hours} hours"

  schedule_expression = "cron(${local.cron_expression})"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.iteration_hours.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.image_gen_lambda.arn
  input     = "{\"location\":\"Bellevue WA\",\"latitude\":\"47.61\",\"longitude\":\"-122.2\",\"is_metric\":\"False\",\"timezone\":\"US/Pacific\"}"
}

resource "aws_cloudwatch_event_target" "lambda_target_casslake" {
  rule      = aws_cloudwatch_event_rule.iteration_hours.name
  target_id = "SendToLambdaCassLake"
  arn       = aws_lambda_function.image_gen_lambda.arn
  input     = "{\"location\":\"Cass Lake MN\",\"latitude\":\"47.40\",\"longitude\":\"-94.65\",\"is_metric\":\"False\",\"timezone\":\"US/Central\"}"
}

resource "aws_cloudwatch_event_target" "lambda_target_winona" {
  rule      = aws_cloudwatch_event_rule.iteration_hours.name
  target_id = "SendToLambdaWinona"
  arn       = aws_lambda_function.image_gen_lambda.arn
  input     = "{\"location\":\"Winona MN\",\"latitude\":\"44.05\",\"longitude\":\"-91.65\",\"is_metric\":\"False\",\"timezone\":\"US/Central\"}"
}

resource "aws_cloudwatch_event_target" "lambda_target_bemidji" {
  rule      = aws_cloudwatch_event_rule.iteration_hours.name
  target_id = "SendToLambdaBemidji"
  arn       = aws_lambda_function.image_gen_lambda.arn
  input     = "{\"location\":\"Bemidji MN\",\"latitude\":\"47.48\",\"longitude\":\"-94.88\",\"is_metric\":\"False\",\"timezone\":\"US/Central\"}"
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.image_gen_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.iteration_hours.arn
}