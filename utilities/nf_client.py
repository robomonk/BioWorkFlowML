import grpc
import uuid
import datetime

# Import the generated classes
import sys
sys.path.append('../proto') # Add proto folder to Python path
import nf_ai_comms_pb2
import nf_ai_comms_pb2_grpc

def run_client():
    # Connect to the server
    channel = grpc.insecure_channel('localhost:50052') # Port for AiActionService

    # Create a stub (client)
    stub = nf_ai_comms_pb2_grpc.AiActionServiceStub(channel)

    # Create a TaskObservation request message
    observation = nf_ai_comms_pb2.TaskObservation()
    observation.event_id = str(uuid.uuid4())
    observation.event_type = "task_start"
    observation.timestamp_iso = datetime.datetime.utcnow().isoformat() + "Z"
    observation.pipeline_name = "TestPipeline"
    observation.process_name = "TestProcess"
    observation.task_id_num = 12345
    observation.task_hash = "abcdef123456"
    observation.task_name = "TestProcess (1)"
    observation.native_id = "native_001"
    observation.status = "RUNNING"
    # For a 'task_start' event, fields like exit_code, duration_ms etc., might not be relevant
    # or available yet. They are more typical for 'task_complete'.

    print(f"Sending TaskObservation: event_id={observation.event_id}")

    try:
        # Make the RPC call
        action_response = stub.SendTaskObservation(observation)
        print(f"Received Action: action_id={action_response.action_id}, "
              f"details='{action_response.action_details}', "
              f"success={action_response.success}, "
              f"message='{action_response.message}', "
              f"correlates_to_event_id='{action_response.observation_event_id}'")
    except grpc.RpcError as e:
        print(f"gRPC call failed: {e.details()} (code: {e.code()})")
    finally:
        channel.close()

if __name__ == '__main__':
    run_client()
