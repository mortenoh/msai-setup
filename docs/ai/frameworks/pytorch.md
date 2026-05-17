# PyTorch

PyTorch on the two supported targets:

- **MS-S1 MAX**: AMD Strix Halo iGPU (`gfx1151`), ROCm 7.x.
- **Apple Silicon laptop**: M-series GPU via the `mps` backend.

Both paths give you a Python session that does GPU-accelerated tensor
ops; the install commands and a few API names differ.

## MS-S1 MAX — PyTorch on ROCm

### Prerequisites

- ROCm 7.x installed and working on the host
  (see [ROCm Installation](../gpu/rocm-installation.md))
- Your user is in the `video` and `render` groups
- Python 3.10+ in a virtual environment (do not install ROCm wheels
  into the system Python)

Quick sanity check before installing:

```bash
rocminfo | head
rocm-smi
```

You should see `gfx1151` listed as the agent.

### Install the ROCm wheels

PyTorch ships official ROCm wheels via its own wheel index. Pick the
index URL that matches your ROCm version (check
[pytorch.org/get-started](https://pytorch.org/get-started/locally/) for
the current ROCm wheel URL — it changes with each ROCm major release):

```bash
python3 -m venv ~/.venvs/torch-rocm
source ~/.venvs/torch-rocm/bin/activate
pip install --upgrade pip

# ROCm 7.1 wheels (example — verify the index URL on pytorch.org)
pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/rocm7.1
```

### Verify the GPU is engaged

```python
import torch

# On ROCm, the `torch.cuda` API namespace is reused for HIP devices.
# This is intentional — code written for CUDA generally runs unchanged.
print("CUDA-API available:", torch.cuda.is_available())
print("Device count:      ", torch.cuda.device_count())
print("Device 0 name:     ", torch.cuda.get_device_name(0))

# Force a real allocation + matmul to make sure HIP is actually wired up
x = torch.randn(4096, 4096, device="cuda")
y = torch.randn(4096, 4096, device="cuda")
z = (x @ y).sum().item()
print("Result OK:", z)
```

Expected output on the MS-S1 MAX: `device 0` shows the AMD GPU
(name varies with ROCm version, e.g. `AMD Radeon Graphics (gfx1151)`).
While the matmul runs, `rocm-smi` on the host should show GPU
utilisation > 0%.

### Environment knobs that matter

| Variable | Use |
|----------|-----|
| `HSA_OVERRIDE_GFX_VERSION` | Set to `11.5.1` if you are stuck on an older ROCm that doesn't recognise `gfx1151`. Not needed on ROCm 7.x. |
| `HIP_VISIBLE_DEVICES` | Restrict which GPUs PyTorch sees. With one iGPU this is rarely useful, but it lets you sanity-check device 0. |
| `PYTORCH_HIP_ALLOC_CONF=expandable_segments:True` | Helps with fragmentation under long-running workloads. |
| `HSA_ENABLE_SDMA=0` | Workaround for occasional SDMA-related hangs on `gfx1151`. Try this if you see GPU hangs under heavy IO. |

### Common gotchas

- **`torch.cuda.*` everywhere**: PyTorch's ROCm wheels reuse the `cuda`
  Python module name. `torch.cuda.is_available()` returning `True` does
  *not* mean CUDA is installed — it means the HIP backend found your
  AMD GPU.
- **AMP / bf16**: Strix Halo supports bf16 in HIP. Use
  `torch.autocast("cuda", dtype=torch.bfloat16)` rather than fp16 when
  you can; fp16 throughput on RDNA 3.5 is comparable but bf16 has
  better numerical headroom.
- **Memory pressure**: the iGPU's "VRAM" is a slice of the unified
  memory pool, configured via the BIOS UMA frame buffer. If you get
  `out of memory` errors at sizes that "should" fit, raise the UMA
  setting first — see
  [Memory Configuration](../gpu/memory-configuration.md).
- **Wheel/runtime mismatch**: ROCm wheels are built against a specific
  ROCm version. If you upgrade ROCm, re-install matching torch wheels
  on the same day. Mixed versions present as silent kernel launch
  failures.

### Minimal training loop

```python
import torch
from torch import nn

device = "cuda" if torch.cuda.is_available() else "cpu"

model = nn.Sequential(
    nn.Linear(1024, 4096),
    nn.GELU(),
    nn.Linear(4096, 10),
).to(device)

opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
loss_fn = nn.CrossEntropyLoss()

for step in range(100):
    x = torch.randn(64, 1024, device=device)
    y = torch.randint(0, 10, (64,), device=device)
    with torch.autocast(device, dtype=torch.bfloat16):
        out = model(x)
        loss = loss_fn(out, y)
    opt.zero_grad(set_to_none=True)
    loss.backward()
    opt.step()
    if step % 10 == 0:
        print(step, loss.item())
```

Watch `rocm-smi` in another shell while this runs — utilisation should
be well above zero.

## Apple Silicon — PyTorch with MPS

### Install

The standard CPU wheels include the MPS backend on macOS:

```bash
python3 -m venv ~/.venvs/torch-mps
source ~/.venvs/torch-mps/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio
```

### Verify

```python
import torch

print("MPS available:", torch.backends.mps.is_available())
print("MPS built:    ", torch.backends.mps.is_built())

x = torch.randn(4096, 4096, device="mps")
y = torch.randn(4096, 4096, device="mps")
z = (x @ y).sum().item()
print("Result OK:", z)
```

While the matmul runs, `sudo powermetrics --samplers gpu_power -i 1000`
should show GPU power increasing.

### MPS gotchas

- Some ops still fall back to CPU. Set
  `PYTORCH_ENABLE_MPS_FALLBACK=1` if you want PyTorch to fall back to
  CPU silently instead of raising; otherwise the error tells you which
  op is missing.
- `float64` is not supported on MPS. Cast to `float32` before sending
  tensors to the device.
- `bf16` support has improved across recent PyTorch releases — verify
  with `torch.tensor([1.0], dtype=torch.bfloat16, device="mps")` if you
  intend to use it.

## Portable device-selection pattern

A single block that works on both targets and on CPU:

```python
import torch

def pick_device() -> str:
    if torch.cuda.is_available():    # ROCm (MS-S1 MAX) or CUDA
        return "cuda"
    if torch.backends.mps.is_available():  # Apple Silicon
        return "mps"
    return "cpu"

device = pick_device()
print("Using:", device)
```

## See also

- [PyTorch get-started page](https://pytorch.org/get-started/locally/)
- [ROCm Installation](../gpu/rocm-installation.md)
- [Memory Configuration](../gpu/memory-configuration.md)
- [Inference Engines](../inference-engines/index.md) - if you only
  need inference, llama.cpp/Ollama are simpler than running PyTorch
  directly
