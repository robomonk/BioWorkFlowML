# BioWorkFlowML Task Logger Nextflow Plugin

This Nextflow plugin logs task start and completion events by sending them to a Python gRPC server.

## Functionality

- Implements `TraceObserverV2` to listen to Nextflow workflow events.
- On task submission/cache (considered as "start") and task completion, it sends a gRPC message to a configured Python server.
- The Python server (`task_event_logger.py`) is responsible for printing "start" or "done".

## Prerequisites

1.  The Python gRPC server (`task_event_logger.py` from the `plugins/python_logger` directory) must be running.
2.  The Nextflow environment must have access to the gRPC and protobuf Java libraries if you build this plugin from source. Typically, these would be declared as dependencies in a `build.gradle` file.

## Configuration

The plugin can be configured in your `nextflow.config` file to specify the host and port of the Python gRPC server:

```groovy
// In nextflow.config
plugins {
    // Assuming the plugin is published or available locally
    id 'com.yourorg.bioflowml.plugin.bioworkflowml-logger@0.1.0'
}

bioworkflowml_logger {
    host = 'localhost' // or the IP/hostname of your Python server
    port = 50052       // the port your Python server is listening on
}
```

If not specified, it defaults to `localhost:50052`.

## Building (Conceptual)

To build this plugin from source (outside the scope of this automated generation):
1.  You would need a `build.gradle` file.
2.  This `build.gradle` would need to include dependencies for:
    - `io.grpc:grpc-netty-shaded`
    - `io.grpc:grpc-protobuf`
    - `io.grpc:grpc-stub`
        - `com.google.protobuf:protobuf-java-util` (for Timestamps, etc., if used)
        - `com.google.guava:guava` (e.g., `com.google.guava:guava:32.1.3-jre` for ListenableFuture, Futures, MoreExecutors)
3.  It would also use the `com.google.protobuf` gradle plugin to generate Java classes from `nf_ai_comms.proto`. The `.proto` file would need to be placed in `src/main/proto/`.
4.  The Nextflow plugin development guidelines and the `nf-hello` example plugin are good resources.
