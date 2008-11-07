#!/usr/bin/env python

#
# Author: David Woolford (woolford@bcm.edu)
# Copyright (c) 2000-2006 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

import PyQt4
from PyQt4 import QtCore, QtGui, QtOpenGL
from PyQt4.QtCore import Qt
import os
import re
from EMAN2 import *
from emimage2d import EMImage2DModule
from emapplication import EMStandAloneApplication, EMQtWidgetModule
from EMAN2db import EMAN2DB
from emplot2d import EMPlot2DModule
#from boxertools import TrimSwarmAutoBoxer


class EMSelectorDialog(QtGui.QDialog):
	def __init__(self,target,application):
		QtGui.QDialog.__init__(self,None)
		self.setFocusPolicy(Qt.StrongFocus)
		self.application=application
		self.target=target
		
		self.db_listing = EMBDBListing(self)
		self.dir_listing = EMDirectoryListing(self)
		
		self.hbl = QtGui.QVBoxLayout(self)
		self.hbl.setMargin(0)
		self.hbl.setSpacing(6)
		self.hbl.setObjectName("hbl")
	
		self.list_hdl = QtGui.QHBoxLayout()
		
		self.__init_icons()
		
		self.__init_filter_combo()
		
		self.first_list_widget = QtGui.QListWidget(None)
		self.starting_directory = os.getcwd()
		
		self.selections = []
		self.current_list_widget = None
		self.lock = True
		self.list_widgets = []
		self.list_widget_data= [] # entries should be tuples containing (current folder item)
		self.__add_list_widget(self.first_list_widget)
		self.__add_list_widget()
		self.__add_list_widget()
		
		self.__load_directory_data(self.starting_directory,self.first_list_widget)
		#self.first_list_widget.setCurrentRow(-1)
		
		self.hbl.addLayout(self.list_hdl)

		self.bottom_hbl = QtGui.QHBoxLayout()
		self.bottom_hbl.addWidget(self.filter_text,0)
		self.bottom_hbl.addWidget(self.filter_combo,1)
		self.__init_buttons()
		self.bottom_hbl.addWidget(self.cancel_button,0)
		self.bottom_hbl.addWidget(self.ok_button,0)
		self.hbl.addLayout(self.bottom_hbl)
		self.gl_image_preview = None
		
		self.bottom_hbl2 = QtGui.QHBoxLayout()
		self.__init_preview_options()
		self.bottom_hbl2.addWidget(self.preview_options,0)
		self.hbl.addLayout(self.bottom_hbl2)
		
		self.__init__force_2d_tb()
		self.__init__force_plot_tb()
		self.bottom_hbl2.addWidget(self.force_2d,0)
		self.bottom_hbl2.addWidget(self.force_plot,0)
		
		self.bottom_hbl3 = QtGui.QHBoxLayout()
		self.__init_plot_options()
		self.bottom_hbl3.addWidget(self.replace,0)
		self.bottom_hbl3.addWidget(self.include,0)
		
		#self.hbl.addLayout(self.bottom_hbl3)
		
		self.groupbox = QtGui.QGroupBox("Plot/3D options")
		self.groupbox.setLayout(self.bottom_hbl3)
		
		
		self.bottom_hbl2.addWidget(self.groupbox)
		
		self.resize(480,480)
		
		self.lock = False
		
		self.paint_events = 0
		
	def get_desktop_hint(self):
		return "dialog"
		
	def set_application(self,app):
		self.application = app
		
	def __init_icons(self):
		self.setWindowIcon(QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/display_icon.png"))
		self.folder_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/Folder.png")
		self.folder_files_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/FolderFiles.png")
		self.file_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/File.png")
		self.database_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/database.png")
		self.key_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/Key.png")
		self.basic_python_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/boxhabanosclose.png")
		self.dict_python_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/Bag.png")
		self.ab_refboxes_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/black_box.png")
		self.ab_manboxes_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/black_box.png")
		self.ab_autoboxes_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/green_boxes.png")
		self.emdata_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/single_image.png")
		self.emdata_3d_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/single_image_3d.png")
		self.emdata_matrix_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/multiple_images.png")
		self.plot_icon = QtGui.QIcon(os.getenv("EMAN2DIR")+"/images/plot.png")

	def __init_plot_options(self):
		self.replace = QtGui.QRadioButton("Replace")
		self.include = QtGui.QRadioButton("Include")
		self.include.setChecked(True)
	
	#def __init_3d_options(self):
		#self.threed_options_label = QtGui.QLabel("3D options:",self)
		#self.replace_3d = QtGui.QCheckBox("Replace")
		#self.include_3d = QtGui.QCheckBox("Include")
		#self.include_3d.setChecked(True)

	def __init_preview_options(self):
		
		self.preview_options = QtGui.QComboBox(self)
		self.preview_options.addItem("No preview")
		self.preview_options.addItem("Single preview")
		self.preview_options.addItem("Multi preview")
		self.preview_options.setCurrentIndex(1)
		
		QtCore.QObject.connect(self.preview_options, QtCore.SIGNAL("currentIndexChanged(QString)"), self.preview_options_changed)
	
	def preview_options_changed(self,qstring):
		if str(qstring) == "Single preview":
			self.groupbox.setEnabled(True)
		else:
			self.groupbox.setEnabled(False)
			
		if str(qstring) == "No preview":
			self.force_2d.setEnabled(False)
			self.force_plot.setEnabled(False)
		else:
			self.force_2d.setEnabled(True)
			self.force_plot.setEnabled(True)
	
	def previews_allowed(self):
		return str(self.preview_options.currentText()) != "No preview"
	
	def single_preview_only(self):
		return str(self.preview_options.currentText()) == "Single preview"
	
	def __init_buttons(self):
		self.ok_button = QtGui.QPushButton("Ok")
		self.ok_button.adjustSize()
		
		self.cancel_button = QtGui.QPushButton("Cancel")
		self.cancel_button.adjustSize()
	
		QtCore.QObject.connect(self.ok_button, QtCore.SIGNAL("clicked(bool)"),self.ok_button_clicked)
		QtCore.QObject.connect(self.cancel_button, QtCore.SIGNAL("clicked(bool)"),self.cancel_button_clicked)
	
	def __init__force_2d_tb(self):
		self.force_2d = QtGui.QCheckBox("Force 2D")
		self.force_2d.setChecked(False)
		
		QtCore.QObject.connect(self.force_2d, QtCore.SIGNAL("clicked(bool)"),self.force_2d_clicked)
		
	def __init__force_plot_tb(self):
		self.force_plot = QtGui.QCheckBox("Force plot")
		self.force_plot.setChecked(False)
		
		QtCore.QObject.connect(self.force_plot, QtCore.SIGNAL("clicked(bool)"),self.force_plot_clicked)
	
	def force_2d_clicked(self):
		self.force_clicked(self.force_2d)
		
	def force_plot_clicked(self):
		self.force_clicked(self.force_plot)
	
	def force_clicked(self,f):
		
		if self.current_force == None:
			self.current_force = f
		elif f == self.current_force:
			self.current_force = None
			return
		else:
			self.current_force.setChecked(False)
			self.current_force = f
		
	
	def single_preview_clicked(self,bool):
		pass
		#print "not supported"
	
	def cancel_button_clicked(self,bool):
		print "cancel"
	
	def ok_button_clicked(self,bool):
		self.emit(QtCore.SIGNAL("done"),self.selections)
		
	def __init_filter_combo(self):
		self.filter_text = QtGui.QLabel("Filter:",self)
		self.filter_combo = QtGui.QComboBox(None)
		self.filter_combo.addItem("EM types")
		self.filter_combo.addItem("Databases") # this doesn't really do anything
		self.filter_combo.addItem("*.mrc,*.hdf,*.img")
		self.filter_combo.addItem("*.*")
		self.filter_combo.addItem("*")
		self.filter_combo.setEditable(True)
	
		QtCore.QObject.connect(self.filter_combo, QtCore.SIGNAL("currentIndexChanged(int)"),self.filter_index_changed)
		QtCore.QObject.connect(self.filter_combo, QtCore.SIGNAL("currentIndexChanged(QString&)"),self.filter_index_changed)

	def filter_index_changed(self):
		self.__redo_list_widget_contents()
	
	def __redo_list_widget_contents(self):
		self.lock = True
		directory = self.starting_directory+"/"
		for i,data in  enumerate(self.list_widget_data):
			
			if data != None:d = str(data.text())
			old_row = self.list_widgets[i].currentRow()
			self.__load_directory_data(directory,self.list_widgets[i])
			self.list_widget_data[i] = self.list_widgets[i].item(old_row)
			if data == None: return
			else:
				directory += '/' + d
	
		self.lock = False
	def __add_list_widget(self, list_widget = None):
		if list_widget == None:	list_widget = QtGui.QListWidget(None)
		
		list_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		list_widget.setMouseTracking(True)	
		self.list_widgets.append(list_widget)
		self.list_hdl.addWidget(list_widget)
		self.list_widget_data.append(None)
		
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("itemDoubleClicked(QListWidgetItem*)"),self.list_widget_dclicked)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("itemPressed(QListWidgetItem*)"),self.list_widget_clicked)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("currentRowChanged (int)"),self.list_widget_row_changed)
		#QtCore.QObject.connect(list_widget, QtCore.SIGNAL("paintEvent (int)"),self.list_widget_row_changed)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("itemEntered(QListWidgetItem*)"),self.list_widget_item_entered)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("currentItemChanged(QListWidgetItem*,QListWidgetItem*)"),self.list_widget_current_changed)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("itemChanged(QListWidgetItem*)"),self.list_widget_item_changed)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("itemActivated(QListWidgetItem*)"),self.list_widget_item_activated)
		#QtCore.QObject.connect(list_widget, QtCore.SIGNAL("activated(QModelIndex)"),self.activated)
		QtCore.QObject.connect(list_widget, QtCore.SIGNAL("selectionChanged(QItemSelection,QItemSelection)"),self.selection_changed)
		
	def __go_back_a_directory(self):
		self.lock = True
		new_dir = self.starting_directory[0:self.starting_directory.rfind('/')]
		#if  self.db_listing.responsible_for(new_dir):
			#new_dir = self.db_listing.
		#print "going back a directory",new_dir
		#if not os.access(new_dir,os.R_OK):
			#print "can't go up a directory, don't have read permission"
			#return
		self.starting_directory = new_dir
		for j in range(0,len(self.list_widgets)):
			self.list_widgets[j].clear()
			self.list_widget_data[j] = None
		self.__load_directory_data(self.starting_directory,self.first_list_widget)
		#self.hide_preview()
		self.lock = False
		
	def __go_forward_a_directory(self):
		self.lock = True
		self.starting_directory = self.starting_directory + '/' + str(self.list_widget_data[0].text())
		
		directory = self.starting_directory 
		for i in range(len(self.list_widgets)-1):
			items = []
			old_row = self.list_widgets[i+1].currentRow()
			n = self.list_widgets[i+1].count()
			for j in range(n-1,-1,-1):
				items.append(self.list_widgets[i+1].takeItem(j))
				
			self.list_widgets[i].clear()	
			for k in items:
				self.list_widgets[i].insertItem(0,k)
			
			self.list_widgets[i].setCurrentRow(old_row)
			
			self.list_widget_data[i] = self.list_widgets[i].item(old_row)
			directory += '/' + str(self.list_widget_data[i].text())
		
		
		a = EMSelectionListItem("../",None)
		a.type_of_me = "go up a directory"
		self.list_widgets[0].insertItem(0,a)
		
		self.lock = False
		#self.hide_preview()
		
	def selection_changed(self,item1,item2):
		pass
		
	def __update_selections(self):
		'''
		Makes the list of currently selected files accurate and up to date. Called when
		something has been clicked in a a list widget
		'''
		
		# get the directory 
		directory = self.starting_directory+"/"
		idx = 0
		for i,list_widget in enumerate(self.list_widgets):
			if list_widget == self.current_list_widget: 
				break
			directory += str(self.list_widget_data[i].text()) + "/"
		else:
			print "no list widget has focus?"
			return
		
		# now make the list of selections accurate
		self.selections = []
		for a in self.current_list_widget.selectedItems():
			file = directory+str(a.text())
			if self.__is_previewable(a): self.selections.append(file)
		
		# if there are no selections then close the preview
		#if len(self.selections) == 0:
			#self.hide_preview()
	
	def hide_preview(self):
		if self.gl_image_preview  != None:
			self.application.hide_specific(self.gl_image_preview)
	
	def list_widget_item_activated(self,item):
		pass
		
	
	def list_widget_item_changed(self,item):
		pass
	
	def list_widget_current_changed(self,item1,item2):
		pass
		
	def list_widget_item_entered(self,item):
		self.current_list_widget = item.listWidget()

	def list_widget_row_changed(self,i):
		return
	
	def keyPressEvent(self,event):
		pass
	
	def list_widget_clicked(self,item):
		if self.lock : return
		if self.current_list_widget == None: return

		self.__update_selections()

		if item == None: return
		
		
		
		if item.text() == "../": 
			self.__go_back_a_directory()
			return
		
		file = self.starting_directory+"/"
		directory = self.starting_directory+"/"
		idx = 0
		for i,list_widget in enumerate(self.list_widgets):
			if list_widget == self.current_list_widget: 
				idx = i
				file += str(item.text())
				break
			file += str(self.list_widget_data[i].text()) + "/"
			directory += str(self.list_widget_data[i].text()) + "/"
		else:
			print "no list widget has focus?"
			return
		
		if self.previews_allowed() and self.set_preview(item):
			
			for i in range(idx+1,len(self.list_widgets)):
				self.list_widgets[i].clear()
				self.list_widget_data[i] = None
				
			if not self.check_preview_item_wants_to_list(item):
				print "nope"
				return
		
	
		n = len(self.list_widgets)-1
		if self.current_list_widget  == self.list_widgets[n]:
				self.list_widget_data[n] = item
				self.__go_forward_a_directory()
				self.__load_directory_data(file+'/',self.list_widgets[n],item)
				return

		if self.__load_directory_data(file,self.list_widgets[idx+1],item):
			#if old_item != None:
				#old_item.setBackgroundColor(QtGui.QColor(255,255,255))
			##item.setBackgroundColor(QtGui.QColor(64,190,0,63))	
			self.list_widget_data[idx] = item
			self.list_widget_data[idx+1] = None
			
		for i in range(idx+2,len(self.list_widgets)):
			self.list_widgets[i].clear()
			self.list_widget_data[i] = None
		
	def list_widget_dclicked(self,item):
		
		file = self.starting_directory+"/"
		for i,list_widget in enumerate(self.list_widgets):
			if item.listWidget() == list_widget:
				file += str(item.text())
				break
			file += str(self.list_widget_data[i].text()) + "/"
	
		
		if self.__is_previewable(item):
			print "Opening ", file
	
	def set_preview(self,item):
		
		if self.db_listing.do_preview(item):
			return True
		elif self.dir_listing.do_preview(item):
			return True
		
		return False
		
	def check_preview_item_wants_to_list(self,item):
		if self.db_listing.preview_item_wants_to_list(item):
			return True
		elif self.dir_listing.preview_item_wants_to_list(item):
			return True
		
		return False
	
	#def try_preview_plot(self,filename):		#preview = EMModuleFromFile(filename,app=self.application,force_2d=False,force_plot=True,old=self.browse_gl_preview)
		#if preview != self.browse_gl_preview:
			#if self.browse_gl_preview != None: self.browse_gl_preview.closeEvent(None):
				#self.browse_gl_preview = preview

	
	def preview_plot(self,filename):
		if self.single_preview_only():
			if not isinstance(self.gl_image_preview,EMPlot2DModule):
				if self.gl_image_preview != None: self.application.close_specific(self.gl_image_preview)
				self.gl_image_preview = EMPlot2DModule(self.application)
	
			self.gl_image_preview.set_data_from_file(filename,self.replace.isChecked())
			self.application.show_specific(self.gl_image_preview)
			self.gl_image_preview.updateGL()
			
		else:
			preview =EMPlot2DModule(self.application)
			preview.set_data_from_file(filename,self.replace.isChecked())
			self.application.show_specific(preview)
			
	def preview_data(self,a,filename=""):
		from emimage import EMImageModule
		if self.single_preview_only():
			
			f_2d = self.force_2d.isChecked()
			f_plot = self.force_plot.isChecked()
			preview = EMImageModule(data=a,app=self.application,force_2d=f_2d,force_plot=f_plot,old=self.gl_image_preview,filename=filename,replace=self.replace.isChecked())
			if preview != self.gl_image_preview:
				if self.gl_image_preview != None: self.application.close_specific(self.gl_image_preview)
				self.gl_image_preview = preview
	
			self.application.show_specific(self.gl_image_preview)
			try: self.gl_image_preview.optimally_resize()
			except: pass
					
			self.gl_image_preview.updateGL()
		else:
			f_2d = self.force_2d.isChecked()
			f_plot = self.force_plot.isChecked()
			preview = EMImageModule(data=a,app=self.application,force_2d=f_2d,force_plot=f_plot,filename=filename)
			self.application.show_specific(preview)
			preview.updateGL()
			
		self.application.setOverrideCursor(Qt.ArrowCursor)	
			
	#def preview_data(self,a,filename=""):
		#self.application.setOverrideCursor(Qt.BusyCursor)
		
		#if type(a) == list and len(a) == 1:
			#a = a[0]
			#data = []
			#if a.get_zsize() != 1:
				#for z in range(a.get_zsize()):
					#image = a.get_clip(Region(0,0,z,a.get_xsize(),a.get_ysize(),1))
					#data.append(image)
				#a = data
		
		#if self.single_preview.isChecked():
			#if self.gl_image_preview == None:
				#self.gl_image_preview = EMImage2DModule(application=self.application)
				#self.gl_image_preview.set_data(a,filename)
			#else:
				#self.gl_image_preview.set_data(a,filename,retain_current_settings=True)
				
			##self.gl_image_preview.set_file_name(f)
			#self.application.show_specific(self.gl_image_preview)
			#self.gl_image_preview.updateGL()
		#else:
			#preview = EMImage2DModule(application=self.application)
			#preview.set_data(a,filename)
			#self.application.show_specific(preview)
			#preview.updateGL()
			
		#self.application.setOverrideCursor(Qt.ArrowCursor)
		
	
	def get_file_filter(self):
		return str(self.filter_combo.currentText())
	
	def filter_strings(self,strings):
		
		filters = str(self.filter_combo.currentText()).split(",")
		
		for j,f in enumerate(filters):
			s = f.replace("*","\w*")
			s = s.replace(".","\.")
			filters[j] = s
		
		reg_exp = []
		for f in filters:
			reg_exp.append(re.compile(f))
		
		solution = []
		for s in strings:
			for r in reg_exp:
				if len(re.findall(r,s)) != 0:
					solution.append(s)
					break
					
		
		return solution
	
	def __is_previewable(self,item):
		#if  self.db_listing.responsible_for(file_name):
		if self.db_listing.is_previewable(item): return True 
		else: return self.dir_listing.is_previewable(item)
		
	def __is_non_empty_directory(self,s):
		'''
		Returns true if s is a non empty directory
		'''

		for root, dirs, files in os.walk(s):
			files = self.filter_strings(files)
			file_length = len(files)
			if file_length == 0: file_length = len(dirs)
		
			if file_length != 0: return True
			
			return False
	
	def __load_database_directory(self,database_name,list_widget):
		
		print "loading database directory",database_name
	
	
	def __load_directory_data(self,directory,list_widget,item=None):
		
		list_widget.clear()
		if (list_widget == self.list_widgets[0]):
			self.lock = True
			a = EMSelectionListItem("../",list_widget)
			a.type_of_me = "go up a directory"
			self.lock = False
			
		if item != None and item.type_of_me == "key_value":
			a = EMSelectionListItem(self.basic_python_icon,str(item.value),list_widget)
			a.type_of_me = "value"
			a.value = item.value
			return
		
		if self.db_listing.responsible_for(directory):
			if  self.db_listing.load_database_data(directory,list_widget): return True
			elif item != None and self.db_listing.load_image_metada(item,list_widget): return True
			elif self.db_listing.load_directory_data(directory,list_widget): return True
			elif self.db_listing.load_database_interrogation(directory,list_widget): return True
			
			else: return False
		else: 
			if item != None and self.dir_listing.load_image_metada(item,list_widget): return True
			else: return self.dir_listing.load_directory_data(directory,list_widget)
		
	def make_replacements(self,dirs,list_widget):
		self.db_listing.make_replacements(dirs,list_widget)


