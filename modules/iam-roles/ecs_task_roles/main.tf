# modules/iam-roles/ecs_task_roles/main.tf

variable "name_prefix" { default = "ecs" }

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

output "execution" {
  value = aws_iam_role.execution.arn
}

output "iot_mqtt" {
  value = aws_iam_role.iot_mqtt.arn
}

output "task_role_arn" {
  value = aws_iam_role.iot_mqtt.arn
}

