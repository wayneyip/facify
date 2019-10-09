# wy_facify.py

from maya import cmds
from math import floor, ceil


class FaceRig:

    def __init__(self, parentJoint, bodyPart, bSmartClose):

        self.bodyPart = bodyPart
        self.parentJoint = parentJoint
        self.bSmartClose = bSmartClose
        self.cornerVerts = None
        self.cornerDict = None
        self.upperHDCurve = None
        self.upperLDCurve = None
        self.lowerHDCurve = None
        self.lowerLDCurve = None
        self.upperMidControl = None
        self.lowerMidControl = None
        self.upperDriverJoints = None
        self.lowerDriverJoints = None

    def facifyVertsSet(self, vertsSet, prefix):

        # Get upper vertices from set
        cmds.select(clear=1)
        cmds.select(vertsSet)
        verts = cmds.ls(selection=1, flatten=1)
        
        # Sort by x-value (left to right)
        verts = sorted(verts, key = lambda v: cmds.xform(v, q=1, worldSpace=1, translation=1)[0])
        vertsPos = [cmds.xform(vert, q=1, worldSpace=1, translation=1) for vert in verts]

        # Create up vector
        centerPos = cmds.xform(self.parentJoint, q=1, worldSpace=1, translation=1)
        upVecPos = centerPos[:]
        upVecPos[1] += 10
        upVecLoc = cmds.spaceLocator(p=upVecPos, absolute=1, n='{}_{}_upVec_LOC'.format(self.bodyPart, prefix))[0]
        cmds.xform(upVecLoc, centerPivots=1)

        def createJointsAndLocator(vert, index, locators):

            # Create center joint
            cmds.select(clear=1)
            centerJoint = cmds.joint(p=centerPos, n='{}_{}_{}_JNT'.format(self.bodyPart, prefix, index))
            
            # Create tip joint 
            cmds.select(clear=1)
            vertPos = cmds.xform(vert, q=1, worldSpace=1, translation=1)
            tipJoint = cmds.joint(p=vertPos, name='{}_{}_{}_tip_JNT'.format(self.bodyPart, prefix, index))

            # Parent and orient center/tip joints
            cmds.parent(tipJoint, centerJoint)
            cmds.parent(centerJoint, self.parentJoint)
            cmds.joint(centerJoint, e=1, orientJoint="xyz", secondaryAxisOrient="yup", children=1, zeroScaleOrient=1)

            # Create locator
            vertLoc = cmds.spaceLocator(n='{}_{}_{}_LOC'.format(self.bodyPart, prefix, index))[0]
            vertLocShape = cmds.listRelatives(vertLoc, shapes=1)[0]
            vertLocScale = 0.0005
            cmds.setAttr(vertLocShape+'.localScaleX', vertLocScale)
            cmds.setAttr(vertLocShape+'.localScaleY', vertLocScale)
            cmds.setAttr(vertLocShape+'.localScaleZ', vertLocScale)

            # Move locator to vert, aim constrain center joint to locator
            vertPos = cmds.xform(vert, q=1, worldSpace=1, translation=1)
            cmds.xform(vertLoc, worldSpace=1, translation=vertPos)
            cmds.aimConstraint(
                vertLoc, centerJoint, 
                maintainOffset=1, weight=1, 
                aimVector=(1,0,0), upVector=(0,1,0), 
                worldUpType='object', worldUpObject=upVecLoc
            )
            locators.append(vertLoc)
            return vertLoc

        locators = []
        for i, vert in enumerate(verts):
            if vert in self.cornerVerts:
                if prefix == 'upper':
                    locator = createJointsAndLocator(vert, i, locators)
                    self.cornerDict[vert] = {'locator': locator}
                elif prefix == 'lower':
                    locators.append(self.cornerDict[vert]['locator'])
            else:
                createJointsAndLocator(vert, i, locators)

        # Draw high-density curves
        HDCurve = cmds.curve(degree=1, point=vertsPos, n='{}_{}_hiDensity_CRV'.format(self.bodyPart, prefix))

        # Connect high-density curves to locators
        for i, loc in enumerate(locators):
            cornerLocators = [vertData['locator'] for vertData in self.cornerDict.values()]
            if loc in cornerLocators and prefix == 'lower':
                continue
            pos = cmds.xform(loc, q=1, worldSpace=1, translation=1)
            u = float(i)
            name = '{}_{}_{}_PCI'.format(self.bodyPart, prefix, i)
            pci = cmds.createNode("pointOnCurveInfo", n=name)
            cmds.connectAttr(HDCurve + '.worldSpace', pci + '.inputCurve')
            cmds.setAttr(pci + '.parameter', u)
            cmds.connectAttr(pci + '.position', loc + '.t')

        # Draw low-density curves
        LDCurve = cmds.rebuildCurve(HDCurve, 
            degree=3, 
            spans=2, 
            replaceOriginal=0,
            n='{}_{}_loDensity_CRV'.format(self.bodyPart, prefix)
        )[0]

        # Create individual joints (and controls) to drive low-density curve
        def CreateDriverJointAndControl(index):

            vertPos = vertsPos[index]
            driverJoint = cmds.joint(p=vertPos, n='{}_{}_{}_driver_JNT'.format(self.bodyPart, prefix, index))

            driverCtrlName = driverJoint.replace('_JNT', '_CTRL')
            driverJointPos = cmds.xform(driverJoint, q=1, worldSpace=1, translation=1)
            driverJointMove = [1.2 * (x - y) for x, y in zip(driverJointPos, centerPos)]

            driverCtrl = cmds.circle(n=driverCtrlName, normal=(1,0,0), radius=0.04)[0]
            cmds.color(driverCtrl, rgbColor=[1,1,0])
            
            drivenJoint = driverJoint.replace('driver_JNT', 'JNT')
            cmds.matchTransform(driverCtrl, drivenJoint, pivots=1, pos=1, rot=1, scl=1)
            cmds.xform(driverCtrl, translation=driverJointMove, relative=1)
            cmds.xform(driverCtrl, rotatePivot=driverJointPos, worldSpace=1)

            cmds.pointConstraint(driverCtrl, driverJoint, maintainOffset=1)
            cmds.makeIdentity(driverCtrl, apply=1, translate=1, rotate=1, scale=1, normal=0)

            return driverJoint, driverCtrl

        driverJoints = []
        driverCtrls = []
        midControl = None
        numControls = 5
        for i in range(numControls):
            cmds.select(clear=1)

            # Spread out selection of vertices to create joints at
            index = float(len(verts)-1) / (numControls-1) * i
            if i < numControls / 2.0:
                index = int(floor(index))
            else:
                index = int(ceil(index))
            
            vert = verts[index]
            if vert in self.cornerVerts:
                if prefix == 'upper':
                    driverJoint, driverCtrl = CreateDriverJointAndControl(index)
                    driverJoints.append(driverJoint)
                    driverCtrls.append(driverCtrl)
                    self.cornerDict[vert]['driverJoint'] = driverJoint
                elif prefix == 'lower':
                    driverJoints.append(self.cornerDict[vert]['driverJoint'])
            
            else:
                driverJoint, driverCtrl = CreateDriverJointAndControl(index)
                driverJoints.append(driverJoint)
                driverCtrls.append(driverCtrl)

                # Identify center control, for creating attributes
                if i == numControls / 2:
                    midControl = driverCtrl

        # Final cleanup (grouping)
        locatorsGrp = cmds.group(locators, n='{}_{}_LOC_GRP'.format(self.bodyPart, prefix))
        driverJointsGrp = cmds.group(driverJoints, n='{}_{}_driver_JNT_GRP'.format(self.bodyPart, prefix))
        driverCtrlsGrp = cmds.group(driverCtrls, n='{}_{}_driver_CTRL_GRP'.format(self.bodyPart, prefix))
        cmds.group(
            driverJointsGrp, driverCtrlsGrp,
            locatorsGrp, upVecLoc, 
            HDCurve, LDCurve,
            n='{}_{}_all_GRP'.format(self.bodyPart, prefix)
        )

        return HDCurve, LDCurve, midControl, driverJoints


    def facify(self, upperVertsSet, lowerVertsSet):

        # Get corner verts
        self.cornerVerts = cmds.sets(upperVertsSet, intersection=lowerVertsSet)
        cmds.select(self.cornerVerts)
        self.cornerVerts = cmds.ls(selection=1, flatten=1)
        self.cornerDict = {}
        
        # Set up main curve-based rig
        self.upperHDCurve, self.upperLDCurve, self.upperMidControl, self.upperDriverJoints = self.facifyVertsSet(upperVertsSet, 'upper')
        self.lowerHDCurve, self.lowerLDCurve, self.lowerMidControl, self.lowerDriverJoints = self.facifyVertsSet(lowerVertsSet, 'lower')


    def isolateSelectCurves(self):

        viewPane = cmds.paneLayout('viewPanes', q=True, pane1=True)
        cmds.select(self.upperHDCurve)
        cmds.select(self.upperLDCurve, add=1)
        cmds.select(self.lowerHDCurve, add=1)
        cmds.select(self.lowerLDCurve, add=1)
        cmds.isolateSelect(viewPane, state=1)


    def connectCurves(self):

        # Drive high-density curve with low-density curve, using wire deformer
        cmds.wire(self.upperHDCurve, wire=self.upperLDCurve, dropoffDistance=[0,10], n='{}_upper_loDensity_WIRE'.format(self.bodyPart))
        cmds.wire(self.lowerHDCurve, wire=self.lowerLDCurve, dropoffDistance=[0,10], n='{}_lower_loDensity_WIRE'.format(self.bodyPart))

        # Skin driver joints to low-density curve
        cmds.skinCluster(self.upperDriverJoints, self.upperLDCurve, 
            name='{}_upper_skinCluster'.format(self.bodyPart), 
            toSelectedBones=True, 
            skinMethod=0,           # classic linear skinning
            normalizeWeights=1
        )
        cmds.skinCluster(self.lowerDriverJoints, self.lowerLDCurve, 
            name='{}_lower_skinCluster'.format(self.bodyPart), 
            toSelectedBones=True, 
            skinMethod=0,           # classic linear skinning
            normalizeWeights=1
        )

        # Return view to normal
        viewPane = cmds.paneLayout('viewPanes', q=True, pane1=True)
        cmds.isolateSelect(viewPane, state=0)

        # Set up smart close functionality
        if self.bSmartClose:
            
            # Create blink curve that blends between upper & lower curves
            blinkCurve = cmds.duplicate(self.upperLDCurve, n='{}_blink_CRV'.format(self.bodyPart))
            blinkBlendshape = cmds.blendShape(self.upperLDCurve, self.lowerLDCurve, blinkCurve, n='{}_blinkHeight_BLN'.format(self.bodyPart))[0]

            # Add attribute to control one blendshape's weight
            cmds.addAttr(self.upperMidControl, longName='smartCloseHeight', attributeType='double', minValue=0, maxValue=1, keyable=1)
            cmds.connectAttr(self.upperMidControl+'.smartCloseHeight', blinkBlendshape+'.'+self.upperLDCurve)
            
            # Connect attribute to reverse other blendshape's weight
            reverseNode = cmds.createNode('reverse', n='{}_blink_RVS'.format(self.bodyPart))
            cmds.connectAttr(self.upperMidControl+'.smartCloseHeight', reverseNode+'.inputX')
            cmds.connectAttr(reverseNode+'.inputX', blinkBlendshape+'.'+self.lowerLDCurve)

            # Create upper blink curve 
            upperBlinkCurve = cmds.duplicate(self.upperHDCurve, n='{}_upper_blink_CRV'.format(self.bodyPart))[0]
            upperBlinkWire = cmds.wire(upperBlinkCurve, wire=blinkCurve, dropoffDistance=[0,10], n='{}_upper_blink_WIRE'.format(self.bodyPart))[0]
            cmds.setAttr(upperBlinkWire+'.scale[0]', 0)
            upperBlinkTargetBlendshape = cmds.blendShape(upperBlinkCurve, self.upperHDCurve, n='{}_upper_blinkTarget_BLN'.format(self.bodyPart))[0]
            
            # Create lower blink curve
            lowerBlinkCurve = cmds.duplicate(self.lowerHDCurve, n='{}_lower_blink_CRV'.format(self.bodyPart))[0]
            cmds.setAttr(self.upperMidControl+'.smartCloseHeight', 1)
            lowerBlinkWire = cmds.wire(lowerBlinkCurve, wire=blinkCurve, dropoffDistance=[0,10], n='{}_lower_blink_WIRE'.format(self.bodyPart))[0]
            cmds.setAttr(lowerBlinkWire+'.scale[0]', 0)
            lowerBlinkTargetBlendshape = cmds.blendShape(lowerBlinkCurve, self.lowerHDCurve, n='{}_lower_blinkTarget_BLN'.format(self.bodyPart))[0]

            # Create attribute to control smart close
            cmds.addAttr(self.upperMidControl, longName='smartClose', attributeType='double', minValue=0, maxValue=1, keyable=1)
            cmds.connectAttr(self.upperMidControl+'.smartClose', upperBlinkTargetBlendshape+'.'+upperBlinkCurve)
            cmds.addAttr(self.lowerMidControl, longName='smartClose', attributeType='double', minValue=0, maxValue=1, keyable=1)
            cmds.connectAttr(self.lowerMidControl+'.smartClose', lowerBlinkTargetBlendshape+'.'+lowerBlinkCurve)

            # Set close to middle
            cmds.setAttr(self.upperMidControl+'.smartCloseHeight', 0.5)
