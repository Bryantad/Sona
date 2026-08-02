#[derive(Clone, Debug)]
pub struct RuntimeLimits {
    pub max_call_depth: usize,
    pub max_instructions: usize,
    pub max_collection_size: usize,
    pub max_string_bytes: usize,
    pub max_import_depth: usize,
}

impl Default for RuntimeLimits {
    fn default() -> Self {
        Self {
            max_call_depth: 128,
            max_instructions: 1_000_000,
            max_collection_size: 100_000,
            max_string_bytes: 1_048_576,
            max_import_depth: 16,
        }
    }
}

#[derive(Clone, Debug)]
pub struct RuntimeCapabilities {
    pub console: bool,
    pub filesystem_read: bool,
    pub filesystem_write: bool,
    pub network: bool,
    pub process: bool,
    pub environment: bool,
}

impl Default for RuntimeCapabilities {
    fn default() -> Self {
        Self {
            console: true,
            filesystem_read: false,
            filesystem_write: false,
            network: false,
            process: false,
            environment: false,
        }
    }
}

#[derive(Clone, Debug, Default)]
pub struct RuntimeConfig {
    pub limits: RuntimeLimits,
    pub capabilities: RuntimeCapabilities,
}
