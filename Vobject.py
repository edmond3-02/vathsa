class Vobject():
    def __init__(self, name="", verts=[], faces=[], normals=[]):
        self.name = name
        self.verts = verts
        self.faces = faces
        self.normals = normals
        self.children = []

    def tostring(self):
        return self.recursive_to_string(0)

    def recursive_to_string(self, level):
        string = ""
        for i in range(level):
            string += "   "
        string += self.name

        for child in self.children:
            string += "\n" + child.recursive_to_string(level + 1)

        return string