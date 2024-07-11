# Virtual Asset Tesselator with a Highly Stretched Acronym --- VATHSA
# Author - Nathan Edmonds

import os, sys
from subprocess import check_output
from pathlib import Path

from PySide2 import QtGui
from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog, QPushButton, QLineEdit, QRadioButton, QStackedLayout, QCheckBox, QTreeView, QAbstractItemView
from PySide2.QtCore import Qt, QSize
from Vobject import Vobject
from Vtreemodel import VTreeModel

try:
	sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
	import FbxCommon
	from fbx import *
except ImportError as e:
	print("Error: module FbxCommon and/or fbx failed to import.\n")
	print(e)
	sys.exit(1)

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

		self.verbose = False

		self.tess_amt = 1.0
		self.linear_deflection = 0.1
		self.angular_deflection = 0.523599

		self.vertices = []
		self.previous_indices = 0
		self.face_indices = []
		self.face_normals = []

		self.vobjects = []
		self.alt_vobjects = []

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
		self.shape_tesselation_rbutton = QRadioButton("Recursive method")
		self.shape_tesselation_rbutton.clicked.connect(self.update_options_box)
		layout.addWidget(self.shape_tesselation_rbutton)
		self.shape_tesselation_rbutton.toggle()

		# Mesh from shape method, Radio button
		self.mesh_from_shape_rbutton = QRadioButton("Single body method")
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

		# ### TREE ###

		self.view = QTreeView()
		self.view.setAlternatingRowColors(True)
		self.view.setSelectionBehavior(QAbstractItemView.SelectItems)
		self.view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.view.setAnimated(False)
		self.view.setAllColumnsShowFocus(True)

		layout.addWidget(self.view)

		headers = ["Name", "Tesselation level"]

		file = Path(__file__).parent / "default.txt"
		self.model = VTreeModel(headers, file.read_text(), self)

		if "-t" in sys.argv:
			QAbstractItemModelTester(self.model, self)
		self.view.setModel(self.model)
		self.view.expandAll()

		# for column in range(self.model.columnCount()):
		#	self.view.resizeColumnToContents(column)

		selection_model = self.view.selectionModel()

		# ### Save button ###
		layout.addStretch()

		output_widget = QWidget()
		output_layout = QHBoxLayout()
		output_widget.setLayout(output_layout)
		layout.addWidget(output_widget)

		self.center_pivot_box = QCheckBox("Force center of mass")
		self.center_pivot_box.setChecked(True)
		output_layout.addWidget(self.center_pivot_box)


		save_button = QPushButton("Save")
		save_button.setMaximumWidth(120)

		save_button.clicked.connect(self.get_destination_file)
		output_layout.addWidget(save_button, alignment=Qt.AlignRight)

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
		file_name, file_format = QFileDialog.getOpenFileName(self, 'Open STEP file', "./step_files", "STEP(*.step; *.stp);;All Files(*.*) ")

		# check if file selection was cancelled
		if file_name == "":
			return
		
		self.in_file = file_name
		self.in_file_label.setText(file_name)

		self.load_vobjects()
		print(self.vobjects[0].tostring())

	# ### GET DESTINATION FILE ###
	def get_destination_file(self):
		file_name, file_format = QFileDialog.getSaveFileName(self, 'Export file name/format', "./meshes", "FBX(*.fbx);;OBJ(*.obj);;All Files(*.*) ")

		# check if file selection was cancelled
		if file_name == "":
			return
		
		self.out_file = file_name
		self.out_format = file_format.split('(', 1)[0]

		self.save_file()

	# ### OUTPUT FILE ###
	def save_file(self):
		self.clear_data()

		# choose tesselation method
		if self.shape_tesselation_rbutton.isChecked():
			self.shape_tesselate()
		elif self.mesh_from_shape_rbutton.isChecked():
			self.mesh_from_shape()

	
		if self.verbose:
			for vob in self.vobjects:
				print(vob.tostring())

		# select output file
		if self.out_format == 'FBX':
			self.save_fbx()
		elif self.out_format == 'OBJ':
			self.save_obj()

	# ### CONVERT TO FBX ###
	def save_fbx(self):
		# Prepare the FBX SDK.
		(lSdkManager, lScene) = FbxCommon.InitializeSdkObjects()

		# Create the scene.
		lResult = self.create_scene(lSdkManager, lScene)

		if lResult == False:
			print("\n\nAn error occurred while creating the scene...\n")
			lSdkManager.Destroy()
			return

		# Save the scene.
		lResult = FbxCommon.SaveScene(lSdkManager, lScene, self.out_file)

		if lResult == False:
			print("\n\nAn error occurred while saving the scene...\n")
			
		lSdkManager.Destroy()
			
		return

	# ### CONVERT TO OBJ ####
	def save_obj(self):
		with open(self.out_file, "w") as f:
			for vert in self.vertices:
				f.write(f'v {vert.x} {vert.y} {vert.z}\n')
			for normal in self.face_normals:
				f.write(f'vn {normal.x} {normal.y} {normal.z}\n')
			face_normal_index = 1
			for face in self.face_indices:
				f.write(f'f {face[0] + 1}//{face_normal_index} {face[1] + 1}//{face_normal_index} {face[2] + 1}//{face_normal_index}\n')
				face_normal_index += 1

	def create_scene(self, sdk_manager, scene):
		lRootNode = scene.GetRootNode()

		for o in self.vobjects:
			lRootNode.AddChild(self.add_node(sdk_manager, o))

		lGlobalSettings = scene.GetGlobalSettings()
		
		return True

	def add_node(self, sdk_manager, vobject):
		node = self.make_node(sdk_manager, vobject)

		for child in vobject.children:
			node.AddChild(self.add_node(sdk_manager, child))

		return node

	def make_node(self, sdk_manager, vobject):
		lMesh = FbxMesh.Create(sdk_manager, vobject.name)

		verts = []
		lMesh.InitControlPoints(len(vobject.vertices))     
	
		index = 0
		for v in vobject.vertices:
			lMesh.SetControlPointAt(FbxVector4(v.x, v.y, v.z), index)
			index += 1

		lLayer = lMesh.GetLayer(0)
		if lLayer == None:
			lMesh.CreateLayer()
			lLayer = lMesh.GetLayer(0)

		lLayerElementNormal= FbxLayerElementNormal.Create(lMesh, "normals")
		lLayerElementNormal.SetMappingMode(FbxLayerElement.EMappingMode.eByPolygonVertex)
		lLayerElementNormal.SetReferenceMode(FbxLayerElement.EReferenceMode.eIndexToDirect)

		index = 0
		for f, n in zip(vobject.faces, vobject.normals):
			lMesh.BeginPolygon(-1, -1, False)

			for i in range(3):
				lMesh.AddPolygon(f[i])

			lMesh.EndPolygon()
			lLayerElementNormal.GetDirectArray().Add(FbxVector4(n.x, n.y, n.z))
			for i in range(3):
				lLayerElementNormal.GetIndexArray().Add(index)
			index += 1


		lLayer.SetNormals(lLayerElementNormal)

		lNode = FbxNode.Create(sdk_manager, vobject.name)
		lNode.SetNodeAttribute(lMesh)
		lNode.LclTranslation.Set(FbxDouble3(vobject.position.x, vobject.position.y, vobject.position.z))
		lNode.SetShadingMode(FbxNode.EShadingMode.eFlatShading)

		return lNode

	def shape_tesselate(self):
		import Import
		Import.open(self.in_file, "Unnamed")
		doc = App.ActiveDocument
		
		objects = doc.RootObjects

		for ob in objects:
			self.vobjects.append(self.recursive_tessellate(ob, 0))

		App.closeDocument("Unnamed")

	def recursive_tessellate(self, node, level):

		# make vobject
		vname = node.Label.replace(" ", "_")
		vobject = Vobject(name=vname, position=node.Placement.Base)

		string = ""
		for i in range(level):
			string += "  "
		string += vobject.name

		if(node.TypeId == "App::Part"):
			for child in node.Group:
				vobject.children.append(self.recursive_tessellate(child, level + 1))
		if(node.TypeId == "Part::Feature"):
			shape = node.Shape
			if shape.Faces:
				# use global values if the vobject tessellation amount is unchanged from 1
				tess_amt = self.tess_amt if vobject.tess_amt == "d" else vobject.tess_amt
				rawdata = shape.tessellate(tess_amt)
				for v in rawdata[0]:
					vobject.add_vertex(v)
					self.vertices.append(v)
				for f in rawdata[1]:
					vobject.faces.append(f)
					self.face_indices.append((f[0]+self.previous_indices, f[1]+self.previous_indices, f[2]+self.previous_indices))
					v1 = vobject.vertices[f[1]].sub(vobject.vertices[f[0]])
					v2 = vobject.vertices[f[2]].sub(vobject.vertices[f[0]])
					normal = v1.cross(v2).normalize()
					vobject.normals.append(normal)
					self.face_normals.append(normal)
				self.previous_indices = self.previous_indices + len(rawdata[1])
				if self.center_pivot_box.isChecked():
					vobject.center_pivot()

		return vobject

	def mesh_from_shape(self):
		import Mesh, Part
		import MeshPart

		import Import
		Import.open(self.in_file, "Unnamed")
		doc = App.ActiveDocument

		__doc__=App.ActiveDocument

		for __object__ in __doc__.RootObjects:
			vname = __object__.Label.replace(" ", "_")
			__mesh__=__doc__.addObject("Mesh::Feature", vname)
			__shape__=Part.getShape(__object__,"")
			__mesh__.Mesh=MeshPart.meshFromShape(Shape=__shape__, LinearDeflection=self.linear_deflection, AngularDeflection=self.angular_deflection, Relative=False)

			vobject = Vobject(name=vname, position=__object__.Placement.Base)

			# points
			points = __mesh__.Mesh.Points
			for point in points:
				self.vertices.append(point.Vector)
				vobject.add_vertex(point.Vector)
			# faces
			faces = __mesh__.Mesh.Facets
			for face in faces:
				self.face_indices.append(face.PointIndices)
				vobject.faces.append(face.PointIndices)
				v1 = self.vertices[face.PointIndices[1]].sub(self.vertices[face.PointIndices[0]])
				v2 = self.vertices[face.PointIndices[2]].sub(self.vertices[face.PointIndices[0]])
				normal = v1.cross(v2)
				if normal != FreeCAD.Vector (0.0, 0.0, 0.0):
					normal = normal.normalize()
				else:
					normal = FreeCAD.Vector(1.0, 0.0, 0.0)
				self.face_normals.append(normal)
				vobject.normals.append(normal)

			self.vobjects.append(vobject)

		App.closeDocument("Unnamed")

	def load_vobjects(self):
		import Import
		Import.open(self.in_file, "Unnamed")
		doc = App.ActiveDocument

		objects = doc.RootObjects

		for ob in objects:
			self.vobjects.append(self.recursive_load(ob))

		self.model.setup_model_data2(self.vobjects[0])
		
	def recursive_load(self, node):
		vname = node.Label.replace(" ", "_")
		vobject = Vobject(name=vname)
		vobject.part = node

		if(node.TypeId == "App::Part"):
			for child in node.Group:
				vobject.children.append(self.recursive_load(child))

		return vobject

	def clear_data(self):
		self.vertices = []
		self.previous_indices = 0
		self.face_indices = []
		self.face_normals = []

		self.vobjects = []
		self.alt_vobjects = []

def main():
	app = QApplication(sys.argv)

	window = MainWindow()
	window.show()

	app.exec_()

if __name__=='__main__':
	main()