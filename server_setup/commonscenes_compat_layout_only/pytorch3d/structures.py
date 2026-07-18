class Meshes:
    def __init__(self, verts=None, faces=None, textures=None):
        self._verts = verts or []
        self._faces = faces or []
        self.textures = textures

    def verts_list(self):
        return self._verts

    def faces_list(self):
        return self._faces

    def verts_normals_list(self):
        return self._verts


def join_meshes_as_scene(meshes):
    return meshes[0] if meshes else Meshes()


def join_meshes_as_batch(meshes):
    return meshes


class Pointclouds:
    def __init__(self, points=None, features=None):
        self.points = points or []
        self.features = features
