# -*- coding: utf-8 -*-
#コンストレインを反転し、接続し直すスクリプト
#コンストレインしているオブジェクトを選択して実行する
import maya.cmds as cmds

def main():
	#コンストレインノードが子供になっているオブジェクトのリストを作成
	#そのリストを元に再選択
	selection_list = []
	for node in cmds.ls(sl=True):
		consList = cmds.listRelatives(node, type="constraint")
		if consList != None:
			selection_list.append(node)
	#cmds.select(selection_list)
	cmds.select(cl=True)

	for node in selection_list:
		#選択中のオブジェクトにコンストレイントを取得（リスト）
		consList = cmds.listRelatives(node, type="constraint")
		#コンストレイントのリスト分だけループ
		for cons in consList:
			#コンストレイント先のオブジェクト名をアトリビュートから取得（リスト）
			consingObjList = cmds.listConnections("%s.target[0].targetParentMatrix" %(cons))
			#コンストレイント先のオブジェクト名のリスト分だけループ
			for consingObj in consingObjList:
				consType = cmds.nodeType(cons)
				#取得したコンストレイントのタイプで処理を分岐
				if consType == "pointConstraint":
					cmds.delete(cons)
					cmds.pointConstraint(node, consingObj)

				elif consType == "orientConstraint":
					cmds.delete(cons)
					cmds.orientConstraint(node, consingObj)

				elif consType == "parentConstraint":
					cmds.delete(cons)
					cmds.parentConstraint(node, consingObj)

				else:
					print u"想定していないコンストレイントです。"

if __name__ == "__main__":
	main()
