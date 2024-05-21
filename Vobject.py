class Vobject():
    def __init__(self, name="", position=(0,0,0), tess_amt=1.0):
        self.name = name
        self.position = position
        self.vertices = []
        self.faces = []
        self.normals = []
        self.children = []
        self.tess_amt = tess_amt
        self.min_face_ind = 1
        self.max_face_ind = 0

    def tostring(self):
        return self.recursive_to_string(0)

    def recursive_to_string(self, level):
        string = ""
        for i in range(level):
            string += "   "

        self.calc_min_max()
        string += self.name

        for child in self.children:
            string += "\n" + child.recursive_to_string(level + 1)

        return string

    def calc_min_max(self):
        for face in self.faces:
            for i in range(3):
                if face[i] < self.min_face_ind:
                    self.min_face_ind = face[i]
                if face[i] > self.max_face_ind:
                    self.max_face_ind = face[i]