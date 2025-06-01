import grpc
import time # Keep if used, else optional
import asyncio
from concurrent import futures
import uuid
import os
import sys
import ray # Add ray back

# 1. sys.path modification block (ensure this is at the top)
# (Content as defined and confirmed in previous successful steps)
_current_script_path = os.path.abspath(__file__)
_ai_action_streamer_dir = os.path.dirname(_current_script_path)
_project_root_dir = os.path.dirname(_ai_action_streamer_dir)
if _project_root_dir not in sys.path:
    sys.path.insert(0, _project_root_dir)
_proto_dir = os.path.join(_project_root_dir, "proto")
if _proto_dir not in sys.path:
    sys.path.insert(1, _proto_dir)
print("__script__: sys.path configured.")

# 2. Protobuf imports
from proto import nf_ai_comms_pb2
from proto import nf_ai_comms_pb2_grpc
print("__script__: Protobuf imports loaded.")

# 3. AiActionServicer class (as defined and confirmed)
class AiActionServicer(nf_ai_comms_pb2_grpc.AiActionServiceServicer):
    async def SendTaskObservation(self, request: nf_ai_comms_pb2.TaskObservation, context):
        print(f"AiActionServicer: Received event_id: {request.event_id}")
        await asyncio.sleep(0.01)
        action_id = f"act_{uuid.uuid4()}"
        return nf_ai_comms_pb2.Action(
            observation_event_id=request.event_id,
            action_id=action_id,
            action_details="echo_via_ray_actor",
            success=True,
            message=f"Echoed {request.event_id}"
        )
print("__script__: AiActionServicer defined.")

# 4. AiActionStreamer Ray Actor class
@ray.remote
class AiActionStreamer:
    def __init__(self, host="[::]", port=50051):
        self.host = host
        self.port = port
        self.server = None
        # This print is in the actor's constructor, will appear on worker log
        print(f"AiActionStreamer Actor: Initialized. Target: {self.host}:{self.port}")

    async def start_server(self):
        # This print is in actor method, will appear on worker log
        print(f"AiActionStreamer Actor: start_server called on port {self.port}")
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        nf_ai_comms_pb2_grpc.add_AiActionServiceServicer_to_server(
            AiActionServicer(), self.server
        )
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        await self.server.start()
        print(f"AiActionStreamer Actor: gRPC server started on {self.host}:{self.port}")
        try:
            await self.server.wait_for_termination()
        except asyncio.CancelledError:
            print("AiActionStreamer Actor: start_server task cancelled, shutting down server.")
        except Exception as e:
            print(f"AiActionStreamer Actor: server.wait_for_termination() error: {e}")
        finally:
            await self.stop_server() # Ensure stop is called

    async def stop_server(self):
        if self.server:
            print("AiActionStreamer Actor: Stopping gRPC server...")
            await self.server.stop(grace=1.0)
            self.server = None
            print("AiActionStreamer Actor: gRPC server stopped.")
        else:
            print("AiActionStreamer Actor: stop_server called but server was not running.")

    def get_port(self): # Not async, as it just returns an attribute
        return self.port
print("__script__: AiActionStreamer (Ray actor) class defined.")

# 5. main_server_loop (for Ray)
async def main_server_loop():
    print("__main_server_loop__: Entered.")
    # Define project_root_dir and proto_module_path for runtime_env
    # These paths are for the context of where this script *runs*, not for the actor directly.
    # The actor gets these paths via Ray's packaging of py_modules.
    # (Re-define here for clarity, ensure paths are absolute for Ray context)
    script_abs_path = os.path.abspath(__file__)
    local_ai_action_streamer_dir = os.path.dirname(script_abs_path)
    local_project_root_dir = os.path.dirname(local_ai_action_streamer_dir)
    local_proto_module_path = os.path.join(local_project_root_dir, "proto")

    print(f"__main_server_loop__: project_root_dir for Ray runtime_env: {local_project_root_dir}")
    print(f"__main_server_loop__: proto_module_path for Ray runtime_env: {local_proto_module_path}")

    if not ray.is_initialized():
        print("__main_server_loop__: Initializing Ray...")
        try:
            ray.init(
                ignore_reinit_error=True,
                log_to_driver=True, # Let's see logs from driver
                runtime_env={"py_modules": [local_project_root_dir, local_proto_module_path]}
            )
            print("__main_server_loop__: Ray initialized.")
        except Exception as e:
            print(f"__main_server_loop__: Ray initialization failed: {e}")
            return

    broker_port = 50051
    actor_handle = None
    actor_name = "" # Define actor_name to be available in finally block
    try:
        print(f"__main_server_loop__: Attempting to create/get AiActionStreamer actor.")
        # Use a unique name to ensure fresh actor if script is re-run quickly
        actor_name = f"AiActionStreamerService_{uuid.uuid4().hex[:6]}"
        actor_handle = AiActionStreamer.options(name=actor_name, get_if_exists=False).remote(port=broker_port) # get_if_exists=False for unique name
        print(f"__main_server_loop__: AiActionStreamer actor {actor_name} created. Handle: {actor_handle}")

        print(f"__main_server_loop__: Calling start_server on actor {actor_name} (non-blocking).")
        # Start the server but don't wait for it here; it runs in the actor's process
        start_task = actor_handle.start_server.remote() # remote() call itself is non-blocking for async actor methods

        # Keep main alive to let actor run
        print(f"__main_server_loop__: Actor {actor_name} is running its server. Main loop will sleep. Check Ray logs for actor output.")
        # A very long sleep, KeyboardInterrupt is the main way to stop this loop.
        # Any exception in the actor's start_server might not propagate here directly unless explicitly handled by awaiting start_task.
        # For now, we assume start_server runs in background and we poll/check logs.
        await asyncio.sleep(3600) # Sleep for an hour, or until KeyboardInterrupt

    except KeyboardInterrupt:
        print("__main_server_loop__: KeyboardInterrupt received. Shutting down.")
    except Exception as e:
        print(f"__main_server_loop__: An error occurred: {e}")
    finally:
        print("__main_server_loop__: In finally block.")
        if actor_handle:
            print(f"__main_server_loop__: Ensuring AiActionStreamer actor {actor_name} server is stopped...")
            try:
                # Call stop_server, wait for it to complete.
                # Ray will kill the actor if this hangs for too long.
                await actor_handle.stop_server.remote() # await the task submitted by .remote()
                print(f"__main_server_loop__: stop_server on actor {actor_name} called and completed.")
            except Exception as e:
                print(f"__main_server_loop__: Error calling stop_server on actor: {e}")
            # Optionally, explicitly kill the actor if stop_server fails or is insufficient
            # print(f"__main_server_loop__: Attempting to kill actor {actor_name} forcefully.")
            # ray.kill(actor_handle)
            # print(f"__main_server_loop__: ray.kill({actor_name}) called.")

        if ray.is_initialized():
            print("__main_server_loop__: Shutting down Ray.")
            ray.shutdown()
            print("__main_server_loop__: Ray shut down.")
        print("__main_server_loop__: Exiting.")
print("__script__: main_server_loop defined.")

# 6. __main__ execution block
if __name__ == "__main__":
    print("__main__: Script started.")
    try:
        asyncio.run(main_server_loop())
    except KeyboardInterrupt:
        print("__main__: Main application KeyboardInterrupt. Exiting.")
    except Exception as e:
        print(f"__main__: Main application unexpected error: {e}")
        # For more detailed debugging of unexpected errors in __main__
        import traceback
        traceback.print_exc()
    finally:
        print("__main__: Application finished.")
print("__script__: End of script.")
