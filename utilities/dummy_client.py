import grpc

# Import the generated classes
import sys
import os
# Add the generated protobuf modules relative to this file so that the client
# can be executed from any location.
proto_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'proto'))
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)
import dummy_pb2
import dummy_pb2_grpc

def run():
    # Connect to the server
    channel = grpc.insecure_channel('localhost:50051')

    # Create a stub (client)
    stub = dummy_pb2_grpc.GreeterStub(channel)

    # Create a request message
    request = dummy_pb2.HelloRequest()
    request.name = "World"

    # Make the call
    try:
        response = stub.SayHello(request)
        print(f"Greeter client received: {response.message}")
    except grpc.RpcError as e:
        print(f"Error: {e.details()} (code: {e.code()})")
    finally:
        channel.close()

if __name__ == '__main__':
    run()
