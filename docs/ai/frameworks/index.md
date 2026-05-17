# ML Frameworks

PyTorch, TensorFlow, and JAX as applications — what runs on the MS-S1
MAX (AMD Strix Halo, ROCm) and what runs on Apple Silicon laptops
(Metal / MPS).

These pages cover the framework *clients*: how to install the right
wheel, verify the GPU is actually engaged, and the few hardware-specific
gotchas. They do not duplicate the framework documentation itself —
treat them as the bridge between the upstream docs and the specific
machines used here.

## Hardware target summary

| Target | GPU | Compute stack | Framework story |
|--------|-----|---------------|-----------------|
| MS-S1 MAX | AMD Strix Halo iGPU (`gfx1151`) | ROCm 7.x / HIP | PyTorch (ROCm wheels), JAX (ROCm wheels), TensorFlow CPU only today |
| Apple Silicon laptop | Apple M-series GPU | Metal / MPS | PyTorch (MPS backend), JAX (Metal plugin), TensorFlow (`tensorflow-macos` + `tensorflow-metal`) |

NVIDIA / CUDA is intentionally out of scope — this build has no NVIDIA
hardware.

## Framework support matrix

| Framework | MS-S1 MAX (`gfx1151`) | Apple Silicon | Notes |
|-----------|-----------------------|---------------|-------|
| [PyTorch](pytorch.md) | Yes — ROCm wheels | Yes — `mps` backend | Most mature ROCm story; `torch.cuda.*` API resolves to AMD GPU on ROCm |
| [JAX](jax.md) | Yes — `jax[rocm]` wheels | Yes — `jax-metal` plugin | Apple Metal plugin lags upstream JAX — version pinning matters |
| [TensorFlow](tensorflow.md) | CPU only today | Yes — `tensorflow-macos` + `tensorflow-metal` | Upstream TF-ROCm builds lag; community `tensorflow-rocm` wheels exist but are not 1st-party for `gfx1151` |

## Pages

<div class="grid cards" markdown>

-   :material-fire: **PyTorch**

    ---

    ROCm wheels for the MS-S1 MAX, MPS backend on Apple Silicon, common
    pitfalls.

    [:octicons-arrow-right-24: PyTorch](pytorch.md)

-   :material-tensorflow: **TensorFlow**

    ---

    Honest assessment of TF on ROCm `gfx1151`, plus the Apple Metal
    plugin path for laptops.

    [:octicons-arrow-right-24: TensorFlow](tensorflow.md)

-   :material-google: **JAX**

    ---

    JAX with ROCm wheels on the MS-S1 MAX and `jax-metal` on Apple
    Silicon.

    [:octicons-arrow-right-24: JAX](jax.md)

</div>

## See Also

- [ROCm Installation](../gpu/rocm-installation.md) - The prerequisite for
  any ROCm framework wheel
- [Memory Configuration](../gpu/memory-configuration.md) - UMA frame
  buffer settings that determine how much "VRAM" your framework sees
- [Inference Engines](../inference-engines/index.md) - When you don't
  actually need to train and just want llama.cpp / Ollama
