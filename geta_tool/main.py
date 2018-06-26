# -*- coding: utf-8 -*-
import maya.cmds as cmds
import pymel.core as pm
import os
import copy

import imp
try:
	imp.find_module('PySide2')
	from PySide2.QtCore import *
	from PySide2.QtGui import *
	from PySide2.QtWidgets import *
except ImportError:
	from PySide.QtGui import *
	from PySide.QtCore import *
try:
	import shiboken
except:
	import shiboken2 as shiboken

# import /module
import module.constraints_locator as constraints_locator
reload(constraints_locator)
import module.PySide_custom.set_load_ui as set_load_ui
reload(set_load_ui)

class Ui_MainWidget(set_load_ui.Ui_MainWidget):
	u"""
	選択しているオブジェクトにロケータをコンストレインしたり、コンストレインを逆転させたりするツール
	作成したロケータや選択しているオブジェクトをリストに登録でき、選択しやすいようにしている
	Mayaの選択、削除からCallbackを受けて、UIの表示に反映する
	"""
	def __init__(self, parent=None):
		super(Ui_MainWidget, self).__init__()
		## フレームレスの設定
		self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
		self.__isDrag = False
		self.__startPos = QPoint(0, 0)

		## Mayaからリネームした時とUIからリネームしたときの処理が重複しないようにするフラグ
		self.fromListRenameFlug = True
		self.fromMayaRenameFlug = True

		## set_load_ui.Ui_MainWidgetクラスを継承して、uifile_loader関数を実行
		## uiファイルをCentralWidgetにセットしている
		## セットしているuiファイルの内容はself.uiに格納
		self.uifile_path = os.path.dirname(os.path.abspath(__file__)) + "/ui/gui.ui"
		self.uifile_loader(self.uifile_path)
		self.setGeometry(200, 300, 250, 410)
		self.setWindowTitle("GETA Tool")

		## ウィンドウの端を丸くする設定
		self.paletteUI()

		## モデルの設定
		self.model = QStandardItemModel()
		self.selModel = QItemSelectionModel(self.model)
		self.ui.list_locators.setModel(self.model)
		self.ui.list_locators.setSelectionModel(self.selModel)

		## イベント設定
		self.ui.btn_point.clicked.connect(self.btn_point_clicked)
		self.ui.btn_orient.clicked.connect(self.btn_orient_clicked)
		self.ui.btn_parent.clicked.connect(self.btn_parent_clicked)
		self.ui.btn_point_orient.clicked.connect(self.btn_point_orient_clicked)
		self.ui.btn_addlist.clicked.connect(self.act_addNode)
		self.ui.btn_bake.clicked.connect(self.act_bake)
		self.ui.btn_changecons.clicked.connect(self.act_changeCons)
		self.ui.btn_dellist.clicked.connect(self.act_deleteList)
		self.ui.btn_close.clicked.connect(self.btn_close_clicked)
		self.ui.list_locators.customContextMenuRequested.connect(self.list_locators_customContextMenuRequested)
		self.ui.list_locators.clicked.connect(self.list_locators_item_clicked)
		self.model.itemChanged.connect(self.list_locators_nameChanged)

		self.ui.list_locators.setEditTriggers(QAbstractItemView.NoEditTriggers)

		## ListView用の登録情報履歴をシーンファイルに直接保存するためのUnknowノードを生成
		self.nameInfo = "getaInfo"
		self.createInfo()

		## スクリプトジョブの生成
		self.job_create()

	def createInfo(self):
		u"""
		TreeViewに登録している情報を保存するために起動時、Unknowノードを生成
		指定した名前のUnknowノードがあった場合、現在の情報を保持
		無かったらUnknowノードを作成
		"""
		if cmds.objExists(self.nameInfo):
			if not cmds.attributeQuery("notes", n=self.nameInfo, ex=True):
				cmds.addAttr(self.nameInfo, ln = "notes", sn="nts", dt="string")
			#getaInfoList = cmds.getAttr("%s.notes" %(self.nameInfo)).split(",")
			getaInfoList = self.updateNote()
			if getaInfoList != None:
				self.addItem(getaInfoList)
		else:
			cmds.createNode('unknown', shared=True, n=self.nameInfo, ss=True)
			if not cmds.attributeQuery("notes", n = self.nameInfo, ex = True):
				cmds.addAttr(self.nameInfo, ln = "notes", sn="nts", dt="string")

	def setNote(self):
		u"""
		createInfo関数で作成したノードのnotesアトリビュートに情報を保持
		"""
		if cmds.objExists(self.nameInfo):
			if cmds.attributeQuery("notes", n=self.nameInfo, ex=True):
				infoList = [self.model.item(i).text() for i in range(self.model.rowCount())]
				cmds.setAttr("%s.notes" %(self.nameInfo), ",".join(infoList), type="string")

	def updateNote(self):
		u"""
		createInfo関数で作成したノードのnotesアトリビュートの情報を更新する
		notesアトリビュート内に現在、シーン上に存在しないノードがあった場合
		削除して、新たなTreeViewの内容のリストを生成する
		"""
		if cmds.objExists(self.nameInfo):
			if cmds.attributeQuery("notes", n=self.nameInfo, ex=True):
				attrString = cmds.getAttr("%s.notes" %(self.nameInfo))
				print attrString
				if attrString != None:
					attrStringList = []
					newAttrStirngList = []
					if "," in attrString:
						attrStringList = attrString.split(",")
					else:
						attrStringList.append(attrString)

					for node in attrStringList:
						if cmds.objExists(node):
							newAttrStirngList.append(node)
					return newAttrStirngList
				else:
					return None


	def createSelectedList(self):
		u"""
		Mayaでのリネーム処理をUIに反映させるため、リネーム前の情報を保存するための関数
		重要なのは以下の3つ
		self.fromListSelected：UIから選択しているもののインデックスのリスト
		self.fromMayaSelected：Mayaから選択しているものの名前のリスト
		self.matchSelected：Mayaで選択しているもののインデックスのリスト
		"""
		cnt = 0
		self.fromListSelected = []
		self.fromMayaSelected = []
		self.matchSelected = []
		for node in cmds.ls(sl=True):
			## self.modelにMayaから選択しているオブジェクトが存在しているか
			if self.model.findItems(node) != []:
				items = [i for i in self.model.findItems(node)]
				for item in items:
					self.fromListSelected.append(self.model.indexFromItem(item))
					self.fromMayaSelected.append(node)
					#Mayaから選択しているものとUIに存在しているものが一致したら
					#Mayaの選択しているもののインデックスを取得する
					if item.text() == node:
						self.matchSelected.append(cnt)
			cnt += 1

	def mousePressEvent(self, event):
		self.__isDrag = True
		self.__startPos = event.pos()
		super(Ui_MainWidget, self).mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		self.__isDrag = False
		super(Ui_MainWidget, self).mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		if self.__isDrag:
			self.move(self.mapToParent(event.pos() - self.__startPos))
		super(Ui_MainWidget, self).mouseMoveEvent(event)

	def paletteUI(self):
		path = QPainterPath()
		path.addRoundedRect(self.rect(), 8, 8)
		region = QRegion(path.toFillPolygon().toPolygon())
		self.setMask(region)

	def job_selection_func(self):
		u"""
		Maya上で選択した情報をUIに反映させる
		選択したオブジェクトがself.modelあった場合、UIをハイライトさせる
		"""
		self.selModel.clear()
		for node in cmds.ls(sl=True):
			## Mayaで選択しているものがself.model内に存在しているか
			if self.model.findItems(node) != []:
				items = [node for node in self.model.findItems(node)]
				for item in items:
					self.selModel.select(self.model.indexFromItem(item), QItemSelectionModel.Select)
					self.createSelectedList()


	def job_delete_func(self):
		u"""
		MayaのDeleteコマンドとScriptJobで連動している
		選択状態のオブジェクトがDeleteされた時、
		TreeVeiwに登録されていたオブジェクトだったら削除
		"""
		newIndexList = []
		rowList = [r.row() for r in self.selModel.selectedIndexes()]
		rowList.sort()
		rowList.reverse()
		for rowIndex in rowList:
			#Scene上に存在しているかどうかの判定 存在していない場合は削除リストに加える
			if not cmds.objExists(self.model.item(rowIndex).text()):
				newIndexList.append(rowIndex)
		self.act_deleteList(True, newIndexList)

	def list_locators_nameChanged(self):
		u"""
		UIから名前を変更したとき、現在、選択しているノードをリネームする
		"""
		if self.fromListRenameFlug == True:
			print "Changed from UI"
			for cnt in range(len(cmds.ls(sl=True))):
				self.fromMayaRenameFlug = False
				if self.selModel.selectedIndexes() != []:
					## UIからのリネーム時に空白だった場合、現在のROWを一旦消して新たにアイテムを追加する
					## model.setItemで空白文字があるROWに上書きしたら、UIからリネームができなくなったのでこの処理にしている
					if self.selModel.selectedIndexes()[cnt].data() != "":
						cmds.rename(cmds.ls(sl=True)[cnt], self.selModel.selectedIndexes()[cnt].data())
					else:
						item = QStandardItem(cmds.ls(sl=True)[cnt])
						self.model.takeRow(self.selModel.selectedIndexes()[cnt].row())
						self.model.appendRow(item)
						#self.model.setItem(0, 0, item)
						#print self.model.findItems(item.text())[0].text()
		else:
			self.fromListRenameFlug = True
			#self.fromMayaRenameFlug = True


	def job_nameChanged(self):
		u"""
		Mayaから名前を変更したとき、現在、選択しているノードをリネームする
		"""
		if self.fromMayaRenameFlug == True:
			print "Renamed from Maya"
			if len(cmds.ls(sl=True)) > 0:
				for nodeIndex, listItem in zip(self.matchSelected, self.fromListSelected):
					self.fromListRenameFlug = False
					#if self.model.findItems(node) != []:
					node = cmds.ls(sl=True)[nodeIndex]
					item = QStandardItem(node)
					self.model.setItem(listItem.row(), item)
				self.job_selection_func()
			else:
				print u"スクリプトによる選択状態でないリネームのため、UIにリネームを反映できませんでした。"
		else:
			#self.fromListRenameFlug = True
			self.fromMayaRenameFlug = True
		self.setNote()

	def job_create(self):
		u"""
		スクリプトジョブの生成
		"""
		self.job_selection = pm.scriptJob(e=["SelectionChanged", self.job_selection_func])
		self.job_delete = pm.scriptJob(ct=["delete", self.job_delete_func])
		self.job_rename = pm.scriptJob(e=["NameChanged", self.job_nameChanged])
		self.job_open = pm.scriptJob(e=["SceneOpened", self.btn_close_clicked])
		self.job_new = pm.scriptJob(e=["deleteAll", self.btn_close_clicked])

	def list_locators_item_clicked(self):
		u"""
		TreeViewをクリックした時に実行される関数
		self.selModelから選択しているもののModelIndexのリストを取得
		ModelIndexから名前を取得して、selectコマンドに渡している
		"""
		selList = [selIndex.data() for selIndex in self.selModel.selectedIndexes()]
		try:
			cmds.select(selList)
			self.createSelectedList()
		except:
			print u"シーン上に存在しないオブジェクトです。"
			#self.act_deleteList()

	def addItem(self, nodeList):
		u"""
		self.modelにnodeListの内容を追加する
		self.model内に既に同じ名前のオブジェクトがあった場合は追加しない
		"""
		for node in nodeList:
			if self.model.findItems(node) == []:
				item = QStandardItem(node)
				self.model.appendRow(item)
				self.job_selection_func()
			else:
				print u"%s は既に登録されています。" %(node)
		self.setNote()

	def btn_point_clicked(self):
		cons_locator = constraints_locator.constraints_locator()
		self.addItem(cons_locator.main("pos"))

	def btn_orient_clicked(self):
		cons_locator = constraints_locator.constraints_locator()
		self.addItem(cons_locator.main("rot"))

	def btn_parent_clicked(self):
		cons_locator = constraints_locator.constraints_locator()
		self.addItem(cons_locator.main("par"))

	def btn_point_orient_clicked(self):
		cons_locator = constraints_locator.constraints_locator()
		self.addItem(cons_locator.main("pos_rot"))

	def btn_close_clicked(self):
		self.setNote()
		self.close()

	def list_locators_customContextMenuRequested(self):
		u"""
		右クリック時のポップアップメニューの設定
		"""
		point = QPoint()
		index = self.ui.list_locators.indexAt(point)
		if not index.isValid():
			return

		menu=QMenu(self)
		act_bake = menu.addAction('Selected Bake')
		act_bake.triggered.connect(self.act_bake)
		act_changeCons = menu.addAction('Change Constraints')
		act_changeCons.triggered.connect(self.act_changeCons)
		act_deleteList = menu.addAction('Delete List')
		act_deleteList.triggered.connect(self.act_deleteList)
		menu.exec_(QCursor.pos())

	def act_bake(self):
		startFrame = cmds.playbackOptions(query=True, minTime=True)
		endFrame = cmds.playbackOptions(query=True, maxTime=True)
		cmds.bakeResults(t=(startFrame, endFrame), sm=True)
		sellist = cmds.ls(sl=True)
		self.EulerFilter(sellist)

	def act_changeCons(self):
		import module.constraints_change as constraints_change
		reload(constraints_change)
		constraints_change.main()

	def act_addNode(self):
		self.addItem(cmds.ls(sl=True))

	def act_deleteList(self, fromMayaDeleteFlag=False, rowIndexList=[]):
		u"""
		ツールに登録されたものをTreeViewから削除する
		fromMayaDeleteFlagがTrueの時は rowIndexList を使用する
			:param fromMayaDeleteFlag: bool 引数を利用して削除する場合はTrue
			:param rowIndexList: list インデックス番号のリスト [3, 2, 1]
			:return: なし
		"""
		if fromMayaDeleteFlag == False:
			rowList = [r.row() for r in self.selModel.selectedIndexes()]
			rowList.sort()
			rowList.reverse()
			for rowIndex in rowList:
				self.model.takeRow(rowIndex)
		else:
			for rowIndex in rowIndexList:
				self.model.takeRow(rowIndex)
		self.setNote()

	def closeEvent(self, event):
		#if self.job_new is not None:
			#cmds.scriptJob(k=self.job_new)
		#if self.job_open is not None:
			#cmds.scriptJob(k=self.job_open)
		if self.job_selection is not None:
			cmds.scriptJob(k=self.job_selection)
		if self.job_delete is not None:
			cmds.scriptJob(k=self.job_delete)
		if self.job_rename is not None:
			cmds.scriptJob(k=self.job_rename)


	def EulerFilter(self, nodeList):
		#オイラーフィルター
		for f in nodeList:
			f_Curve = cmds.keyframe(f,query=True,name=True)
			cmds.filterCurve(f_Curve)

def main():
	ui=Ui_MainWidget()
	ui.show()
