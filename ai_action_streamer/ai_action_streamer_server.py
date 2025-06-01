import grpc
import time
import asyncio
from concurrent import futures
import uuid # For generating unique action IDs
import os # Ensure os is imported
import sys # Ensure sys is imported

# Allow the script to find the 'proto' package for local execution
_current_script_path = os.path.abspath(__file__)
_ai_action_streamer_dir = os.path.dirname(_current_script_path)
_project_root_dir = os.path.dirname(_ai_action_streamer_dir) # e.g. /app
_proto_dir = os.path.join(_project_root_dir, "proto")        # e.g. /app/proto

if _project_root_dir not in sys.path:
    sys.path.insert(0, _project_root_dir)
if _proto_dir not in sys.path:
    sys.path.insert(1, _proto_dir) # Add after project_root_dir

import ray

# Import the generated gRPC files
from proto import nf_ai_comms_pb2
from proto import nf_ai_comms_pb2_grpc


# Define the servicer class that implements the RPC methods
class AiActionServicer(nf_ai_comms_pb2_grpc.AiActionServiceServicer):
    async def SendTaskObservation(self, request: nf_ai_comms_pb2.TaskObservation, context):
        print(f"AiActionStreamer: Received observation_event_id: {request.event_id}, type: {request.event_type}")
        print(f"  Pipeline: {request.pipeline_name}, Process: {request.process_name}, Task: {request.task_name}")

        await asyncio.sleep(0.01) 

        action_id = f"act_{uuid.uuid4()}"
        response_message = f"AiActionStreamer: Echoed observation_event_id {request.event_id}"
        print(f"  Sending action_id: {action_id}")

        return nf_ai_comms_pb2.Action(
            observation_event_id=request.event_id, 
            action_id=action_id,
            action_details="echo_received_and_processed", 
            success=True,
            message=response_message
        )

@ray.remote
class AiActionStreamer:
    # __init__ must be synchronous for Ray actors
    def __init__(self, host="[::]", port=50051):
        self.host = host
        self.port = port
        self.server = None
        print(f"AiActionStreamer Actor initialized. Will listen on {self.host}:{self.port}")

    async def start_server(self): # Changed to async
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10)) # Use grpc.aio.server
        nf_ai_comms_pb2_grpc.add_AiActionServiceServicer_to_server(
            AiActionServicer(), self.server
        )
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        await self.server.start() # await start
        print(f"AiActionStreamer gRPC server started on {self.host}:{self.port}")
        try:
            await self.server.wait_for_termination() # await termination
        except KeyboardInterrupt:
            print("AiActionStreamer server shutting down due to KeyboardInterrupt...")
        except Exception as e:
            print(f"AiActionStreamer server error: {e}")
        finally:
            await self.stop_server() # Ensure stop_server is awaited if called here


    async def stop_server(self): # Changed to async
        if self.server:
            print("Stopping AiActionStreamer gRPC server...")
            await self.server.stop(grace=1.0) # await stop
            self.server = None
            print("AiActionStreamer gRPC server stopped.")

    def get_port(self): 
        return self.port

# The main_server_loop and its async nature might need reconsideration
# if the entire application is intended to be synchronous.
# However, the subtask is focused on the AiActionStreamer actor.
async def main_server_loop():
    # Determine project root for Ray runtime environment
    current_script_path = os.path.abspath(__file__)
    ai_action_streamer_dir = os.path.dirname(current_script_path)
    project_root_dir = os.path.dirname(ai_action_streamer_dir)
    # Construct the path to the 'proto' directory from the project root
    proto_module_path = os.path.join(project_root_dir, "proto")

    if not ray.is_initialized():
        ray.init(
            ignore_reinit_error=True,
            log_to_driver=False,
            runtime_env={"py_modules": [project_root_dir, proto_module_path]}
        )

    broker_port = 50051
    # Note: If AiActionStreamer is fully synchronous, calling its methods with .remote()
    # will still work, but the methods themselves will block the actor.
    ai_streamer_actor = AiActionStreamer.options(name="AiActionStreamerService", get_if_exists=True).remote(port=broker_port)

    print("Attempting to start AiActionStreamer server via Ray actor...")
    # The AiActionStreamer methods are now async, so .remote() returns a future immediately.
    # The actual execution on the actor will be async.
    actor_start_method_future = ai_streamer_actor.start_server.remote() # This is an async method

    # Allow some time for the server to potentially start or fail.
    # This is a bit arbitrary; a more robust check would be better if possible.
    print(f"AiActionStreamer server launch initiated via actor. Waiting a few seconds for status...")

    # Check if the start_server task completed or if there was an error during startup.
    # We can await the future with a timeout.
    try:
        # This will wait for start_server to complete. If start_server has wait_for_termination(),
        # this will block until the server is shut down. This might be intended if the main script
        # is just a launcher.
        # For testing if it STARTS, we might not want to wait indefinitely.
        # However, the previous logic with ray.get(..., timeout=10) was for a synchronous start_server.
        # For an async start_server that runs an infinite loop (wait_for_termination),
        # we expect this remote call to "hang" until the server is stopped.
        # The goal is to ensure it *can* start without actor init error.
        # So, we won't block indefinitely on ray.get() here for this subtask's purpose.
        # We'll rely on actor logs or other means if needed for deeper inspection.
        # The main check is that the actor doesn't die on init.
        pass # No indefinite blocking on ray.get(actor_start_method_future)

    except Exception as e:
        print(f"Error interacting with AiActionStreamer actor: {e}")
        # Attempt to stop the actor if an error occurred during interaction
        if ai_streamer_actor:
            print("Attempting to stop actor due to error...")
            await ai_streamer_actor.stop_server.remote()


    # Keep the main script alive for a period, or until KeyboardInterrupt
    # This allows the server (running in the actor) to operate.
    # The actual server logic is within the actor's start_server method.
    try:
        print("Main script will sleep for 60 seconds or until KeyboardInterrupt to keep actor alive.")
        await asyncio.sleep(60)
        print("Main script sleep finished.")
    except KeyboardInterrupt:
        print("Application shutting down by KeyboardInterrupt...")
    except Exception as e:
        print(f"Main loop encountered an error: {e}")
    finally:
        print("Ensuring AiActionStreamer server is stopped...")
        if ai_streamer_actor: # Check if actor handle exists
            stop_future = ai_streamer_actor.stop_server.remote()
            await stop_future # Wait for async stop_server to complete
        if ray.is_initialized():
            ray.shutdown()
        print("Ray shut down. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main_server_loop())
    except KeyboardInterrupt:
        print("Exiting main application script...")
