# JAX

JAX has working ROCm wheels for AMD GPUs and a Metal plugin for Apple
Silicon. Both paths are functional but the version pinning matters more
than with PyTorch because the JAX/XLA release train moves quickly.

## MS-S1 MAX — JAX on ROCm

### Prerequisites

- ROCm 7.x installed and working
  (see [ROCm Installation](../gpu/rocm-installation.md))
- User in `video` and `render` groups
- Python 3.10+ in a virtual environment

### Install

AMD publishes ROCm-built JAX wheels on PyPI as `jax[rocm]`. The exact
extras tag may be `jax[rocm]` or a versioned variant — check the
[ROCm JAX docs](https://rocm.docs.amd.com/projects/jax/) for the
current name.

```bash
python3 -m venv ~/.venvs/jax-rocm
source ~/.venvs/jax-rocm/bin/activate
pip install --upgrade pip

# Install ROCm-enabled JAX
# (Confirm exact wheel name + index URL from the upstream ROCm-JAX docs)
pip install --upgrade "jax[rocm]" \
  -f https://repo.radeon.com/rocm/manylinux/rocm-rel-7.1/
```

If you hit an error along the lines of "no matching distribution", the
ROCm-JAX wheel index URL has changed. Refer to the ROCm-JAX docs for
the version-specific URL.

### Verify

```python
import jax
import jax.numpy as jnp

print("JAX version:", jax.__version__)
print("Devices:    ", jax.devices())
print("Default backend:", jax.default_backend())

x = jnp.ones((4096, 4096))
y = jnp.ones((4096, 4096))
z = (x @ y).sum()
print("Result OK:", float(z))
```

Expected output on the MS-S1 MAX: `jax.devices()` returns one device of
type `rocm` (sometimes printed as `gpu`), and `jax.default_backend()` is
`"rocm"` or `"gpu"`.

While the matmul runs, `rocm-smi` on the host should show utilisation.

### ROCm-specific knobs

| Variable | Use |
|----------|-----|
| `HSA_OVERRIDE_GFX_VERSION=11.5.1` | Only if you're on an older ROCm that doesn't recognise `gfx1151`. Not needed on ROCm 7.x. |
| `XLA_PYTHON_CLIENT_MEM_FRACTION` | Controls how much of "GPU memory" XLA pre-allocates. With unified memory, keep this modest (e.g. `0.5`) to avoid starving the rest of the system. |
| `XLA_PYTHON_CLIENT_PREALLOCATE=false` | Disables eager allocation entirely; useful while developing. |
| `JAX_PLATFORMS=rocm` | Force the ROCm backend if both CPU and GPU are present and JAX picks CPU. |

### Common gotchas

- **`jax.devices()` returns CPU only**: the most common cause is a
  CPU-only JAX wheel sneaking in via a dependency. `pip show jax
  jaxlib` should show ROCm-tagged versions. If not, reinstall with the
  ROCm index URL.
- **Mismatched `jax` and `jaxlib` versions**: JAX is two packages and
  they must agree. After installing ROCm wheels, double-check
  `jax.__version__` matches the `jaxlib` version JAX prints in error
  traces.
- **First call slow**: XLA compilation happens on first execution.
  Subsequent calls with the same shapes are fast. This is the same
  behavior as JAX on any backend.
- **Unified memory accounting**: XLA pre-allocates based on what ROCm
  reports as GPU memory. On Strix Halo that's the UMA frame buffer
  setting — see [Memory Configuration](../gpu/memory-configuration.md).

## Apple Silicon — JAX with the Metal plugin

Apple supplies a `jax-metal` plugin that exposes Metal as a JAX
backend.

### Install

```bash
python3 -m venv ~/.venvs/jax-metal
source ~/.venvs/jax-metal/bin/activate
pip install --upgrade pip

pip install jax-metal
```

`jax-metal` pulls in compatible `jax` / `jaxlib` versions. Apple is
explicit about which JAX versions a given `jax-metal` release supports
— pin both if you have a working combination.

### Verify

```python
import jax
import jax.numpy as jnp

print("JAX version:", jax.__version__)
print("Devices:    ", jax.devices())
print("Default backend:", jax.default_backend())

x = jnp.ones((4096, 4096))
y = jnp.ones((4096, 4096))
z = (x @ y).sum()
print("Result OK:", float(z))
```

You should see one device of platform `METAL`.

### Metal gotchas

- `jax-metal` historically supports a narrow range of `jax` versions.
  Pin both `jax==X.Y.Z` and `jax-metal==A.B.C` once you have a working
  combination.
- Some ops are missing or fall back to CPU. Check the
  [jax-metal release notes](https://developer.apple.com/metal/jax/) for
  the supported ops list before committing to a workload.
- The plugin runs in eager mode by default; expect a smaller speedup
  than what you would get on a discrete GPU, especially for tiny
  shapes.

## Minimal training step (portable)

This works on both targets. JAX will use the ROCm backend on the
MS-S1 MAX and the Metal backend on Apple Silicon, falling back to CPU
elsewhere:

```python
import jax
import jax.numpy as jnp
from jax import grad, jit, random

@jit
def loss_fn(params, x, y):
    pred = x @ params["w1"]
    pred = jax.nn.gelu(pred)
    pred = pred @ params["w2"]
    return jnp.mean((pred - y) ** 2)

key = random.key(0)
params = {
    "w1": random.normal(random.fold_in(key, 1), (1024, 4096)) * 0.01,
    "w2": random.normal(random.fold_in(key, 2), (4096, 10))   * 0.01,
}

@jit
def step(params, x, y, lr=1e-3):
    grads = grad(loss_fn)(params, x, y)
    return {k: v - lr * grads[k] for k, v in params.items()}

x = random.normal(random.fold_in(key, 3), (64, 1024))
y = random.normal(random.fold_in(key, 4), (64, 10))

for s in range(50):
    params = step(params, x, y)
    if s % 10 == 0:
        print(s, float(loss_fn(params, x, y)))
```

## See also

- [ROCm-JAX docs](https://rocm.docs.amd.com/projects/jax/)
- [Apple — jax-metal plugin](https://developer.apple.com/metal/jax/)
- [PyTorch](pytorch.md) - the most mature ROCm framework
- [TensorFlow](tensorflow.md) - status check before committing to TF
  on ROCm
- [ROCm Installation](../gpu/rocm-installation.md)
- [Memory Configuration](../gpu/memory-configuration.md)
