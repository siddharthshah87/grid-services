# modules/iam-roles/ecs_task_roles/main.tf

variable "name_prefix" { default = "ecs" }
variable "tls_secret_arn" {}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "execution" {
  name = "${var.name_prefix}-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "execution_policy" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for IoT access (Task Role)
resource "aws_iam_role" "iot_mqtt" {
  name = "${var.name_prefix}-task-iot"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "iot_publish_policy" {
  name = "${var.name_prefix}-iot-policy"
  role = aws_iam_role.iot_mqtt.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "iot:Connect",
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "allow_tls_secret_access" {
  name = "${var.name_prefix}-ven-tls-secret-access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = var.tls_secret_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_tls_secret" {
  role       = aws_iam_role.iot_mqtt.name
  policy_arn = aws_iam_policy.allow_tls_secret_access.arn
}

output "execution" {
  value = aws_iam_role.execution.arn
}

output "iot_mqtt" {
  value = aws_iam_role.iot_mqtt.arn
}

output "task_role_arn" {
  value = aws_iam_role.iot_mqtt.arn
}

