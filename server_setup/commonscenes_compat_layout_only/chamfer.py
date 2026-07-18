"""Layout-only stub for CommonScenes Chamfer CUDA extension."""


def forward(*args, **kwargs):
    raise RuntimeError("Chamfer distance is unavailable in layout-only mode.")


def backward(*args, **kwargs):
    raise RuntimeError("Chamfer distance is unavailable in layout-only mode.")
