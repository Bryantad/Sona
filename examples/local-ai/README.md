# Example A — Direct local AI

This example loads a GGUF file directly through `llama.cpp`; it does not use
Ollama and has no cloud fallback.

Install Sona with its optional direct runtime, then pass an existing model:

```powershell
python -m pip install "sona-lang[llama-cpp]"
python examples/local-ai/run_local.py D:\Models\coder.gguf --device cpu
```

The file is loaded only for this run and unloaded in `finally`. Select `cuda`
only when the installed llama.cpp binding reports CUDA offload support. Hardware
and speed are machine-dependent; this example makes no performance guarantee.

The script fails if the artifact is not a readable GGUF or the optional direct
runtime is unavailable. It never routes the prompt to Ollama or a cloud provider.
