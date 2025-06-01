import grpc
import uuid
import datetime

# Import the generated classes
# Assuming 'proto' directory is in PYTHONPATH or handled by the calling script.
import nf_ai_comms_pb2
import nf_ai_comms_pb2_grpc

def send_task_observation(observation_data, server_address='localhost:50052'):
    """
    Sends a TaskObservation to the AiActionService and returns the Action response.

    Args:
        observation_data (dict): A dictionary containing the data for the TaskObservation.
        server_address (str): The address (host:port) of the gRPC server.

    Returns:
        nf_ai_comms_pb2.Action: The Action message response from the server.
                                Returns None if an RPC error occurs.
    """
    channel = grpc.insecure_channel(server_address)
    stub = nf_ai_comms_pb2_grpc.AiActionServiceStub(channel)

    request = nf_ai_comms_pb2.TaskObservation()

    # Map dictionary data to protobuf message fields
    request.event_id = observation_data.get("event_id", str(uuid.uuid4()))
    request.event_type = observation_data.get("event_type", "")
    request.timestamp_iso = observation_data.get("timestamp_iso", datetime.datetime.utcnow().isoformat() + "Z")
    request.pipeline_name = observation_data.get("pipeline_name", "")
    request.process_name = observation_data.get("process_name", "")

    # Ensure numeric fields are correctly typed, providing defaults or handling missing values
    task_id_num_str = observation_data.get("task_id_num")
    if task_id_num_str is not None:
        try:
            request.task_id_num = int(task_id_num_str)
        except ValueError:
            print(f"Warning: Could not convert task_id_num '{task_id_num_str}' to int. Using default 0.")
            request.task_id_num = 0 # Default or error handling
    else:
        request.task_id_num = 0 # Default if not provided

    request.task_hash = observation_data.get("task_hash", "")
    request.task_name = observation_data.get("task_name", "")
    request.native_id = observation_data.get("native_id", "")
    request.status = observation_data.get("status", "")

    # Optional fields (example: exit_code, duration_ms)
    # Check if they exist in observation_data and set them if they do
    if "exit_code" in observation_data:
        try:
            request.exit_code = int(observation_data["exit_code"])
        except ValueError:
            print(f"Warning: Could not convert exit_code '{observation_data['exit_code']}' to int.")
            # Decide on default or leave unset if appropriate for your proto definition

    if "duration_ms" in observation_data:
        try:
            request.duration_ms = int(observation_data["duration_ms"])
        except ValueError:
            print(f"Warning: Could not convert duration_ms '{observation_data['duration_ms']}' to int.")

    if "peak_rss_bytes" in observation_data:
        try:
            request.peak_rss_bytes = int(observation_data["peak_rss_bytes"])
        except ValueError:
             print(f"Warning: Could not convert peak_rss_bytes '{observation_data['peak_rss_bytes']}' to int.")

    if "cpu_time_seconds" in observation_data:
        try:
            request.cpu_time_seconds = float(observation_data["cpu_time_seconds"])
        except ValueError:
            print(f"Warning: Could not convert cpu_time_seconds '{observation_data['cpu_time_seconds']}' to float.")

    # Add more optional fields as needed from your .proto definition
    # request.error_message = observation_data.get("error_message", "")
    # request.work_dir = observation_data.get("work_dir", "")
    # request.container_id = observation_data.get("container_id", "")
    # request.container_engine = observation_data.get("container_engine", "")
    # request.script_id = observation_data.get("script_id", "")
    # request.script_hash = observation_data.get("script_hash", "")

    print(f"Sending TaskObservation (event_id={request.event_id}, event_type='{request.event_type}') to {server_address}...")

    try:
        action_response = stub.SendTaskObservation(request)
        return action_response
    except grpc.RpcError as e:
        print(f"gRPC call to {server_address} failed: {e.details()} (code: {e.code()})")
        return None
    finally:
        if channel:
            channel.close()

if __name__ == '__main__':
    # Prepare sample observation data
    sample_observation_data = {
        "event_id": str(uuid.uuid4()),
        "event_type": "task_complete",
        "timestamp_iso": datetime.datetime.utcnow().isoformat() + "Z",
        "pipeline_name": "MainAnalysisPipeline",
        "process_name": "AlignmentProcess",
        "task_id_num": "98765", # Example as string, will be converted
        "task_hash": "fedcba654321",
        "task_name": "AlignReads (SampleX)",
        "native_id": "native_002",
        "status": "COMPLETED",
        "exit_code": "0", # Example as string
        "duration_ms": "123450" # Example as string
    }

    print("Running nf_client standalone test...")
    action = send_task_observation(sample_observation_data)

    if action:
        print("\nReceived Action Details:")
        print(f"  Action ID: {action.action_id}")
        print(f"  Correlates to Event ID: {action.observation_event_id}")
        print(f"  Success: {action.success}")
        print(f"  Message: '{action.message}'")
        print(f"  Details: '{action.action_details}'")
    else:
        print("Failed to receive action from server.")
