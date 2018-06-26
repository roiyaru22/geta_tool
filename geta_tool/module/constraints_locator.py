# -*- coding: utf-8 -*-
import maya.cmds as cmds

class constraints_locator():
	def __init__(self):
		self.locatorNameList = []

	def main(self, ConstraintType):
		selected_list = cmds.ls(sl=True)
		for node in cmds.ls(sl=True):
			if ConstraintType == "pos":
				#locator_list = cmds.spaceLocator(name = "%s_%s" %(node, ConstraintType))
				locator_list = cmds.spaceLocator(name = self.isObjectName("%s_%s" %(node, ConstraintType)))
				cmds.pointConstraint(node, locator_list)

			elif ConstraintType == "rot":
				locator_list = cmds.spaceLocator(name = self.isObjectName("%s_%s" %(node, ConstraintType)))
				cmds.orientConstraint(node, locator_list)
				node_translate = cmds.xform(node, q=True, t=True, ws=True)
				cmds.xform(locator_list, t=node_translate)

			elif ConstraintType == "par":
				locator_list = cmds.spaceLocator(name = self.isObjectName("%s_%s" %(node, ConstraintType)))
				cmds.parentConstraint(node, locator_list)

			elif ConstraintType == "pos_rot":
				locator_list = cmds.spaceLocator(name = self.isObjectName("%s_%s" %(node, ConstraintType)))
				cmds.pointConstraint(node, locator_list)
				cmds.orientConstraint(node, locator_list)

			self.locatorNameList.append(locator_list[0])
		cmds.select(selected_list)
		return self.locatorNameList

	def isObjectName(self, obj_name):
		if cmds.objExists(obj_name):
			return "%s_%d" %(obj_name, 0)
		else:
			return obj_name
