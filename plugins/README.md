# Plugin System Overview

This directory and its subdirectories contain a two-part plugin system designed to demonstrate communication from a Nextflow pipeline to an external Python application using gRPC.

The system consists of:

1.  **Nextflow Groovy Plugin (`nf-bioworkflowml-logger/`)**:
    -   Located in the `nf-bioworkflowml-logger` subdirectory.
    -   Written in Groovy and designed to be a Nextflow plugin.
    -   Implements `nextflow.trace.TraceObserverV2` to capture task-level events (start, completion, etc.) from a running Nextflow pipeline.
    -   When an event occurs, it serializes the event data using Protocol Buffers and sends it via gRPC to the Python server.
    -   See `nf-bioworkflowml-logger/README.md` for details on its configuration and (conceptual) build process.

2.  **Python gRPC Server (`python_logger/`)**:
    -   Located in the `python_logger` subdirectory.
    -   The main script is `task_event_logger.py`.
    -   This server listens for incoming gRPC messages (TaskObservations) from the Nextflow plugin.
    -   Upon receiving an event, it prints "start" or "done" to the console based on the event type.
    -   See `python_logger/README.md` for prerequisites and instructions on how to run this server.

## General Workflow

To use this plugin system:

1.  **Build the Groovy Plugin (Conceptual):**
    -   The Groovy plugin (`nf-bioworkflowml-logger`) would typically be built using Gradle with the appropriate protobuf and gRPC dependencies. This step is conceptual within this repository as a `build.gradle` is not provided for automated execution.
    -   The build process would generate Java classes from `nf_ai_comms.proto`.

2.  **Install/Configure the Groovy Plugin in Nextflow:**
    -   Once built and packaged (e.g., as a JAR), the plugin needs to be made available to your Nextflow environment.
    -   Configure it in your `nextflow.config` file, specifying its ID (e.g., `bioworkflowml-logger`) and potentially the Python server's address if not using the default (`localhost:50052`). Example:
        ```groovy
        plugins {
            id 'your.group:nf-bioworkflowml-logger:0.1.0' // Adjust based on actual publishing
        }
        bioworkflowml_logger {
            host = 'localhost'
            port = 50052
        }
        ```

3.  **Run the Python gRPC Server:**
    -   Start the `task_event_logger.py` server as described in `plugins/python_logger/README.md`. Ensure `PYTHONPATH` is set correctly to include the `proto` directory.

4.  **Run a Nextflow Pipeline:**
    -   Execute any Nextflow pipeline. If the plugin is correctly installed and configured, and the Python server is running, you should see "start" and "done" messages printed to the Python server's console as tasks in the pipeline begin and complete.

This system provides a basic framework for sending structured data from Nextflow to external applications, enabling various possibilities for monitoring, logging, or triggering external actions based on workflow events.

## Testing the Plugin System

Testing this plugin system involves several steps, as it combines a Nextflow plugin (Groovy) that needs building and an external Python server.

**1. Build the Groovy Nextflow Plugin (`nf-bioworkflowml-logger`)**

This is the most involved manual step. The `nf-bioworkflowml-logger` plugin needs to be compiled and packaged, typically into a JAR or a ZIP file that Nextflow can load.

*   **Prerequisites:**
    *   Java Development Kit (JDK) (e.g., version 11 or 17).
    *   Gradle (a recent version).
