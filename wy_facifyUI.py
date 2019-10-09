# wy_facifyUI.py
# Author: Wayne Yip
# Date: May 27, 2019

import maya.cmds as cmds
from functools import partial
import wy_facify
reload (wy_facify)

class FacifyUI():

    def __init__(self):

        self.faceRig = None

    def createUI(self):
        
        # Create window
        if cmds.window('facifyWin', exists=1):
            cmds.deleteUI('facifyWin')
        window = cmds.window('facifyWin', title='Facify', sizeable=1)
        
        # Create form + UI elements
        form = cmds.formLayout(numberOfDivisions=100)

        upperVertsSetText = cmds.textFieldGrp(label='Upper Verts Set ', adj=2, editable=0)
        upperVertsSetBtn = cmds.button(label='Set Selected',
            command=partial(self.checkSelectedVertsSet,
                upperVertsSetText
            )
        )
        lowerVertsSetText = cmds.textFieldGrp(label='Lower Verts Set ', adj=2, editable=0)
        lowerVertsSetBtn = cmds.button(label='Set Selected',
            command=partial(self.checkSelectedVertsSet,
                lowerVertsSetText
            )
        )
        parentJointText = cmds.textFieldGrp(label='Parent Joint ', adj=2, editable=0)
        parentJointBtn = cmds.button(label='Set Selected',
            command=partial(self.checkSelectedParentJoint,
                parentJointText
            )
        )
        namingPrefixText = cmds.textFieldGrp(label='Naming Prefix ', adj=2)
        
        smartCloseChkbox = cmds.checkBoxGrp( label='Smart Close ')
        
        finalizeRigBtn = cmds.button(label='Finalize Rig', enable=0,
            command=partial(self.finalizeRig
            )
        )
        facifyBtn = cmds.button(label='Facify!', 
            command=partial(self.applyFacify, 
                upperVertsSetText, lowerVertsSetText, 
                parentJointText, namingPrefixText,
                smartCloseChkbox, finalizeRigBtn
            )
        )
        closeBtn = cmds.button(label='Close', 
            command="cmds.deleteUI('facifyWin')"
        )

        # Format UI elements
        cmds.formLayout(form, edit=1,
            attachForm=[
                (upperVertsSetText, 'top', 15),
                (upperVertsSetText, 'left', 0),

                (upperVertsSetBtn, 'top', 15),
                (upperVertsSetBtn, 'right', 10),

                (lowerVertsSetText, 'left', 0),
                (lowerVertsSetText, 'right', 0),

                (lowerVertsSetBtn, 'right', 10),

                (parentJointText, 'left', 0),
                (parentJointText, 'right', 0),

                (parentJointBtn, 'right', 10),

                (namingPrefixText, 'left', 0),
                (namingPrefixText, 'right', 0),

                (smartCloseChkbox, 'left', 0),
                (smartCloseChkbox, 'right', 0),

                (facifyBtn, 'left', 5),
                (facifyBtn, 'right', 5),

                (finalizeRigBtn, 'left', 5),
                (finalizeRigBtn, 'right', 5),

                (closeBtn, 'left', 5),
                (closeBtn, 'right', 5),
                (closeBtn, 'bottom', 5)
            ],
                attachControl=[
                (upperVertsSetText, 'bottom', 5, lowerVertsSetText),
                (upperVertsSetText, 'right', 5, upperVertsSetBtn),
                (upperVertsSetBtn, 'bottom', 5, lowerVertsSetBtn),

                (lowerVertsSetText, 'bottom', 5, parentJointText),
                (lowerVertsSetText, 'right', 5, lowerVertsSetBtn),
                (lowerVertsSetBtn, 'bottom', 5, parentJointBtn),
                
                (parentJointText, 'bottom', 5, namingPrefixText),
                (parentJointText, 'right', 5, parentJointBtn),
                (parentJointBtn, 'bottom', 5, namingPrefixText),
                
                (namingPrefixText, 'bottom', 5, smartCloseChkbox),
                
                (smartCloseChkbox, 'bottom', 15, facifyBtn),
                
                (facifyBtn, 'bottom', 15, finalizeRigBtn),
                (finalizeRigBtn, 'bottom', 15, closeBtn),
            ],
            attachPosition=[
            ]
        )

        cmds.showWindow(window)


    def checkSelectedVertsSet(self, vertsSetText, *args):

        vertsSet = cmds.ls(selection=1)

        if len(vertsSet) != 1:
            cmds.confirmDialog(title='Error', message='Please select a set of vertices.')

        elif cmds.objectType(vertsSet) != 'objectSet' or cmds.sets(vertsSet, q=1, vertices=1):
            cmds.confirmDialog(title='Error', message='Object selected is not a set of vertices.')

        else:
            cmds.textFieldGrp(vertsSetText, edit=1, text=cmds.ls(selection=1)[0])


    def checkSelectedParentJoint(self, parentJointText, *args):

        parentJoint = cmds.ls(selection=1)

        if len(parentJoint) != 1:
            cmds.confirmDialog(title='Error', message='Please select a joint.')
            return False

        elif cmds.objectType(parentJoint) != 'joint':
            cmds.confirmDialog(title='Error', message='Object selected is not a joint.')
        
        else:
            cmds.textFieldGrp(parentJointText, edit=1, text=cmds.ls(selection=1)[0])
        

    def applyFacify(self, upperVertsSetText, lowerVertsSetText, parentJointText, namingPrefixText, smartCloseChkbox, finalizeRigBtn, *args):

        upperVertsSet = cmds.textFieldGrp(upperVertsSetText, q=1, text=1)
        lowerVertsSet = cmds.textFieldGrp(lowerVertsSetText, q=1, text=1)
        parentJoint = cmds.textFieldGrp(parentJointText, q=1, text=1)
        namingPrefix = cmds.textFieldGrp(namingPrefixText, q=1, text=1)
        smartClose = cmds.checkBoxGrp(smartCloseChkbox, q=1, value1=1)

        if upperVertsSet == '' or lowerVertsSet == '' or parentJoint == '' or namingPrefix == '':
            cmds.confirmDialog(title='Error', message="Please fill in all text fields.")
            return

        if upperVertsSet == lowerVertsSet:
            cmds.confirmDialog(title='Error', message="Vertex sets are identical.")
            return

        self.faceRig = wy_facify.FaceRig(parentJoint, namingPrefix, smartClose)
        self.faceRig.facify(upperVertsSet, lowerVertsSet)
        
        cmds.inViewMessage(amg='Adjust the <hl>low-density curves</hl> to match the high-density curves.', pos='topCenter', fade=True)
        
        cmds.button(finalizeRigBtn, edit=1, enable=1)

        self.faceRig.isolateSelectCurves()


    def finalizeRig(self, facifyBtn, *args):

        self.faceRig.connectCurves()