# Python gRPC Task Event Logger Server

This directory contains the Python gRPC server (`task_event_logger.py`) that listens for task events from the Nextflow `nf-bioworkflowml-logger` plugin.

## Purpose

The `task_event_logger.py` script implements a gRPC service (`TaskEventLoggerService`) that:
- Receives `TaskObservation` messages from the Nextflow plugin.
- Logs the details of each received event (event ID, event type).
- Prints "start" to standard output if the `event_type` is "task_start".
- Prints "done" to standard output if the `event_type` includes "complete", "succeeded", or "failed".
- Returns an `Action` message to the gRPC client (the Nextflow plugin).

This server is primarily used for demonstrating and debugging the flow of task events from Nextflow to an external system via gRPC.

## Prerequisites

Before running the server, ensure you have the following Python packages installed:
- `grpcio`
- `grpcio-tools`

You can install them using pip:
```bash
pip install grpcio grpcio-tools
```

Additionally, the generated Protobuf Python files (`nf_ai_comms_pb2.py`, `nf_ai_comms_pb2_grpc.py`) must be importable. These are located in the main `proto` directory of the repository.

## Running the Server

1.  **Set PYTHONPATH:**
    You need to add the repository's `proto` directory to your `PYTHONPATH` environment variable so that the server script can import the generated Protobuf modules. From the root of this repository, you can set it like this:

    ```bash
    export PYTHONPATH=$PYTHONPATH:$(pwd)/proto
    ```
    Replace `$(pwd)/proto` with the absolute path to the `proto` directory if you are not in the repository root.

2.  **Execute the script:**
    Once the prerequisites are met and `PYTHONPATH` is set, run the server using:

    ```bash
    python plugins/python_logger/task_event_logger.py
    ```

3.  **Server Endpoint:**
    By default, the server listens on:
    - Host: `localhost`
    - Port: `50052`

    This endpoint is configurable in the Nextflow plugin (`nf-bioworkflowml-logger`) via `nextflow.config`.

## Expected Output

When the server is running and receives events, you will see output similar to this in your console:

```
TaskEventLoggerService started on port 50052
Received event: id=..., type=task_start
start
Received event: id=..., type=task_complete
done
...
```
