class Textures:
    def __init__(self, verts_rgb=None, *args, **kwargs):
        self.verts_rgb = verts_rgb


class TexturesVertex(Textures):
    pass


class TexturesUV(Textures):
    pass


class _MeshNamespace:
    TexturesVertex = TexturesVertex


mesh = _MeshNamespace()


def look_at_view_transform(*args, **kwargs):
    import torch

    return torch.eye(3).unsqueeze(0), torch.zeros(1, 3)


class FoVPerspectiveCameras:
    def __init__(self, *args, **kwargs):
        pass


class FoVOrthographicCameras:
    def __init__(self, *args, **kwargs):
        pass


class PointLights:
    def __init__(self, *args, **kwargs):
        pass


class DirectionalLights:
    def __init__(self, *args, **kwargs):
        pass


class Materials:
    def __init__(self, *args, **kwargs):
        pass


class RasterizationSettings:
    def __init__(self, *args, **kwargs):
        pass


class PointsRasterizationSettings:
    def __init__(self, *args, **kwargs):
        pass


class MeshRasterizer:
    def __init__(self, *args, **kwargs):
        pass


class PointsRasterizer:
    def __init__(self, *args, **kwargs):
        pass


class SoftPhongShader:
    def __init__(self, *args, **kwargs):
        pass


class HardPhongShader:
    def __init__(self, *args, **kwargs):
        pass


class MeshRenderer:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        raise RuntimeError("pytorch3d rendering is unavailable in layout-only mode.")


class PointsRenderer(MeshRenderer):
    pass


class PulsarPointsRenderer(MeshRenderer):
    pass


class AlphaCompositor:
    def __init__(self, *args, **kwargs):
        pass


class NormWeightedCompositor:
    def __init__(self, *args, **kwargs):
        pass
