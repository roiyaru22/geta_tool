# -*- coding: utf-8 -*-
from maya import OpenMayaUI as OpenMayaUI

import imp
try:
	imp.find_module('PySide2')
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *
	from PySide2.QtUiTools import QUiLoader
except ImportError:
	from PySide.QtGui import *
	from PySide.QtCore import *
	from PySide.QtUiTools import QUiLoader
try:
	import shiboken
except:
	import shiboken2 as shiboken

class Ui_MainWidget(QMainWindow):
	u"""
	PySideのウィンドウをMayaへ適応させるクラス
		:param: なし
		:return: なし
	"""
	def __init__(self):
		def getMayaWindow():
			u"""
			Mayaの前にウィンドウを表示するためのポインタを取得
				:param: なし
				:return: ポインタ
			"""
			Ptr = OpenMayaUI.MQtUtil.mainWindow()
			return shiboken.wrapInstance(long(Ptr), QWidget)

		QMainWindow.__init__(self, getMayaWindow())
		self.loader = QUiLoader()

	def uifile_loader(self, uifile_path):
		u"""
		.uiファイルをCentralWidgetに割り当てる関数
			:param uifile_path: 文字列 .uiファイルのフルパス
			:return: なし
		"""
		self.ui = self.loader.load(uifile_path)
		self.setCentralWidget(self.ui)
