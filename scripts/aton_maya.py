__author__ = "Vahan Sosoyan"
__copyright__ = "2016 All rights reserved. See Copyright.txt for more details."
__version__ = "v1.1.3"

import sys, re
import maya.mel as mel
import maya.OpenMaya as OM
import pymel.core as pm
from maya import cmds, OpenMayaUI

try:
    from arnold import *
    import mtoa.core as core
except ImportError:
    cmds.warning("MtoA was not found.")

from PySide import QtCore
from PySide import QtGui
from shiboken import wrapInstance

def maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

class Aton(QtGui.QDialog):

    def __init__(self, parent = maya_main_window()):
        super(Aton, self).__init__(parent)

        self.windowName = "Aton"
        if cmds.window(self.windowName, exists = True):
            cmds.deleteUI(self.windowName, wnd = True)

        self.setupUi()

    def closeEvent(self, event):
        if self.timeChange != None:
            OM.MEventMessage.removeCallback(self.timeChange)
            self.timeChange = None

    def getActiveCamera(self, s=1):
        ''' Returns active view camera name '''
        modelviewPanels = [x for x in cmds.lsUI(dw=1) if re.search(r"viewPanes\|modelPanel[0-9]+$", x)]
        for item in modelviewPanels:
            try:
                model_editor = cmds.modelPanel(item.split("|")[-1], q=1, me=1)
                if cmds.modelEditor(model_editor, q=1, av=1):
                    cam = cmds.modelEditor(model_editor, q=1, cam=1)
                    return cam if s == 0 else cmds.listRelatives(cam)[0]
            except RuntimeError:
                pass

    def getSceneOptions(self):
        sceneOptions = {}
        if cmds.getAttr("defaultRenderGlobals.ren") == "arnold":
            try:
                cmds.getAttr("defaultArnoldDisplayDriver.port")
            except ValueError:
                mel.eval("unifiedRenderGlobalsWindow;")
            sceneOptions["port"] = cmds.getAttr("defaultArnoldDisplayDriver.port")
            sceneOptions["camera"] = self.getActiveCamera()
            sceneOptions["width"]  = cmds.getAttr("defaultResolution.width")
            sceneOptions["height"] = cmds.getAttr("defaultResolution.height")
            sceneOptions["AASamples"] = cmds.getAttr("defaultArnoldRenderOptions.AASamples")
            sceneOptions["motionBlur"] = cmds.getAttr("defaultArnoldRenderOptions.ignoreMotionBlur")
            sceneOptions["subdivs"] = cmds.getAttr("defaultArnoldRenderOptions.ignoreSubdivision")
            sceneOptions["displace"] = cmds.getAttr("defaultArnoldRenderOptions.ignoreDisplacement")
            sceneOptions["bump"] = cmds.getAttr("defaultArnoldRenderOptions.ignoreBump")
            sceneOptions["sss"] = cmds.getAttr("defaultArnoldRenderOptions.ignoreSss")
        else:
            sceneOptions["port"] = 0
            sceneOptions["camera"] = self.getActiveCamera()
            sceneOptions["width"]  = cmds.getAttr("defaultResolution.width")
            sceneOptions["height"] = cmds.getAttr("defaultResolution.height")
            sceneOptions["AASamples"] = 0
            sceneOptions["motionBlur"] = 0
            sceneOptions["subdivs"] = 0
            sceneOptions["displace"] = 0
            sceneOptions["bump"] = 0
            sceneOptions["sss"] = 0
            cmds.warning("Current renderer is not set to Arnold.")
        return sceneOptions
        
    def setupUi(self):

        sceneOptions = self.getSceneOptions()

        def resUpdateUi():
            self.resolutionSpinBox.setValue(resolutionSlider.value() * 5)

        def camUpdateUi():
            self.cameraAaSpinBox.setValue(cameraAaSlider.value())

        def portUpdateUi():
            self.portSpinBox.setValue(portSlider.value() + self.defaultPort)

        def resetUi(*args):
            sceneOptions = self.getSceneOptions()
            self.portSpinBox.setValue(self.defaultPort)
            portSlider.setValue(0)
            self.cameraComboBox.setCurrentIndex(0)
            self.resolutionSpinBox.setValue(100)
            resolutionSlider.setValue(20)
            self.cameraAaSpinBox.setValue(sceneOptions["AASamples"])
            cameraAaSlider.setValue(sceneOptions["AASamples"])
            self.renderRegionXSpinBox.setValue(0)
            self.renderRegionYSpinBox.setValue(0)
            self.renderRegionRSpinBox.setValue(sceneOptions["width"])
            self.renderRegionTSpinBox.setValue(sceneOptions["height"])
            self.motionBlurCheckBox.setChecked(sceneOptions["motionBlur"])
            self.subdivsCheckBox.setChecked(sceneOptions["subdivs"])
            self.displaceCheckBox.setChecked(sceneOptions["displace"])
            self.bumpCheckBox.setChecked(sceneOptions["bump"])
            self.sssCheckBox.setChecked(sceneOptions["sss"])

        self.setObjectName(self.windowName)
        self.setWindowTitle("Aton %s"%__version__)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_AlwaysShowToolTips)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.setContentsMargins(5,5,5,5)
        mainLayout.setSpacing(2)

        generalGroupBox = QtGui.QGroupBox("General")
        generalLayout = QtGui.QVBoxLayout(generalGroupBox)

        # Port Layout
        portLayout = QtGui.QHBoxLayout()
        portLabel = QtGui.QLabel("Port:")
        portLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        portLabel.setMaximumSize(75, 20)
        portLabel.setMinimumSize(75, 20)
        self.portSpinBox = QtGui.QSpinBox()
        self.portSpinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.portSpinBox.setMaximum(1024)
        self.portSpinBox.setMaximum(9999)
        self.defaultPort = sceneOptions["port"]
        self.portSpinBox.setValue(self.defaultPort)
        portSlider = QtGui.QSlider()
        portSlider.setOrientation(QtCore.Qt.Horizontal)
        portSlider.setMinimum(0)
        portSlider.setMaximum(15)
        portSlider.setValue(0)
        self.timeChange = None
        portLayout.addWidget(portLabel)
        portLayout.addWidget(self.portSpinBox)
        portLayout.addWidget(portSlider)

        # Camera Layout
        cameraLayout = QtGui.QHBoxLayout()
        cameraLabel = QtGui.QLabel("Camera:")
        cameraLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        cameraLabel.setMaximumSize(75, 20)
        cameraLabel.setMinimumSize(75, 20)
        self.cameraComboBox = QtGui.QComboBox()
        self.cameraComboBoxDict = {}
        self.cameraComboBox.addItem("Current (%s)"%sceneOptions["camera"])
        for i in cmds.listCameras():
            self.cameraComboBox.addItem(i)
            self.cameraComboBoxDict[cmds.listCameras().index(i)+1] = i
        cameraLayout.addWidget(cameraLabel)
        cameraLayout.addWidget(self.cameraComboBox)

        overridesGroupBox = QtGui.QGroupBox("Overrides")
        overridesLayout = QtGui.QVBoxLayout(overridesGroupBox)

        # Resolution Layout
        resolutionLayout = QtGui.QHBoxLayout()
        resolutionLabel = QtGui.QLabel("Resolution %:")
        resolutionLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        resolutionLabel.setMinimumSize(75, 20)
        self.resolutionSpinBox = QtGui.QSpinBox()
        self.resolutionSpinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.resolutionSpinBox.setMinimum(1)
        self.resolutionSpinBox.setMaximum(900)
        self.resolutionSpinBox.setValue(100)
        resolutionSlider = QtGui.QSlider()
        resolutionSlider.setOrientation(QtCore.Qt.Horizontal)
        resolutionSlider.setValue(20)
        resolutionSlider.setMaximum(20)
        resolutionLayout.addWidget(resolutionLabel)
        resolutionLayout.addWidget(self.resolutionSpinBox)
        resolutionLayout.addWidget(resolutionSlider)

        # Camera Layout
        cameraAaLayout = QtGui.QHBoxLayout()
        cameraAaLabel = QtGui.QLabel("Camera (AA):")
        cameraAaLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        cameraAaLabel.setMinimumSize(75, 20)
        self.cameraAaSpinBox = QtGui.QSpinBox()
        self.cameraAaSpinBox.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.cameraAaSpinBox.setMaximum(64)
        self.cameraAaSpinBox.setMinimum(-64)
        self.cameraAaSpinBox.setValue(sceneOptions["AASamples"])
        cameraAaSlider = QtGui.QSlider()
        cameraAaSlider.setOrientation(QtCore.Qt.Horizontal)
        cameraAaSlider.setValue(self.cameraAaSpinBox.value())
        cameraAaSlider.setMaximum(16)
        cameraAaSlider.valueChanged[int].connect(self.cameraAaSpinBox.setValue)
        cameraAaLayout.addWidget(cameraAaLabel)
        cameraAaLayout.addWidget(self.cameraAaSpinBox)
        cameraAaLayout.addWidget(cameraAaSlider)

        # Render region layout
        renderRegionLayout = QtGui.QHBoxLayout()
        renderRegionLabel = QtGui.QLabel("Region X:")
        renderRegionLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.renderRegionXSpinBox = QtGui.QSpinBox()
        renderRegionYLabel = QtGui.QLabel("Y:")
        self.renderRegionYSpinBox = QtGui.QSpinBox()
        renderRegionRLabel = QtGui.QLabel("R:")
        self.renderRegionRSpinBox = QtGui.QSpinBox()
        renderRegionTLabel = QtGui.QLabel("T:")
        self.renderRegionTSpinBox = QtGui.QSpinBox()
        renderRegionCheckBox = QtGui.QCheckBox()
        renderRegionGetNukeButton = QtGui.QPushButton("Get")
        renderRegionGetNukeButton.clicked.connect(self.getNukeCropNode)
        renderRegionCheckBox.setLayoutDirection(QtCore.Qt.RightToLeft)
        renderRegionLayout.addWidget(renderRegionLabel)
        renderRegionLayout.addWidget(self.renderRegionXSpinBox)
        renderRegionLayout.addWidget(renderRegionYLabel)
        renderRegionLayout.addWidget(self.renderRegionYSpinBox)
        renderRegionLayout.addWidget(renderRegionRLabel)
        renderRegionLayout.addWidget(self.renderRegionRSpinBox)
        renderRegionLayout.addWidget(renderRegionTLabel)
        renderRegionLayout.addWidget(self.renderRegionTSpinBox)
        renderRegionLayout.addWidget(renderRegionGetNukeButton)

        for i in [renderRegionLabel,
                  renderRegionYLabel,
                  renderRegionRLabel,
                  renderRegionTLabel]:
            i.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)

        for i in [self.renderRegionXSpinBox,
                  self.renderRegionYSpinBox,
                  self.renderRegionRSpinBox,
                  self.renderRegionTSpinBox]:
            i.setRange(0,99999)
            i.setMaximumSize(60,25)
            i.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)

        self.renderRegionRSpinBox.setValue(sceneOptions["width"])
        self.renderRegionTSpinBox.setValue(sceneOptions["height"])

        ignoresGroupBox = QtGui.QGroupBox("Ignore")
        ignoresLayout = QtGui.QVBoxLayout(ignoresGroupBox)

        # Ignore Layout
        ignoreLayout = QtGui.QHBoxLayout()
        ignoreLabel = QtGui.QLabel("Ignore:")
        ignoreLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.motionBlurCheckBox = QtGui.QCheckBox("Motion Blur")
        self.motionBlurCheckBox.setChecked(sceneOptions["motionBlur"])
        self.subdivsCheckBox = QtGui.QCheckBox("Subdivs")
        self.subdivsCheckBox.setChecked(sceneOptions["subdivs"])
        self.displaceCheckBox = QtGui.QCheckBox("Displace")
        self.displaceCheckBox.setChecked(sceneOptions["displace"])
        self.bumpCheckBox = QtGui.QCheckBox("Bump")
        self.bumpCheckBox.setChecked(sceneOptions["bump"])
        self.sssCheckBox = QtGui.QCheckBox("SSS")
        self.sssCheckBox.setChecked(sceneOptions["sss"])
        ignoreLayout.addWidget(self.motionBlurCheckBox)
        ignoreLayout.addWidget(self.subdivsCheckBox)
        ignoreLayout.addWidget(self.displaceCheckBox)
        ignoreLayout.addWidget(self.bumpCheckBox)
        ignoreLayout.addWidget(self.sssCheckBox)

        # Main Buttons Layout
        mainButtonslayout = QtGui.QHBoxLayout()
        startButton = QtGui.QPushButton("Start / Refresh")
        stopButton = QtGui.QPushButton("Stop")
        resetButton = QtGui.QPushButton("Reset")
        startButton.clicked.connect(self.render)
        stopButton.clicked.connect(self.stop)
        resetButton.clicked.connect(resetUi)
        mainButtonslayout.addWidget(startButton)
        mainButtonslayout.addWidget(stopButton)
        mainButtonslayout.addWidget(resetButton)

        # Add Layouts to Main
        generalLayout.addLayout(portLayout)
        generalLayout.addLayout(cameraLayout)
        overridesLayout.addLayout(resolutionLayout)
        overridesLayout.addLayout(cameraAaLayout)
        overridesLayout.addLayout(renderRegionLayout)
        ignoresLayout.addLayout(ignoreLayout)

        mainLayout.addWidget(generalGroupBox)
        mainLayout.addWidget(overridesGroupBox)
        mainLayout.addWidget(ignoresGroupBox)
        mainLayout.addLayout(mainButtonslayout)

        # UI Updates
        self.connect(portSlider, QtCore.SIGNAL("valueChanged(int)"), portUpdateUi)
        self.connect(resolutionSlider, QtCore.SIGNAL("valueChanged(int)"), resUpdateUi)

        # IPR Updates
        self.connect(self.cameraComboBox, QtCore.SIGNAL("activated(int)"), self.IPRUpdate)
        self.connect(self.resolutionSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.cameraAaSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.renderRegionXSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.renderRegionYSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.renderRegionRSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.renderRegionTSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.IPRUpdate)
        self.connect(self.cameraAaSpinBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)
        self.connect(self.motionBlurCheckBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)
        self.connect(self.subdivsCheckBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)
        self.connect(self.displaceCheckBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)
        self.connect(self.bumpCheckBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)
        self.connect(self.sssCheckBox, QtCore.SIGNAL("toggled(bool)"), self.IPRUpdate)

        self.setLayout(mainLayout)

    def getCamera(self):
        if self.cameraComboBox.currentIndex() == 0:
            camera = self.getSceneOptions()["camera"]
        else:
            try:
                camera = cmds.listRelatives(self.cameraComboBoxDict[self.cameraComboBox.currentIndex()], s=1)[0]
            except TypeError:
                camera = self.cameraComboBoxDict[self.cameraComboBox.currentIndex()]
        return camera

    def IPRUpdate(self):

        try: # If render session is not started yet
            cmds.arnoldIpr(mode='pause')
        except (AttributeError, RuntimeError):
            return

        options = AiUniverseGetOptions()

        # Camera Update
        camera = self.getCamera()
        iterator = AiUniverseGetNodeIterator(AI_NODE_CAMERA);
        while not AiNodeIteratorFinished(iterator):
            node = AiNodeIteratorGetNext(iterator)
            if AiNodeGetName(node) == camera:
                AiNodeSetPtr(options, "camera", node)

        # Resolution and Region Update
        xres = self.getSceneOptions()["width"] * self.resolutionSpinBox.value() / 100
        yres = self.getSceneOptions()["height"] * self.resolutionSpinBox.value() / 100

        AiNodeSetInt(options, "xres", xres)
        AiNodeSetInt(options, "yres", yres)

        rMinX = self.renderRegionXSpinBox.value()
        rMinY = yres - self.renderRegionTSpinBox.value()
        rMaxX = self.renderRegionRSpinBox.value() -1
        rMaxY = (yres - self.renderRegionYSpinBox.value()) - 1

        if (rMinX >= 0) and (rMinY >= 0) and (rMaxX <= xres) and (rMaxY <= yres):
            AiNodeSetInt(options, "region_min_x", rMinX)
            AiNodeSetInt(options, "region_min_y", rMinY)
            AiNodeSetInt(options, "region_max_x", rMaxX)
            AiNodeSetInt(options, "region_max_y", rMaxY)
        else:
            AiNodeSetInt(options, "region_min_x", 0)
            AiNodeSetInt(options, "region_min_y", 0)
            AiNodeSetInt(options, "region_max_x", xres-1)
            AiNodeSetInt(options, "region_max_y", yres-1)

        # Camera AA Update
        cameraAA = self.cameraAaSpinBox.value()
        options = AiUniverseGetOptions()
        AiNodeSetInt(options, "AA_samples", cameraAA)

        # Ignore options Update
        AASamples = self.cameraAaSpinBox.value()
        motionBlur = self.motionBlurCheckBox.isChecked()
        subdivs = self.subdivsCheckBox.isChecked()
        displace = self.displaceCheckBox.isChecked()
        bump = self.bumpCheckBox.isChecked()
        sss = self.sssCheckBox.isChecked()

        AiNodeSetBool(options, "ignore_motion_blur", motionBlur)
        AiNodeSetBool(options, "ignore_subdivision", subdivs)
        AiNodeSetBool(options, "ignore_displacement", displace)
        AiNodeSetBool(options, "ignore_bump", bump)
        AiNodeSetBool(options, "ignore_sss", sss)

        try:
            cmds.arnoldIpr(mode='unpause')
        except RuntimeError:
            pass

    def render(self):

        try: # If MtoA was not found
            defaultTranslator = cmds.getAttr("defaultArnoldDisplayDriver.aiTranslator")
        except ValueError:
            cmds.warning("MtoA was not found.")
            return

        try: # If Aton driver for Arnold is not installed
            cmds.setAttr("defaultArnoldDisplayDriver.aiTranslator", "aton", type="string")
        except RuntimeError:
            cmds.warning("Aton driver for Arnold is not installed")
            return

        camera = self.getCamera()

        if camera != None:
            # Updating the port
            port = self.portSpinBox.value()
            cmds.setAttr("defaultArnoldDisplayDriver.port", port)

            # Adding time changed callback
            if self.timeChange == None:
                self.timeChange = OM.MEventMessage.addEventCallback("timeChanged", self.updateFrame)

            try: # If render session is not started yet
                cmds.arnoldIpr(mode='stop')
            except RuntimeError:
                pass

            # Temporary make default cameras visible before scene export
            hiddenCams = []
            for cam in cmds.listCameras():
                camShape = cmds.listRelatives(cam, s=1)[0]
                visible = cmds.getAttr("%s.visibility"%cam) and cmds.getAttr("%s.visibility"%camShape)
                if not visible:
                    hiddenCams.append(cam)
                    cmds.showHidden(cam)

            # Start IPR
            cmds.arnoldIpr(cam=camera, mode='start')

            # Update IPR
            self.IPRUpdate()
            sys.stdout.write("// Info: Aton - Render started.\n")

            # Setting back to options default
            for i in hiddenCams: cmds.hide(i)
            cmds.setAttr("defaultArnoldDisplayDriver.aiTranslator", defaultTranslator, type="string")
            cmds.setAttr("defaultArnoldDisplayDriver.port", self.defaultPort)
        else:
            cmds.warning("Camera is not selected!")

    def stop(self):
        if self.timeChange != None:
            OM.MEventMessage.removeCallback(self.timeChange)
            self.timeChange = None
        try:
            cmds.arnoldIpr(mode='stop')
            sys.stdout.write("// Info: Aton - Render stopped.\n")
        except (AttributeError, RuntimeError):
            return

    def updateFrame(self, *args):
        options = AiUniverseGetOptions()
        time = cmds.currentTime(q=1)
        AiNodeSetFlt(options, "frame", time)

    def getNukeCropNode(self, *args):

        def find_between( s, first, last ):
            try:
                start = s.index( first ) + len( first )
                end = s.index( last, start )
                return s[start:end]
            except ValueError:
                return ""

        clipboard = QtGui.QApplication.clipboard()
        data = clipboard.text()

        checkData1 = "set cut_paste_input [stack 0]"
        checkData2 = "Crop {"

        if (checkData1 in data.split('\n', 10)[0]) and \
           (checkData2 in data.split('\n', 10)[3]):
                cropData = find_between(data.split('\n', 10)[4], "box {", "}" ).split()
                nkX, nkY, nkR, nkT = int(float(cropData[0])),\
                                     int(float(cropData[1])),\
                                     int(float(cropData[2])),\
                                     int(float(cropData[3]))

                self.renderRegionXSpinBox.setValue(nkX)
                self.renderRegionYSpinBox.setValue(nkY)
                self.renderRegionRSpinBox.setValue(nkR)
                self.renderRegionTSpinBox.setValue(nkT)

                return cropData

if __name__ == "__main__":
    rc = Aton()
    rc.show()
