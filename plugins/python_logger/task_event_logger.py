# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import grpc
from concurrent import futures
import time
import uuid

# The following import assumes that the 'proto' directory is in the PYTHONPATH.
# Add 'proto' directory to PYTHONPATH when running this script.
# e.g., export PYTHONPATH=$PYTHONPATH:/path/to/your/repo/proto
import nf_ai_comms_pb2
import nf_ai_comms_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class TaskEventLoggerService(nf_ai_comms_pb2_grpc.AiActionServiceServicer):
    """
    gRPC service that logs task events and prints "start" or "done"
    based on event types.
    """

    def SendTaskObservation(self, request, context):
        """
        Receives task observation events.
        Logs event details and prints "start" or "done" to stdout.
        Returns an Action response.
        """
        event_id = request.observation_event_id
        event_type = request.event_type
        print(f"Received event: id={event_id}, type={event_type}", flush=True)

        if event_type == "task_start":
            print("start", flush=True)
        elif any(keyword in event_type.lower() for keyword in ["complete", "succeeded", "failed"]):
            print("done", flush=True)

        return nf_ai_comms_pb2.Action(
            observation_event_id=event_id,
            action_id=str(uuid.uuid4()),
            success=True,
            # Additional fields like 'tool_name', 'tool_input', 'output'
            # can be set here if needed, but are not required by the current spec.
        )

def serve():
    """
    Starts the gRPC server and waits for termination.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    nf_ai_comms_pb2_grpc.add_AiActionServiceServicer_to_server(
        TaskEventLoggerService(), server
    )
    port = "50052"
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"TaskEventLoggerService started on port {port}", flush=True)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        print("TaskEventLoggerService stopping gracefully.", flush=True)
        server.stop(0)
        print("TaskEventLoggerService stopped.", flush=True)

if __name__ == "__main__":
    serve()