class EMDirectoryListing:
	def __init__(self,target):
		self.target = target
		
		self.emdata_mx = "directory_emdata_mx"
		self.emdata_3d = "directory_emdata_3d"
		self.emdata = "directory_emdata"
		self.emdata_mx_member = "directory_emdata_mx_member" # for individual images in mxs
		self.plot_data = "plot_data"
 		
		self.previewable_types = [self.emdata_mx,self.emdata_3d,self.emdata,self.emdata_mx_member,self.plot_data] # add any others as functionality grows
		self.threed_dim_limit = 128
		pass
	
	
	#if str(self.filter_combo.currentText()) != "EM types":
			#for s in strings:
				
		#else:
			
	def filter_strings(self,strings):
		
		filt = self.target.get_file_filter()
		if filt == "EM types": 	return strings # this is a bit of hack unfortunately
		
		filters = filt.split(",")

		for j,f in enumerate(filters):
			s = f.replace("*","\w*")
			s = s.replace(".","\.")
			filters[j] = s
		
		reg_exp = []
		for f in filters:
			reg_exp.append(re.compile(f))
		
		solution = []
		for s in strings:
			for r in reg_exp:
				if len(re.findall(r,s)) != 0:
					solution.append(s)
					break
					
		
		return solution
	
	def load_directory_data(self,directory,list_widget):
		e = EMData()
		read_header_only = True
		plot = EMPlot2DModule()
		for root, dirs, files in os.walk(directory):
			files = self.filter_strings(files)
			filt = self.target.get_file_filter()
			
			dirs.sort()
			files.sort()
			 
			self.target.make_replacements(dirs,list_widget)
			 
			for i in dirs:
				if i[0] == '.': continue
				
				file_length = 0
				for r, d, f in os.walk(directory+"/"+i):
					f = self.filter_strings(f)
					file_length = len(f)
					if file_length == 0: file_length = len(d)
					break
				if file_length != 0:
					a = EMSelectionListItem(self.target.folder_files_icon,i,list_widget)
					a.type_of_me = "directory_file"
				else:
					a = EMSelectionListItem(self.target.folder_icon,i,list_widget)
					type_of_me = "directory"
				
			#for i,file in enumerate(files):
				#if file[0] == '.': continue
				#if get_file_tag(file) == "bdb":
					#a = EMSelectionListItem(self.database_icon,file,list_widget)
					#files.pop(i)
					
			for file in files:
				if file[0] == '.': continue
				if file[-1] == '~': continue
				#print EMUtil.get_image_ext_type(Util.get_filename_ext((file)),get_file_tag(file)
				full_name = directory+"/"+file
				if EMUtil.get_image_ext_type(Util.get_filename_ext(file)) != IMAGE_UNKNOWN:
					try:
						if EMUtil.get_image_count(full_name) > 1:
							a = EMSelectionListItem(self.target.emdata_matrix_icon,file,list_widget)
							a.type_of_me = self.emdata_mx
							a.full_path = full_name
						else:
							e.read_image(full_name,0, read_header_only)
							if e.get_zsize() > 1:
								a = EMSelectionListItem(self.target.emdata_3d_icon,file,list_widget)
								a.type_of_me = self.emdata_3d 
								a.full_path = full_name
							else:
								a = EMSelectionListItem(self.target.emdata_icon,file,list_widget)
								a.type_of_me = self.emdata 
								a.full_path = full_name
						
					except:
						a = EMSelectionListItem(self.target.file_icon,file,list_widget) # this happens when files are corrupted	
						a.type_of_me = "regular_file"
				
				elif plot.is_file_readable(full_name):
					a = EMSelectionListItem(self.target.plot_icon,file,list_widget)
					a.type_of_me = self.plot_data
					a.full_path = full_name
				else:
					if filt != "EM types":
						a = EMSelectionListItem(self.target.file_icon,file,list_widget)
						a.type_of_me = "regular_file"
						

			return True
			
		return False
	
	def do_preview(self,item):
		
		#if not os.path.isfile(item.full_path): return False
		
		if item.type_of_me == self.emdata_3d or item.type_of_me == self.emdata:
			self.target.preview_data(EMData(item.full_path),item.full_path)
			return True
		elif item.type_of_me == self.emdata_mx:
			# there is an inconsistency here seeing as size considerations are 
			a=EMData.read_images(item.full_path)
			self.target.preview_data(a,item.full_path)
			return True
		elif item.type_of_me == self.emdata_mx_member:
			# there is an inconsistency here seeing as size considerations are 
			a=EMData(item.full_path,item.idx)
			self.target.preview_data(a,item.full_path)
			return True
		elif item.type_of_me == self.plot_data:
			# there is an inconsistency here seeing as size considerations are 
			self.target.preview_plot(item.full_path)
			return True
		#else:
			
			#self.target.preview
		else: return False
	
	def load_image_metada(self,item,list_widget):
		if item.type_of_me in [self.emdata_3d, self.emdata,self.emdata_mx_member]:
			data = self.get_emdata_header(item)
			keys = data.keys()
			keys.sort() # alphabetical order
			for k in keys:
				v = data[k]
				a = EMSelectionListItem(self.target.basic_python_icon,str(k)+":"+str(v),list_widget)
				a.type_of_me = "key_value"
				a.key = k
				a.value = v
		
			return True
		elif item.type_of_me == self.emdata_mx:
			for i in range(EMUtil.get_image_count(item.full_path)):
				a = EMSelectionListItem(self.target.emdata_icon,str(i),list_widget)
				a.type_of_me = self.emdata_mx_member
				a.full_path = item.full_path
				a.idx = i
				
			return True
				
				
		return False
	
	def get_emdata_header(self,item):
		
		read_header_only = True
		e = EMData()
		if item.type_of_me in [self.emdata_3d, self.emdata]:
			e.read_image(item.full_path,0, read_header_only)
			return e.get_attr_dict()
		elif item.type_of_me == self.emdata_mx_member:
			e.read_image(item.full_path,item.idx, read_header_only)
			return e.get_attr_dict()
		else: return None
			
		
	def is_previewable(self,item):
		if item.type_of_me in self.previewable_types: return True
		else: return False
		
	def preview_item_wants_to_list(self,item):
		if item.type_of_me in self.previewable_types: return True
		else: return False

	#def is_previewable(self,file_or_folder):
		## this may not be strictly correct, seeing as if it's a file it will return true
		#return os.path.isfile(file_or_folder)
		

