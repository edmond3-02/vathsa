# Virtual Asset Tesselator with a Highly Stretched Acronym --- VATHSA
# Author - Nathan Edmonds

import sys
from subprocess import check_output

from PySide2 import QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton, QLineEdit, QRadioButton, QStackedLayout
from PySide2.QtCore import Qt, QSize
from Vobject import Vobject

try:
	import FreeCAD
except ModuleNotFoundError:
	print('FreeCAD library not found. Please check the FREECADPATH variable in line 1 is correct')
	exit()

class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()

		self.min_width = 400
		self.min_height = 200

		self.in_file = ""
		self.out_file = ""
		self.out_format = ""

		self.tess_amt = 1.0
		self.linear_deflection = 0.1
		self.angular_deflection = 0.523599

		self.vertices = []
		self.face_indices = []
		self.face_normals = []

		self.vobjects = []

		self.initUI()

	def initUI(self):
		self.setWindowTitle('CAD to asset')
		self.setMinimumSize(QSize(self.min_width, self.min_height))

		layout = QVBoxLayout()

		# ### GUI FOR INPUT CAD FILE ###

		in_file_button = QPushButton("Select CAD file")
		in_file_button.clicked.connect(self.get_step_file)
		layout.addWidget(in_file_button)

		self.in_file_label = QLabel(self.in_file)
		layout.addWidget(self.in_file_label)

		# ### Tesselation type ###
		# Label
		tess_type_label = QLabel("Tesselation Type:")
		layout.addWidget(tess_type_label)

		# Shape tesselation method, Radio button
		self.shape_tesselation_rbutton = QRadioButton("Tesselation method")
		self.shape_tesselation_rbutton.clicked.connect(self.update_options_box)
		layout.addWidget(self.shape_tesselation_rbutton)
		self.shape_tesselation_rbutton.toggle()

		# Mesh from shape method, Radio button
		self.mesh_from_shape_rbutton = QRadioButton("Mesh from shape method")
		self.mesh_from_shape_rbutton.clicked.connect(self.update_options_box)
		layout.addWidget(self.mesh_from_shape_rbutton)

		# Widget with switchable layout
		self.switchable_layout = QStackedLayout()
		switchable_widget = QWidget()
		switchable_widget.setLayout(self.switchable_layout)
		layout.addWidget(switchable_widget)


		# ### Shape tesselation options ###
		shape_tesselation_widget = QWidget()
		shape_tesselation_layout = QHBoxLayout()
		shape_tesselation_widget.setLayout(shape_tesselation_layout)
		self.switchable_layout.addWidget(shape_tesselation_widget)

		# Label
		shape_tesselation_layout.addWidget(QLabel("Tesselation level:"), alignment=Qt.AlignLeft)

		# Line edit
		self.shape_tesselation_amt_box = QLineEdit()
		self.shape_tesselation_amt_box.setValidator(QtGui.QDoubleValidator())
		self.shape_tesselation_amt_box.setText("1.0")
		self.shape_tesselation_amt_box.editingFinished.connect(self.update_tesselation_value)

		# Add widget to layout
		shape_tesselation_layout.addWidget(self.shape_tesselation_amt_box)

		# ### Mesh from Shape ###
		mesh_from_shape_widget = QWidget()
		mesh_from_shape_layout = QVBoxLayout()
		mesh_from_shape_widget.setLayout(mesh_from_shape_layout)
		self.switchable_layout.addWidget(mesh_from_shape_widget)

		# # linear deflection # #
		linear_deflection_widget = QWidget()
		linear_deflection_layout = QHBoxLayout()
		linear_deflection_widget.setLayout(linear_deflection_layout)
		mesh_from_shape_layout.addWidget(linear_deflection_widget)

		# Label
		linear_deflection_layout.addWidget(QLabel("Linear Deflection:"), alignment=Qt.AlignLeft)

		# Line edit
		self.linear_deflection_box = QLineEdit()
		self.linear_deflection_box.setValidator(QtGui.QDoubleValidator())
		self.linear_deflection_box.setText("0.1")
		self.linear_deflection_box.editingFinished.connect(self.update_tesselation_value)
		# Add widget to layout
		linear_deflection_layout.addWidget(self.linear_deflection_box)

		# #  angular deflection # #
		angular_deflection_widget = QWidget()
		angular_deflection_layout = QHBoxLayout()
		angular_deflection_widget.setLayout(angular_deflection_layout)
		mesh_from_shape_layout.addWidget(angular_deflection_widget)

		# Label
		angular_deflection_layout.addWidget(QLabel("Angular Deflection:"), alignment=Qt.AlignLeft)

		# Line edit
		self.angular_deflection_box = QLineEdit()
		self.angular_deflection_box.setValidator(QtGui.QDoubleValidator())
		self.angular_deflection_box.setText("0.523599")
		self.angular_deflection_box.editingFinished.connect(self.update_tesselation_value)
		# Add widget to layout
		angular_deflection_layout.addWidget(self.angular_deflection_box)

		# ### Save button ###
		layout.addStretch()

		save_button = QPushButton("Save")
		save_button.setMaximumWidth(120)

		save_button.clicked.connect(self.get_destination_file)
		layout.addWidget(save_button, alignment=Qt.AlignRight)

		# ### MAIN APP LAYOUT ####

		self.container = QWidget()
		self.container.setLayout(layout)
		self.setCentralWidget(self.container)

	def update_options_box(self):
		if self.shape_tesselation_rbutton.isChecked():
			self.switchable_layout.setCurrentIndex(0)
		elif self.mesh_from_shape_rbutton.isChecked():
			self.switchable_layout.setCurrentIndex(1)

	def update_tesselation_value(self):
		self.tess_amt = float(self.shape_tesselation_amt_box.text())
		self.linear_deflection = float(self.linear_deflection_box.text())
		self.angular_deflection = float(self.angular_deflection_box.text())

	# ### GET STEP FILE ###
	def get_step_file(self):
		file_name, file_format = QFileDialog.getOpenFileName(self, 'Open STEP file', "", "STEP(*.step; *.stp);;All Files(*.*) ")

		# check if file selection was cancelled
		if file_name == "":
			return
		
		self.in_file = file_name
		self.in_file_label.setText(file_name)

	# ### GET DESTINATION FILE ###
	def get_destination_file(self):
		file_name, file_format = QFileDialog.getSaveFileName(self, 'Export file name/format', "", "OBJ(*.obj);;FBX(*.fbx);;All Files(*.*) ")

		# check if file selection was cancelled
		if file_name == "":
			return
		
		self.out_file = file_name
		self.out_format = file_format.split('(', 1)[0]

		self.save_file()

	# ### OUTPUT FILE ###
	def save_file(self):
		# choose tesselation method
		if self.shape_tesselation_rbutton.isChecked():
			self.shape_tesselate()
		elif self.mesh_from_shape_rbutton.isChecked():
			print("mesh from shape")
			self.mesh_from_shape()

		# select output file
		if self.out_format == 'FBX':
			self.save_fbx()
		elif self.out_format == 'OBJ':
			self.save_obj()

	# ### CONVERT TO FBX ###
	def save_fbx(self):
		print("FBX not yet implemented")

	def shape_tesselate(self):
		import Import
		Import.open(self.in_file, "Unnamed")
		doc = App.ActiveDocument

		self.clear_data()
		
		objects = doc.RootObjects

		for ob in objects:
			self.vobjects.append(self.recursive_tessellate(ob, 1))

		for v in self.vobjects:
			print(v.tostring())

		for ob in objects:
			if ob.TypeId[:4] == 'Part':
				shape = ob.Shape
				if shape.Faces:
					rawdata = shape.tessellate(self.tess_amt)
					for v in rawdata[0]:
						self.vertices.append(v)
					for f in rawdata[1]:
						self.face_indices.append(f)
						v1 = self.vertices[f[1]].sub(self.vertices[f[0]])
						v2 = self.vertices[f[2]].sub(self.vertices[f[0]])
						self.face_normals.append(v1.cross(v2))

		App.closeDocument("Unnamed")

	def recursive_tessellate(self, object, level):
		string = ""
		for i in range(level):
			string += "   "
		string += object.Label + " : " + object.TypeId

		# print(string)


		# make vobject
		vobject = Vobject(name=object.Label)

		if(object.TypeId == "App::Part"):
			for ob in object.Group:
				vobject.children.append(self.recursive_tessellate(ob, level + 1))
		# if(object.TypeId == "Part::Feature"):
		# 	print("    " + object.Label + "is a leaf node!")

		return vobject

	def mesh_from_shape(self):
		import Mesh, Part
		import MeshPart

		import Import
		Import.open(self.in_file, "Unnamed")
		doc = App.ActiveDocument

		self.clear_data()

		__doc__=App.ActiveDocument

		for __object__ in __doc__.Objects:
			__mesh__=__doc__.addObject("Mesh::Feature","Mesh")
			__part__=__doc__.getObject("Model")
			__shape__=Part.getShape(__part__,"")
			__mesh__.Mesh=MeshPart.meshFromShape(Shape=__shape__, LinearDeflection=self.linear_deflection, AngularDeflection=self.angular_deflection, Relative=False)

			# points
			points = __mesh__.Mesh.Points
			for point in points:
				self.vertices.append(point)
			# faces
			faces = __mesh__.Mesh.Facets
			for face in faces:
				self.face_indices.append(face.PointIndices)
				v1 = self.vertices[face.PointIndices[1]].Vector.sub(self.vertices[face.PointIndices[0]].Vector)
				v2 = self.vertices[face.PointIndices[2]].Vector.sub(self.vertices[face.PointIndices[0]].Vector)
				self.face_normals.append(v1.cross(v2))

		App.closeDocument("Unnamed")

	# ### CONVERT TO OBJ ####
	def save_obj(self):
		
		with open(self.out_file, "w") as f:
			for vert in self.vertices:
				f.write(f'v {vert.x} {vert.z} {vert.y}\n')
			for normal in self.face_normals:
				f.write(f'vn {normal.x} {normal.z} {normal.y}\n')
			face_normal_index = 1
			for face in self.face_indices:
				f.write(f'f {face[0] + 1}//{face_normal_index} {face[1] + 1}//{face_normal_index} {face[2] + 1}//{face_normal_index}\n')
				face_normal_index += 1

		self.clear_data()

	def clear_data(self):
		self.vertices = []
		self.face_indices = []
		self.face_normals = []


def main():
	app = QApplication(sys.argv)

	window = MainWindow()
	window.show()

	app.exec_()

if __name__=='__main__':
	main()