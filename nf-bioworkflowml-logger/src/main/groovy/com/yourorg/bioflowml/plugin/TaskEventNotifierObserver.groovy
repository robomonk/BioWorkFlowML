package com.yourorg.bioflowml.plugin

import nextflow.trace.TraceObserverV2
import nextflow.trace.TraceRecord
import nextflow.processor.TaskHandler
import nextflow.Session // For onWorkflowStart
import groovy.transform.CompileStatic // Optional: for type checking

// Imports for Guava ListenableFuture and Futures for async gRPC
import com.google.common.util.concurrent.ListenableFuture
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.FutureCallback
import com.google.common.util.concurrent.MoreExecutors


// Imports for gRPC (assuming generated Java classes are in classpath)
import io.grpc.ManagedChannel
import io.grpc.ManagedChannelBuilder
// Assuming nf_ai_comms.proto generated classes are under com.yourorg.bioflowml.grpc
import com.yourorg.bioflowml.grpc.NfAiCommsProto
import com.yourorg.bioflowml.grpc.AiActionServiceGrpc

import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.util.UUID

// @CompileStatic // Enable if you want stricter Groovy compilation
class TaskEventNotifierObserver implements TraceObserverV2 {

    private ManagedChannel channel
    private AiActionServiceGrpc.AiActionServiceFutureStub futureStub
    private String id = UUID.randomUUID().toString()

    TaskEventNotifierObserver(String host, int port) {
        try {
            // System.out.println("BioWorkFlowML Logger (" + id + "): Initializing gRPC client for " + host + ":" + port)
            this.channel = ManagedChannelBuilder.forAddress(host, port)
                                .usePlaintext() // For simplicity, use plaintext
                                .build()
            this.futureStub = AiActionServiceGrpc.newFutureStub(channel)
            // System.out.println("BioWorkFlowML Logger (" + id + "): gRPC client initialized.")
        } catch (Exception e) {
            // System.err.println("BioWorkFlowML Logger (" + id + "): Failed to initialize gRPC client: " + e.getMessage())
            e.printStackTrace()
            // Set channel and stub to null if initialization fails
            this.channel = null
            this.futureStub = null
        }
    }

    private void sendObservation(String eventType, String taskName = "", String processName = "", String status = "") {
        if (futureStub == null) {
            // System.err.println("BioWorkFlowML Logger (" + id + "): gRPC stub not available. Cannot send observation for event: " + eventType)
            return
        }
        try {
            // System.out.println("BioWorkFlowML Logger (" + id + "): Sending observation: " + eventType + " for task: " + taskName)
            NfAiCommsProto.TaskObservation.Builder observationBuilder = NfAiCommsProto.TaskObservation.newBuilder()
                .setEventId(UUID.randomUUID().toString())
                .setEventType(eventType)
                .setTimestampIso(OffsetDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME))
                .setPipelineName("pipeline-name-placeholder") // TODO: Get actual pipeline name if possible
                .setTaskName(taskName ?: "N/A")
                .setProcessName(processName ?: "N/A")
                .setStatus(status ?: "N/A");

            // Add more fields if necessary/available
            ListenableFuture<NfAiCommsProto.Action> future = futureStub.sendTaskObservation(observationBuilder.build());

            Futures.addCallback(
                future,
                new FutureCallback<NfAiCommsProto.Action>() {
                    @Override
                    void onSuccess(NfAiCommsProto.Action result) {
                        // System.out.println("BioWorkFlowML Logger (" + id + "): Async send success for event " + eventType + ". Response: " + result.getActionId())
                    }

                    @Override
                    void onFailure(Throwable t) {
                        // System.err.println("BioWorkFlowML Logger (" + id + "): Async send failed for event " + eventType + ": " + t.getMessage())
                    }
                },
                MoreExecutors.directExecutor() // Using Guava's direct executor
            );

        } catch (Exception e) {
            // System.err.println("BioWorkFlowML Logger (" + id + "): Error sending gRPC message for event " + eventType + ": " + e.getMessage())
            // e.printStackTrace()
        }
    }

    @Override
    void onWorkflowStart(Session session) {
        // System.out.println("BioWorkFlowML Logger (" + id + "): Workflow starting...")
        // Optionally send a "workflow_start" event or similar if desired
    }

    // NOTE: There isn't a direct "onTaskStart" in TraceObserverV2 that's universally ideal.
    // onProcessSubmit, onProcessCached, or observing task status changes might be alternatives.
    // For simplicity, we'll rely on onProcessSubmitted and onProcessCached as proxies for "start"
    // and onProcessComplete for "done".
    // The Python server already handles "task_start" and "task_complete" event types.

    @Override
    void onProcessSubmit(TaskHandler handler, TraceRecord trace) {
        sendObservation("task_start", handler.getTask().getName(), handler.getTask().getProcess(), "SUBMITTED")
    }

    @Override
    void onProcessCached(TaskHandler handler, TraceRecord trace) {
        // Consider if cached tasks should also trigger a "start" and "done"
        // For this example, we'll send "task_start" assuming it's like starting,
        // and then it will be followed by onProcessComplete.
        sendObservation("task_start", handler.getTask().getName(), handler.getTask().getProcess(), "CACHED_START")
    }

    @Override
    void onProcessComplete(TaskHandler handler, TraceRecord trace) {
        String status = trace.getStatus().toString() // COMPLETED, FAILED, etc.
        sendObservation("task_complete", handler.getTask().getName(), handler.getTask().getProcess(), status)
    }

    @Override
    void onWorkflowComplete(Session session) {
        // System.out.println("BioWorkFlowML Logger (" + id + "): Workflow completed.")
        // Shutdown the gRPC channel
        if (channel != null && !channel.isShutdown()) {
            // System.out.println("BioWorkFlowML Logger (" + id + "): Shutting down gRPC channel.")
            channel.shutdown()
        }
    }
}
