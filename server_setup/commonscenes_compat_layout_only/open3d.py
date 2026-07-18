"""Layout-only stub for CommonScenes smoke tests.

The CommonScenes evaluation script imports open3d at module import time, even
when visualization is disabled. This stub lets layout-only runs pass import
checks without installing the large Open3D wheel.
"""


class _MissingOpen3D:
    def __getattr__(self, name):
        raise RuntimeError(
            "open3d stub was used, but Open3D functionality was requested. "
            "Install open3d for visualization or mesh processing."
        )


geometry = _MissingOpen3D()
io = _MissingOpen3D()
utility = _MissingOpen3D()
visualization = _MissingOpen3D()
