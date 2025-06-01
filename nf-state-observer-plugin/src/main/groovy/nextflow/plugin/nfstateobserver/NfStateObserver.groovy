package nextflow.plugin.nfstateobserver

import org.pf4j.Plugin
import org.pf4j.PluginWrapper

class NfStateObserver extends Plugin {
    NfStateObserver(PluginWrapper wrapper) {
        super(wrapper)
    }

    @Override
    void start() {
        // Plugin startup logic
        System.out.println("${wrapper.pluginId} plugin started")
    }

    @Override
    void stop() {
        // Plugin cleanup logic
        System.out.println("${wrapper.pluginId} plugin stopped")
    }
}
