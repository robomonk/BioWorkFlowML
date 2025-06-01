import sys
import os
import datetime
import uuid
import time

# Add project root to sys.path to allow utilities.ai_server and utilities.nf_client imports
# This is needed when running 'python utilities/test_integration.py' from the project root,
# or if 'utilities' is not directly in PYTHONPATH.
# Assumes this script is in 'utilities' and project root is one level up.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
proto_dir = os.path.join(project_root, 'proto')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir) # Add proto dir directly

# Now that sys.path is adjusted, we can import from utilities and proto deps should be found
from utilities.ai_server import AiServer
from utilities.nf_client import send_task_observation


TEST_SERVER_PORT = 50059
TEST_LOG_FILE = "/tmp/test_ai_server.log"

if __name__ == "__main__":
    print("Starting integration test...")

    # Instantiate and start the AI Server
    ai_server = AiServer(port=TEST_SERVER_PORT, log_file=TEST_LOG_FILE)
    print(f"Attempting to start AI Server on port {TEST_SERVER_PORT} with log file {TEST_LOG_FILE}...")
    ai_server.start()
    print("AI Server started.")

    # Allow server a moment to fully start
    # Increased sleep time to ensure server is ready, especially in slower CI environments
    time.sleep(2)

    # Prepare sample observation data
    sample_observation_data = {
        "event_id": str(uuid.uuid4()),
        "event_type": "test_event_from_integration_script",
        "timestamp_iso": datetime.datetime.utcnow().isoformat() + "Z",
        "pipeline_name": "integration_test_pipeline",
        "process_name": "integration_test_process",
        "task_id_num": "777", # Sending as string, client should handle conversion
        "status": "TESTING",
    }

    print(f"Sending task observation (event_id={sample_observation_data['event_id']}) to localhost:{TEST_SERVER_PORT}")
    action_response = None
    test_success = False
    try:
        action_response = send_task_observation(
            sample_observation_data,
            server_address=f'localhost:{TEST_SERVER_PORT}'
        )

        if action_response:
            print(f"Received action: ID={action_response.action_id}, Success={action_response.success}")
            print(f"Details: {action_response.action_details}")
            print(f"Correlated Event ID: {action_response.observation_event_id}")

            assert action_response.success, "Action response success was not True!"
            assert action_response.observation_event_id == sample_observation_data["event_id"], \
                f"Observation event ID mismatch! Expected {sample_observation_data['event_id']}, Got {action_response.observation_event_id}"

            print("Client received valid and successful response.")
            test_success = True
        else:
            print("Client did not receive a response.")
            # This case will lead to test_success remaining False

        if test_success:
            print("Integration test successful!")
        else:
            # This else is important if action_response was None
            print("Integration test failed: Client did not receive a valid response or assertions failed.")


    except Exception as e:
        print(f"Integration test failed with exception: {e}")
        test_success = False
        # Optionally re-raise if needed, but for now, let it proceed to finally
        # raise

    finally:
        print("Stopping AI Server...")
        ai_server.stop(0) # Grace period 0 for immediate stop
        print("AI Server stopped.")

        # Log inspection (optional, but useful for debugging)
        if os.path.exists(TEST_LOG_FILE):
            print(f"\n--- Content of {TEST_LOG_FILE} ---")
            with open(TEST_LOG_FILE, "r") as f:
                print(f.read())
            print("--- End of log ---")
            # For automated tests, you might choose to remove the log file:
            # os.remove(TEST_LOG_FILE)
        else:
            print(f"Test log file {TEST_LOG_FILE} was not created.")

    # Exit with a status code reflecting test success or failure
    if not test_success:
        sys.exit(1) # Indicate failure
    else:
        sys.exit(0) # Indicate success
