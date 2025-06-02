package com.yourorg.bioflowml.plugin

import nextflow.Session
import nextflow.trace.TraceObserverV2
import nextflow.trace.TraceObserverFactoryV2
import org.pf4j.Extension // Required for PF4J to discover this factory

@Extension
class TaskEventNotifierFactory implements TraceObserverFactoryV2 {
    @Override
    Collection<TraceObserverV2> create(Session session) {
        // In a real scenario, get Python server address/port from session.config
        String pythonServerHost = session.config.navigate('bioworkflowml_logger.host', 'localhost')
        int pythonServerPort = session.config.navigate('bioworkflowml_logger.port', 50052)

        // Log that the factory is creating the observer
        // System.out.println("BioWorkFlowML Logger: Creating TaskEventNotifierObserver for " + pythonServerHost + ":" + pythonServerPort)

        return [new TaskEventNotifierObserver(pythonServerHost, pythonServerPort)]
    }
}
