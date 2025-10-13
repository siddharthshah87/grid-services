#modules/ecs-service-backend/main.tf
resource "aws_cloudwatch_log_group" "this" {
  name = "/ecs/${var.service_name}"
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.service_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name  = var.service_name
      image = var.image
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "DB_HOST"
          value = var.db_host
        },
        {
          name  = "DB_USER"
          value = var.db_user
        },
        {
          name  = "DB_PASSWORD"
          value = var.db_password
        },
        {
          name  = "DB_NAME"
          value = var.db_name
        },
        {
          name  = "MQTT_ENABLED"
          value = "true"
        },
        {
          name  = "MQTT_HOST"
          value = var.mqtt_host
        },
        {
          name  = "MQTT_PORT"
          value = "8883"
        },
        {
          name  = "MQTT_USE_TLS"
          value = "true"
        },
        {
          name  = "MQTT_CLIENT_ID"
          value = "backend-mqtt-consumer"
        }
      ]
      secrets = [
        {
          name      = "CA_CERT_PEM"
          valueFrom = var.ca_cert_secret_arn
        },
        {
          name      = "CLIENT_CERT_PEM"
          valueFrom = var.client_cert_secret_arn
        },
        {
          name      = "PRIVATE_KEY_PEM"
          valueFrom = var.private_key_secret_arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.service_name
        }
      }
    }
  ])
}

resource "aws_ecs_service" "this" {
  name            = var.service_name
  cluster         = var.cluster_id
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.security_group_id]
    assign_public_ip = var.assign_public_ip
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = var.service_name
    container_port   = var.container_port
  }

  depends_on = [aws_ecs_task_definition.this]
}
