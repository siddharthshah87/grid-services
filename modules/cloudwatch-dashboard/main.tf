resource "aws_cloudwatch_log_metric_filter" "vtn_event" {
  name           = "VTNEventCount"
  log_group_name = var.vtn_log_group
  pattern        = "Published OpenADR event"
  metric_transformation {
    name      = "VTNEventCount"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "vtn_registered" {
  name           = "VTNDeviceRegistered"
  log_group_name = var.vtn_log_group
  pattern        = "VEN registered"
  metric_transformation {
    name      = "VTNDeviceRegistered"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "vtn_unregistered" {
  name           = "VTNDeviceUnregistered"
  log_group_name = var.vtn_log_group
  pattern        = "VEN unregistered"
  metric_transformation {
    name      = "VTNDeviceUnregistered"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "vtn_error" {
  name           = "VTNError"
  log_group_name = var.vtn_log_group
  pattern        = "❌"
  metric_transformation {
    name      = "VTNError"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ven_status" {
  name           = "VENStatusUpdate"
  log_group_name = var.ven_log_group
  pattern        = "Published VEN status"
  metric_transformation {
    name      = "VENStatusUpdate"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ven_event" {
  name           = "VENEventReceived"
  log_group_name = var.ven_log_group
  pattern        = "Received event via MQTT"
  metric_transformation {
    name      = "VENEventReceived"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "ven_error" {
  name           = "VENError"
  log_group_name = var.ven_log_group
  pattern        = "❌"
  metric_transformation {
    name      = "VENError"
    namespace = var.namespace
    value     = "1"
  }
}

resource "aws_cloudwatch_dashboard" "this" {
  dashboard_name = var.dashboard_name
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            [var.namespace, "VENStatusUpdate"]
          ]
          stat   = "Sum"
          period = 300
          title  = "Device Status Updates"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            [var.namespace, "VTNEventCount"],
            [var.namespace, "VENEventReceived"]
          ]
          stat   = "Sum"
          period = 300
          title  = "Event Counts"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          metrics = [
            [var.namespace, "VTNError"],
            [var.namespace, "VENError"]
          ]
          stat   = "Sum"
          period = 300
          title  = "Error Rate"
        }
      }
    ]
  })
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.this.dashboard_name
}
