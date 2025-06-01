// Defines the package for this plugin. This should match the directory structure.
package NfStateObserver

// Imports necessary classes from Nextflow and PF4J (Plugin Framework for Java).
import nextflow.plugin.BasePlugin // Base class for all Nextflow plugins.
import org.pf4j.Extension         // Annotation to mark classes as extensions.
import org.pf4j.PluginWrapper     // Provides information about the plugin.

/**
 * Main class for the NfStateObserver plugin.
 * This class extends Nextflow's BasePlugin and can hook into various Nextflow lifecycle events
 * and extend Nextflow's functionality, such as adding new commands.
 */
class NfStateObserver extends BasePlugin {

    /**
     * Constructor for the NfStateObserver plugin.
     * This is required by the PF4J plugin framework.
     * @param wrapper The PluginWrapper provides access to plugin metadata and resources.
     */
    NfStateObserver(PluginWrapper wrapper) {
        super(wrapper) // Calls the constructor of the BasePlugin.
    }

    /**
     * This method is a Nextflow lifecycle hook that is called when a new Nextflow session
     * (typically a pipeline run) is created.
     * It's a good place to initialize session-specific resources or log information.
     * @param session The Nextflow Session object, providing context about the current run.
     */
    @Override
    void onSessionCreate(nextflow.Session session) {
        // Logs an informational message indicating the plugin has been loaded for the current session.
        // 'log' is an instance of a logger provided by BasePlugin.
        log.info "[NfStateObserver] Hello World! Plugin loaded for session: ${session.getId()}"
    }

    /**
     * This inner static class demonstrates how to define custom commands that can be
     * invoked from the Nextflow command line.
     * The @Extension annotation marks this class as an extension to be loaded by PF4J.
     */
    @Extension
    public static class MyCommands {

        /**
         * Defines a new command 'greet-agent'.
         * This class extends nextflow.cli.BaseCommand and is marked as an @ExtensionPoint,
         * making it discoverable by Nextflow's command-line interface.
         */
        @org.pf4j.ExtensionPoint // Marks this class as an extension point that can be implemented by plugins.
        public static class SayHelloFromNfStateObserver extends nextflow.cli.BaseCommand {

            /**
             * Constructor for the 'greet-agent' command.
             * Sets the command name and a brief description that will appear in Nextflow's help messages.
             */
            public SayHelloFromNfStateObserver() {
                super("greet-agent", "Prints a greeting from the NfStateObserver plugin")
            }

            /**
             * This method contains the logic that is executed when the 'greet-agent' command is run.
             * For example, `nextflow greet-agent`.
             */
            @Override
            protected void run() {
                // Prints a greeting message to the console.
                println "[NfStateObserver] Greetings from the greet-agent command!"
            }
        }
    }
}

