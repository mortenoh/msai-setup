# TensorFlow

Honest status check first: TensorFlow on the AMD Strix Halo iGPU
(`gfx1151`) is in worse shape than PyTorch. Apple Silicon laptops have
a clean install path via the Metal plugin.

## MS-S1 MAX — TensorFlow status

**Recommendation: use CPU TensorFlow for now, or use PyTorch / JAX
instead.**

Upstream TensorFlow's official ROCm builds (`tensorflow-rocm`) target
Instinct/CDNA GPUs and lag behind PyTorch in `gfx1151` support. As of
ROCm 7.x there is no first-party `tensorflow-rocm` wheel that
specifically advertises Strix Halo support. Community builds exist on
GitHub and the AMD developer forums; if you must use TensorFlow on this
GPU, expect to:

- Build TensorFlow from source against your ROCm install, or
- Use a community-supplied wheel and live with surprises
- Verify every workload — kernels that "work" can still produce silently
  wrong numbers if the build isn't current

For most users the right answer is one of:

1. **Inference-only?** Use Ollama / llama.cpp (see
   [Inference Engines](../inference-engines/index.md)).
2. **Training a model from a TensorFlow codebase?** Port to PyTorch or
   JAX — both have working ROCm wheels for `gfx1151`.
3. **You need TensorFlow specifically and the model is small?** Use
   CPU TensorFlow. The MS-S1 MAX has a competent 16-core CPU and large
   amounts of fast unified memory — for many traditional ML workloads
   this is fine.

### CPU install on the MS-S1 MAX

```bash
python3 -m venv ~/.venvs/tf-cpu
source ~/.venvs/tf-cpu/bin/activate
pip install --upgrade pip
pip install tensorflow
```

Verify:

```python
import tensorflow as tf
print(tf.__version__)
print("Built with CUDA:", tf.test.is_built_with_cuda())     # False here
print("GPUs:", tf.config.list_physical_devices("GPU"))      # likely []
```

`tf.test.is_built_with_cuda()` returns `False`, and no GPU devices are
listed — expected for the CPU wheel.

### Optional: trying tensorflow-rocm

If you want to experiment with `tensorflow-rocm` anyway, treat this as
research, not production:

```bash
# Heads-up: 'pip install tensorflow-rocm' may install an older build
# that does not include gfx1151 kernels. Check the package's recent
# release notes on PyPI/GitHub before committing time to it.
pip install tensorflow-rocm
```

Then verify:

```python
import tensorflow as tf
gpus = tf.config.list_physical_devices("GPU")
print("GPUs:", gpus)
if gpus:
    with tf.device("/GPU:0"):
        x = tf.random.normal((4096, 4096))
        y = tf.random.normal((4096, 4096))
        z = tf.reduce_sum(x @ y).numpy()
        print("Result OK:", z)
```

If `GPUs:` is empty, the wheel didn't pick up the iGPU. Watch
`rocm-smi` while running a matmul: if utilisation stays at 0, the GPU
isn't being used regardless of what the API reports.

## Apple Silicon — TensorFlow with Metal

This path is supported and works well for laptop development.

### Install

```bash
python3 -m venv ~/.venvs/tf-metal
source ~/.venvs/tf-metal/bin/activate
pip install --upgrade pip

# Base TF wheel for macOS
pip install tensorflow

# Apple's Metal acceleration plugin
pip install tensorflow-metal
```

The `tensorflow-metal` plugin registers a PluggableDevice that
TensorFlow picks up automatically.

### Verify

```python
import tensorflow as tf

print(tf.__version__)
print("GPUs:", tf.config.list_physical_devices("GPU"))

with tf.device("/GPU:0"):
    x = tf.random.normal((4096, 4096))
    y = tf.random.normal((4096, 4096))
    z = tf.reduce_sum(x @ y).numpy()
    print("Result OK:", z)
```

You should see something like `[PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]`.

While the matmul runs, `sudo powermetrics --samplers gpu_power -i 1000`
should show GPU power activity.

### Apple Metal gotchas

- The Metal plugin lags the upstream `tensorflow` release by some
  amount. If a brand-new TF version breaks Metal acceleration, pin to
  the most recent combination that works (see Apple's
  [tensorflow-metal release notes](https://developer.apple.com/metal/tensorflow-plugin/)).
- Some ops fall back to CPU silently. Profile rather than assume the
  whole graph runs on the GPU.
- Mixed precision via `tf.keras.mixed_precision.set_global_policy("mixed_float16")`
  works on Apple Silicon and is usually a sizeable speedup.

## Minimal training step (works on Metal; works on CPU TF on MS-S1 MAX)

```python
import tensorflow as tf

# Trivial MLP
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(1024,)),
    tf.keras.layers.Dense(4096, activation="gelu"),
    tf.keras.layers.Dense(10),
])
model.compile(
    optimizer=tf.keras.optimizers.AdamW(1e-4),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)

import numpy as np
x = np.random.randn(1024, 1024).astype("float32")
y = np.random.randint(0, 10, size=(1024,))

model.fit(x, y, batch_size=64, epochs=2)
```

On Apple Silicon with `tensorflow-metal` this will use the GPU. On the
MS-S1 MAX with the CPU wheel it will use all CPU cores.

## See also

- [Apple — tensorflow-metal plugin](https://developer.apple.com/metal/tensorflow-plugin/)
- [PyTorch](pytorch.md) - the recommended framework for ROCm `gfx1151`
- [JAX](jax.md) - the other framework with usable ROCm wheels
- [ROCm Installation](../gpu/rocm-installation.md)