*   **Create `build.gradle`:**
    You'll need to create a `build.gradle` file inside the `nf-bioworkflowml-logger` directory. This build script is responsible for compiling the Groovy code, processing the `.proto` file to generate Java gRPC classes, and packaging everything.
    *   **Key `build.gradle` components:**
        *   Apply Gradle plugins: `groovy`, `java`, `com.google.protobuf` (for compiling `.proto` files).
        *   Define dependencies. Example versions are illustrative; use versions compatible with your Nextflow environment:
            ```gradle
            dependencies {
                implementation "org.codehaus.groovy:groovy-all:3.0.10" // Or Groovy version matching Nextflow's
                compileOnly "io.nextflow:nextflow:23.10.0" // Use your Nextflow version; compileOnly as NF provides it

                // gRPC and Protobuf (use recent, compatible versions)
                implementation "io.grpc:grpc-api:1.58.0"
                implementation "io.grpc:grpc-stub:1.58.0"
                implementation "io.grpc:grpc-protobuf:1.58.0"
                implementation "io.grpc:grpc-netty-shaded:1.58.0" // For the client
                implementation "com.google.protobuf:protobuf-java:3.24.4"
                implementation "com.google.protobuf:protobuf-java-util:3.24.4"

                // Guava for ListenableFuture (used by async gRPC client)
                implementation "com.google.guava:guava:32.1.3-jre"

                // For generated gRPC Java code (if javax.annotation is needed)
                // compileOnly 'javax.annotation:javax.annotation-api:1.3.2' // Or 'jakarta.annotation:jakarta.annotation-api:2.1.1' for newer Java versions
            }
            ```
        *   Configure the `protobuf-gradle-plugin` to find the `.proto` file (in `src/main/proto/`) and generate Java classes.
        *   Define tasks to package the plugin into a JAR and potentially a ZIP archive (e.g., `nf-bioworkflowml-logger-0.1.0.zip`) that includes the plugin JAR and its dependencies (like gRPC, Guava).
    *   **Reference:** The [nf-hello plugin](https://github.com/nextflow-io/nf-hello) is an excellent official example for structuring a `build.gradle` for Nextflow plugins.
*   **Build Command:**
    Once `build.gradle` is set up, you'd typically run `gradle build` or `gradle assemble` from within the `nf-bioworkflowml-logger` directory.
*   **Output:** A JAR file (e.g., `nf-bioworkflowml-logger-0.1.0.jar`) in `build/libs/` and potentially a distribution ZIP.

**2. Run the Python gRPC Server**

*   Open a new terminal window.
*   Navigate to the root directory of this repository.
*   **Set `PYTHONPATH`:** Ensure the `proto` directory (which contains the generated Python protobuf files `nf_ai_comms_pb2.py` and `nf_ai_comms_pb2_grpc.py`) is in your `PYTHONPATH`.
    ```bash
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/proto"
    ```
*   **Install Python Dependencies:** If not already installed, you'll need `grpcio` and `grpcio-tools`.
    ```bash
    pip install grpcio grpcio-tools
    ```
*   **Run the Server:**
    ```bash
    python plugins/python_logger/task_event_logger.py
    ```
    You should see output like: `TaskEventLoggerService listening on port 50052...` Keep this server running.

**3. Configure Nextflow to Use the Plugin**

*   **Make the Plugin Available to Nextflow:**
    *   **Development Mode (Recommended for initial testing):**
        If your plugin has its compiled classes in `nf-bioworkflowml-logger/build/classes/groovy/main` (or similar, depending on your Gradle setup), you can try Nextflow's development mode. Set the `NXF_PLUGINS_DEV` environment variable to the *parent directory* of `nf-bioworkflowml-logger`. For example, if your plugin is at `/path/to/your-repo/nf-bioworkflowml-logger`, you might set:
        ```bash
        export NXF_PLUGINS_DEV=/path/to/your-repo
        ```
        Nextflow will attempt to load plugins from source/build directories found there.
    *   **Using `NXF_PLUGINS_DIR` (More robust):**
        Place the built plugin ZIP archive (e.g., `nf-bioworkflowml-logger-0.1.0.zip`) into a dedicated directory (e.g., `/opt/nextflow_plugins/`). Then, set the `NXF_PLUGINS_DIR` environment variable:
        ```bash
        export NXF_PLUGINS_DIR=/opt/nextflow_plugins
        ```
*   **Update `nextflow.config`:**
    In the `nextflow.config` file of the pipeline you want to test with (or your global Nextflow config), add the following:
    ```groovy
    // nextflow.config
    plugins {
        id 'bioworkflowml-logger@0.1.0' // Matches Plugin-Id and Version from MANIFEST.MF
    }

    // Optional: Configure host/port if your Python server is not on localhost:50052
    // These are the defaults used by the plugin if not specified.
    bioworkflowml_logger {
        host = 'localhost'
        port = 50052
    }
    ```

**4. Run a Nextflow Pipeline**

*   Execute any Nextflow pipeline in a separate terminal (where Nextflow is configured to find the plugin).
*   **Expected Output:**
    *   In the terminal running the Python gRPC server (`task_event_logger.py`), you should see "start" printed when a Nextflow task begins and "done" when it completes.
    *   The Nextflow pipeline should run as usual. You might also see log messages from the Groovy plugin in Nextflow's output if you re-enable the commented-out `System.out.println` statements within `TaskEventNotifierObserver.groovy` for debugging.

This detailed setup is necessary due to the manual build step for the Groovy/Java-based Nextflow plugin and the coordination with the external Python server.
