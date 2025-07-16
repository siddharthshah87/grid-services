# Terraform Modules

This directory contains reusable Terraform modules used by the environment under `../envs`.
Each module is self-contained and can be composed to create the complete infrastructure.
Refer to the main [README](../README.md) for an overview of how these modules are used.

New in this repository is `iot-rule-forwarder`, which creates an IoT Core topic
rule that forwards selected MQTT topics to both an S3 bucket and a Kinesis
stream for later processing.
