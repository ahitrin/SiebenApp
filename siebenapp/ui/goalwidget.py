# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/goal.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GoalBody(object):
    def setupUi(self, GoalBody):
        GoalBody.setObjectName("GoalBody")
        GoalBody.resize(228, 72)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GoalBody.sizePolicy().hasHeightForWidth())
        GoalBody.setSizePolicy(sizePolicy)
        self.horizontalLayout = QtWidgets.QHBoxLayout(GoalBody)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtWidgets.QFrame(GoalBody)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.check_open = QtWidgets.QCheckBox(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.check_open.sizePolicy().hasHeightForWidth())
        self.check_open.setSizePolicy(sizePolicy)
        self.check_open.setText("")
        self.check_open.setObjectName("check_open")
        self.horizontalLayout_3.addWidget(self.check_open)
        self.label_number = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_number.sizePolicy().hasHeightForWidth())
        self.label_number.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label_number.setFont(font)
        self.label_number.setText("")
        self.label_number.setObjectName("label_number")
        self.horizontalLayout_3.addWidget(self.label_number)
        self.label_goal_name = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_goal_name.sizePolicy().hasHeightForWidth())
        self.label_goal_name.setSizePolicy(sizePolicy)
        self.label_goal_name.setText("")
        self.label_goal_name.setObjectName("label_goal_name")
        self.horizontalLayout_3.addWidget(self.label_goal_name)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addWidget(self.frame)

        self.retranslateUi(GoalBody)
        QtCore.QMetaObject.connectSlotsByName(GoalBody)

    def retranslateUi(self, GoalBody):
        _translate = QtCore.QCoreApplication.translate
        GoalBody.setWindowTitle(_translate("GoalBody", "Form"))

