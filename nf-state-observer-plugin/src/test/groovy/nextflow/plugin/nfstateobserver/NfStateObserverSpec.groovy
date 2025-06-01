package nextflow.plugin.nfstateobserver

import spock.lang.Specification
import org.pf4j.PluginWrapper
import org.pf4j.DefaultPluginManager
import org.pf4j.PluginState

// Attempt to import a generated gRPC class to check protobuf compilation
import com.yourorg.bioflowml.grpc.NfAiCommsProto.TaskObservation // Corrected import for nested class

class NfStateObserverSpec extends Specification {

    def "check if plugin can be loaded and gRPC classes are available"() {
        given: "A plugin manager and a plugin wrapper"
        // We need a PluginManager to create a PluginWrapper
        // This is a simplified setup. For real unit tests, you might need more mocking.
        def pluginManager = new DefaultPluginManager()

        // Create a dummy PluginWrapper for our plugin
        // Normally, Nextflow or PF4J runtime would create this.
        // We need to provide enough information for the plugin to be instantiated.
        // The paths might not be relevant for this basic test but are typically part of wrapper.
        def pluginWrapper = new PluginWrapper(pluginManager,
            new org.pf4j.PluginDescriptor() {
                @Override String getPluginId() { "nf-state-observer-plugin" }
                @Override String getPluginDescription() { "Test" }
                @Override String getPluginClass() { NfStateObserver.class.name }
                @Override String getVersion() { "0.1.0" }
                @Override String getRequires() { "*" }
                @Override String getProvider() { "Test" }
                @Override String getLicense() { "Apache-2.0" }
                @Override List<org.pf4j.PluginDependency> getDependencies() { [] }
            },
            null, // pluginPath - not essential for this test
            null  // pluginClassLoader - PF4J will create one
        )

        when: "The plugin is instantiated"
        def plugin = new NfStateObserver(pluginWrapper)

        then: "The plugin instance should not be null"
        plugin != null

        and: "The plugin's wrapper is set correctly"
        plugin.getWrapper() == pluginWrapper

        and: "We can reference a gRPC generated class (TaskObservation)"
        // This line primarily checks if the class is available, meaning proto compilation worked.
        // We are not doing much with it other than proving it can be loaded.
        def observation = TaskObservation.newBuilder().build()
        observation != null

        // Optional: Simulate plugin lifecycle
        when: "Plugin lifecycle methods are called"
        plugin.start()
        plugin.stop()

        then: "No exceptions should be thrown"
        noExceptionThrown()

        // Clean up plugin manager if necessary, though for this simple test it might not be strictly needed
        // pluginManager.stopPlugins() // This might be needed if plugins were actually loaded and started
    }
}
