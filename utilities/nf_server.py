import grpc
from concurrent import futures
import time
import uuid

# Import the generated classes
import sys
sys.path.append('../proto') # Add proto folder to Python path
import nf_ai_comms_pb2
import nf_ai_comms_pb2_grpc

class AiActionServiceServicer(nf_ai_comms_pb2_grpc.AiActionServiceServicer):
    def SendTaskObservation(self, request, context):
        print(f"Received TaskObservation: event_id={request.event_id}, event_type={request.event_type}")
        response = nf_ai_comms_pb2.Action()
        response.observation_event_id = request.event_id
        response.action_id = str(uuid.uuid4())
        response.action_details = f"Action for event {request.event_id}: Processed event type '{request.event_type}'"
        response.success = True
        response.message = "Successfully processed TaskObservation"
        print(f"Sending Action: action_id={response.action_id}")
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    nf_ai_comms_pb2_grpc.add_AiActionServiceServicer_to_server(AiActionServiceServicer(), server)
    port = '50052' # Using a different port than the dummy server
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"AiActionService server started. Listening on port {port}.")
    try:
        while True:
            time.sleep(86400) # Keep server alive
    except KeyboardInterrupt:
        server.stop(0)
        print("Server stopped.")

if __name__ == '__main__':
    serve()