class EMBDBListing:
	def __init__(self,target):
		self.target = target
		self.directory_replacements = {"EMAN2DB":"bdb"}
	
		self.db_mx = "database_emdata_mx"
		self.emdata_3d_entry = "database_emdata_3d_entry"
		self.emdata_entry = "database_emdata_entry"
		self.db_dict_emdata_entry = "database_dictionary_emdata"
		
		self.previewable_types = [self.db_mx,self.emdata_3d_entry,self.emdata_entry,self.db_dict_emdata_entry] # add any others as functionality grows
	
	def responsible_for(self,file_or_folder):
		real_name = self.convert_to_absolute_path(file_or_folder)
		#print file_or_folder,real_name
		split = real_name.split('/')
		split.reverse() # this probably makes things faster
		for s in split:
			if s in self.directory_replacements.keys() or (len(s) > 4 and s[-4:] == ".bdb"): return True 
	
		return False
	
	def make_replacements(self,dirs,list_widget):
		rm = []
		for i,directory in enumerate(dirs):
			d = remove_directories_from_name(directory)
			
			if d in self.directory_replacements.keys():
				a = EMSelectionListItem(self.target.database_icon,self.directory_replacements[d],list_widget)
				rm.append(i)
				a.type_of_me = "regular"
		
		rm.reverse()
		for r in rm:
			dirs.pop(r)
	
	def convert_to_absolute_path(self,file_or_folder):
		ret = file_or_folder
		found = False
		for dir_rep in self.directory_replacements.items():
			if ret.find('/'+dir_rep[1]) != -1:
				ret = ret.replace('/'+dir_rep[1],'/'+dir_rep[0])
				found = True
		if not found: return ret
		if (not os.path.isdir(ret)) and (not os.path.isfile(ret)):
			if ret[-1] == "/": ret = ret[:-1]
			ret += ".bdb"
			
		return ret
			
	def is_database_directory(self,directory):
		if remove_directories_from_name(directory) in self.directory_replacements.values(): return True
		else: return False

	def load_directory_data(self,directory,list_widget):
		
		'''
		Displays the file/folder information in the directory /home/someonone/data/EMAN2DB
		this will typically consist of .bdb (database) files, but may contain folders and other
		EMAN2DB directories.
		
		At the moment I have only written the code so that it supports the interrogation of the .bdb
		files, and am displaying the other folders only as a I reminder that they need to be dealt with
		'''
		if not remove_directories_from_name(directory) in self.directory_replacements.values():
			 return False

		real_directory = self.convert_to_absolute_path(directory)
		for root, dirs, files in os.walk(real_directory):
			files.sort()
			dirs.sort()
			
			for i in dirs:
				if i[0] == '.': continue
				
				if i == "EMAN2DB":
					a = EMSelectionListItem(self.target.database_icon,"bdb",list_widget) # this is something we do not wish to support
					a.type_of_me = "unwanted"
					continue
			
				file_length = 0
				for r, d, f in os.walk(real_directory+"/"+i):
					file_length = len(f)
					if file_length == 0: file_length = len(d)
					break
					
				if file_length != 0:
					a = EMSelectionListItem(self.target.folder_files_icon,i,list_widget)
					a.type_of_me = "directory_file"
					#a.full_path = real_directory
				else:
					a = EMSelectionListItem(self.target.folder_icon,i,list_widget)
					a.type_of_me = "directory"
					a.full_path = real_directory
				
			for file in files:
				if file[len(file)-3:] == "bdb":
					f = file.rpartition(".bdb")
					db_directory = self.get_emdatabase_directory(real_directory)
					DB = EMAN2DB.open_db(db_directory)
					DB.open_dict(f[0])
					if DB[f[0]].has_key("maxrec"):
						n = DB[f[0]]["maxrec"]
						if n > 1:
							a = EMSelectionListItem(self.target.emdata_matrix_icon,f[0],list_widget)
							a.type_of_me = self.db_mx
							a.database_directory = db_directory
							a.database = f[0]
						else:
							a = EMSelectionListItem(self.target.database_icon,f[0],list_widget)
							a.type_of_me = "regular"
							#data = DB[f[0]].get_header(0)
							#if data["nz"] > 1:
								
							#else:
								
							#print data
						
					else:
						a = EMSelectionListItem(self.target.database_icon,f[0],list_widget)
						a.type_of_me = "regular"
				#else:
					#a = EMSelectionListItem(self.target.key_icon,file,list_widget)
				
			return True
				
		return False

	def is_database_file(self,file_name):
		file = self.convert_to_absolute_path(file_name)
		if len(file) > 4 and file[-4:] == ".bdb":
			if self.get_last_directory(file) == "EMAN2DB":
				if file_exists(file):
					return True
			
		return False

	def load_database_data(self,directory,list_widget):
		
		if not self.is_database_file(directory): 
			return False
		
		file = self.convert_to_absolute_path(directory)
 
		db_directory = self.get_emdatabase_directory(file)
		DB = EMAN2DB.open_db(db_directory)
		
		
		#print "the database directory is",db_directory
		key = remove_directories_from_name(file)
		key = strip_file_tag(key)
		DB.open_dict(key)
		
		list_widget.clear()
		items = DB[key]
		keys = items.keys()
		keys.sort() # puts them alphabetical order
		for k in keys:
			if k == '': continue
			_type =items.item_type(k)
			if _type == dict:
				a = EMSelectionListItem(self.target.database_icon,str(k),list_widget)
				a.type_of_me = "database_dict"
			elif _type == EMData:
				data = items.get_header(k)
				if data["nz"] > 1:
					a = EMSelectionListItem(self.target.emdata_3d_icon,str(k),list_widget)
					a.type_of_me = self.emdata_3d_entry
					a.database_directory = db_directory
					a.database = key
					a.database_key = k
				else:
					a = EMSelectionListItem(self.target.emdata_icon,str(k),list_widget)
					a.type_of_me = self.emdata_entry
					a.database_directory = db_directory
					a.database = key
					a.database_key = k
			else:
				#if type(i) in [str,float,int,tuple,list,bool]:
				v = items[k]
				a = EMSelectionListItem(self.target.basic_python_icon,str(k)+":"+str(v),list_widget)
				a.type_of_me = "key_value"
				a.key = k
				a.value = v
		return True
				
	
	def get_last_directory(self,file):
		idx1 = file.rfind('/')
		if idx1 > 0:
			ret = file[0:idx1]
		else: return ret
		
		idx2 = ret.rfind('/')
		if idx2 > 0:
			ret = ret[idx2+1:]
		
		return ret
		
	def get_emdatabase_directory(self,file):
		'''
		Get the database where EMAN2DB should be opening in order to open the given file
		e.g. if db path is /home/someone/work/EMAN2DB/data.bdb will return /home/someone/work
		'''
		
		idx1 = file.find("EMAN2DB")
		if idx1 > 0:
			return file[0:idx1]
		else: return None
		
	
	def load_image_metada(self,item,list_widget):
		if item.type_of_me in [self.emdata_3d_entry,self.emdata_entry,self.db_dict_emdata_entry]:
			data = self.get_emdata_header(item)
			data = self.get_emdata_header(item)
			keys = data.keys()
			keys.sort() # alphabetical order
			for k in keys:
				v = data[k]
				a = EMSelectionListItem(self.target.basic_python_icon,str(k)+":"+str(v),list_widget)
				a.type_of_me = "key_value"
				a.key = k
				a.value = v
				
			return True
			
		return False
		
	
	def load_database_interrogation(self,file_name,list_widget):
		split = file_name.split('/')
		
		rm = []
		for i,s in enumerate(split):
			if len(s) == 0: rm.append(i)
		
		rm.reverse()
		for k in rm: split.pop(k)
		
		if len(split) > 2 : # must atleast have EMAN2DB/something.bdb/dictionary
			split.reverse() # this probably makes things faster
			for j in range(2,len(split)):
				if split[j] in self.directory_replacements.values():
					break
			else:
				return False
			
			real_name = self.convert_to_absolute_path(file_name)
			db_directory = self.get_emdatabase_directory(real_name)

			#db_open_dict
			DB = EMAN2DB.open_db(db_directory)
			
			key = split[j-1]
			item_key = split[j-2]
			
			DB.open_dict(key)
			item = DB[key]
			
			#item = item[item_key]
			for ii in range(j-2,-1,-1):
				item = item[split[ii]]
			
			if type(item) == dict:
				keys = item.keys()
				keys.sort() # puts them alphabetical order
				for k in keys:
					i = item[k]
					if k == "auto_boxes":
						a = EMSelectionListItem(self.target.ab_autoboxes_icon,str(k),list_widget)
						a.type_of_me = "auto_boxes"
					elif k == "reference_boxes":
						a = EMSelectionListItem(self.target.ab_autoboxes_icon,str(k),list_widget)
						a.type_of_me = "reference_boxes"
					elif k == "manual_boxes":
						a = EMSelectionListItem(self.target.ab_autoboxes_icon,str(k),list_widget)
						a.type_of_me = "manual_boxes"
					elif type(i) in [str,float,int,tuple,list,bool]:
						a = EMSelectionListItem(self.target.basic_python_icon,str(k),list_widget)
						a.type_of_me = "python_basic"
					elif type(i) == dict:
						a = EMSelectionListItem(self.target.dict_python_icon,str(k),list_widget)
						a.type_of_me = "python_dict"
					elif type(i) == EMData:
						a = EMSelectionListItem(self.target.emdata_icon,str(k),list_widget)
						a.type_of_me = self.db_dict_emdata_entry
						a.database_directory = db_directory
						a.database = key
						a.database_dictionary_keys = [split[jj] for jj in range(j-2,-1,-1)]
						a.database_dictionary_keys.append(k)
					else:
						a = EMSelectionListItem(self.target.basic_python_icon,str(k),list_widget)
						a.type_of_me = "python_basic"
			elif isinstance(item,EMData):
				print "this shouldn't happen"
				self.target.preview_data(item)
				return False
			else:
				a = EMSelectionListItem(self.target.basic_python_icon,str(item),list_widget)
				a.type_of_me = "python_basic"
			return True
				
		else: return False 
	
	#def is_previewable(self,file_name):
		#return self.do_preview(file_name,fake_it=True)
	
	def is_previewable(self,item):
		if item.type_of_me in self.previewable_types: return True 
	
	def preview_item_wants_to_list(self,item):
		'''
		Sometimes a previeable item will still be able to list information
		'''
		if item.type_of_me in self.previewable_types: return True
		else: return False
	
	def do_preview(self,item):
		#if not os.path.isfile(item.full_path): return False
		
		if item.type_of_me == self.db_mx:
			DB = EMAN2DB.open_db(item.database_directory)
			DB.open_dict(item.database)
			maxrec = DB[item.database]["maxrec"]
			data = []
			for i in range(maxrec):
				data.append(DB[item.database][i])
			self.target.preview_data(data)	
			return True
				
		elif item.type_of_me == self.emdata_3d_entry or item.type_of_me == self.emdata_entry:
			
			DB = EMAN2DB.open_db(item.database_directory)
			DB.open_dict(item.database)
			data = DB[item.database][item.database_key]
			self.target.preview_data(data)
			return True

		elif item.type_of_me == self.db_dict_emdata_entry:
			DB = EMAN2DB.open_db(item.database_directory)
			DB.open_dict(item.database)
			db = DB[item.database]
			for key in item.database_dictionary_keys:
				db = db[key]
				
			# db should now be an EMData
			self.target.preview_data(db)
			return True
		
		
		else: return False
		
	
	def get_emdata_header(self,item):

				
		if item.type_of_me == self.emdata_3d_entry or item.type_of_me == self.emdata_entry:
			
			DB = EMAN2DB.open_db(item.database_directory)
			DB.open_dict(item.database)
			return DB[item.database].get_header(item.database_key)

		elif item.type_of_me == self.db_dict_emdata_entry:
			#this is really inefficient seeing as the whole image has to be read
			DB = EMAN2DB.open_db(item.database_directory)
			DB.open_dict(item.database)
			db = DB[item.database]
			for key in item.database_dictionary_keys:
				db = db[key]
				
			return db.get_attr_dict()
			
		else: return None
	
	#def do_preview(self,file_name,fake_it=False):
		#split = file_name.split('/')
		
		#rm = []
		#for i,s in enumerate(split):
			#if len(s) == 0: rm.append(i)
		
		#rm.reverse()
		#for k in rm: split.pop(k)
		
		#if len(split) > 1 : # must atleast have EMAN2DB/something.bdb/dictionary
			#split.reverse() # this probably makes things faster
			#for j in range(1,len(split)):
				#if split[j] in self.directory_replacements.values():
					#break
			#else: return False
			
			#real_name = self.convert_to_absolute_path(file_name)
			#db_directory = self.get_emdatabase_directory(real_name)
			#DB = EMAN2DB.open_db(db_directory)
			
			#key = split[j-1]
			##item_key = split[j-2]
			
			
			##print key,item_key
			#DB.open_dict(key)
			#item = DB[key]
			#for ii in range(j-2,-1,-1):
				#for t in [type(split[ii]),float,int]:
					#try:
						#key = t(split[ii])
						#if item[key] != None: 
							#item = item[key]
							#break
					#except:
						#pass
			
			#if isinstance(item,EMData):
				#if not fake_it: self.target.preview_data(item)
				#return True
			
		#return False
			
	def load_database_variables(self,directory,list_widget):
		pass


class EMSelectionListItem(QtGui.QListWidgetItem):
	def __init__(self,a,b,c=None):
		if c != None:
			QtGui.QListWidgetItem.__init__(self,a,b,c)
		else:
			QtGui.QListWidgetItem.__init__(self,a,b)
	
		self.type_of_me = None # should be a string storing "emdata","emdata_matrix","emdata_3d", etc
	def set_type_of_me(self,type_of_me):
		self.type_of_me = type_of_me
		
	def get_type_of_me(self): return self.type_of_me
	

	
app = None
def on_done(string_list):
	print "on done"
	if len(string_list) != 0:
		for s in string_list:
			print s,
		print
	app.quit()


if __name__ == '__main__':
	em_app = EMStandAloneApplication()
	app = em_app
	dialog = EMSelectorDialog(None,em_app)
	em_qt_widget = EMQtWidgetModule(dialog,em_app)
	QtCore.QObject.connect(dialog,QtCore.SIGNAL("done"),on_done)
	em_app.show()
	em_app.execute()




