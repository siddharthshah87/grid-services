# modules/iam-roles/main.tf

variable "name" {}

resource "aws_iam_role" "execution" {
  name = "${var.name}-execution-role"

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

resource "aws_iam_role" "task" {
  name = "${var.name}-task-role"

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

# Optional: attach policies needed by the task, such as IoT Core publish permissions
resource "aws_iam_policy" "iot_publish" {
  name        = "${var.name}-iot-policy"
  description = "Allow publish to IoT topics"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "iot:Publish",
          "iot:Connect",
          "iot:Subscribe",
          "iot:Receive"
        ],
        Resource = "*" # You can scope to topic ARN for production
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_policy" {
  role       = aws_iam_role.task.name
  policy_arn = aws_iam_policy.iot_publish.arn
}

output "execution_role_arn" {
  value = aws_iam_role.execution.arn
}

output "task_role_arn" {
  value = aws_iam_role.task.arn
}

