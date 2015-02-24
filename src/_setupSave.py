'''
Created on Feb 10, 2015

@author: qurban.ali
'''
from loader.command.python import RedshiftAOVTools
import pymel.core as pc
import os.path as osp
import os
import uiContainer
from PyQt4.QtGui import QMessageBox, QPushButton
import appUsageApp
import fillinout
import msgBox
reload(msgBox)
import qtify_maya_window as qtfy
import re
import maya.cmds as cmds

__title__ = 'Setup & Save Scene'
__ep_regex__ = 'EP\d{2}'
__seq_regex__ = 'SQ\d{3}'
__sh_regex__ = 'SH\d{3}'

def showMessage(msg=''):
    pc.confirmDialog(title='Setup & Save Scene',
                     message=msg, button='Ok')

def createLogFile():
    pass

def getCacheFiles():
    return pc.ls(type='cacheFile')

def getMatch(regex):
    files = getCacheFiles()
    val = None
    while files:
        phile = files.pop()
        match = re.search(regex, phile.cp.get())
        if match:
            val = match.group()
    return val

def setRenderableCamera(camera):
    for cam in pc.ls(cameras=True):
        if cam.renderable.get():
            cam.renderable.set(False)
    camera.renderable.set(True)
            

def setResolution():
    node = pc.ls('defaultResolution')[0]
    node.width.set(1920)
    node.height.set(1080)
    pc.setAttr("defaultResolution.deviceAspectRatio", 1.777)
    pc.mel.redshiftUpdateResolution()
    
def camExists(match):
    for cam in pc.ls(cameras=True):
        if match in cam.firstParent().name():
            return cam
    return False

def fileExists(path, fileName):
    for name in os.listdir(path):
        try:
            return re.search(fileName+'_v\d{3}', name)
        except:
            pass

def getLastVersion(path, fileName, next=False):
    versions = []
    for version in os.listdir(path):
        try:
            versions.append(int(re.search('_v\d{3}', version).group().split('v')[-1]))
        except AttributeError:
            pass
    if versions:
        temp = max(versions) + 1 if next else max(versions)
        return fileName +'_v'+ str(temp).zfill(3)
        
def saveScene(path, fileName):
    if fileExists(path, fileName):
        versionButton = QPushButton('Create Version')
        versionButton.setToolTip('Create a new version')
        overwriteButton = QPushButton('Overwrite Existing')
        overwriteButton.setToolTip('Overwrite the last version')
        btn = msgBox.showMessage(qtfy.getMayaWindow(), title=__title__,
                                 msg='File already exists for this shot',
                                 ques='What do you wnat to do?',
                                 icon=QMessageBox.Question,
                                 btns=QMessageBox.Cancel,
                                 customButtons=[overwriteButton, versionButton])
        if btn == versionButton:
            fileName = getLastVersion(path, fileName, next=True)
        elif btn == overwriteButton:
            fileName = getLastVersion(path, fileName)
            for phile in os.listdir(path):
                if osp.splitext(phile)[0] == fileName:
                    try:
                        os.remove(osp.join(path, phile))
                    except Exception as ex:
                        showMessage('Could not overwrite the existing file\n'+str(ex))
                        return
        else:
            return
    else:
        fileName += '_v001'
    fullPath = osp.join(path, fileName)
    typ = cmds.file(q=True, type=True)[0]
    fullPath += '.mb' if typ == 'mayaBinary' else '.ma'
    cmds.file(rename=fullPath)
    cmds.file(f=True, save=True, options="v=0;", type=typ)


def setupScene():
    if pc.mel.currentRenderer().lower() != 'redshift':
        pc.mel.setCurrentRenderer('redshift')
    ep = getMatch(__ep_regex__)
    seq = getMatch(__seq_regex__)
    sh = getMatch(__sh_regex__)
    
    if not ep:
        showMessage('Could not find Episode number form the scene')
        return
    if not seq:
        showMessage('Could not find Sequence number from the scene')
        return
    if not sh:
        showMessage('Could not find Shot number from the scene')
        return
    
    camPrefix = '_'.join([seq, sh])
    cam = camExists(camPrefix)
    if not cam:
        showMessage('Could not find a camera containing %s'%camPrefix)
    else:
        setRenderableCamera(cam)
        pc.setAttr("defaultRenderGlobals.animation", 1)
        pc.select(cam)
        try:
            start, end = fillinout.fill()
            pc.setAttr("defaultRenderGlobals.extensionPadding", len(str(int(max([start, end])))))
        except:
            showMessage('Could not find keyframes on selected camera')
        pc.select(cl=True)
    
    # set image format to openEXR
    pc.setAttr("redshiftOptions.imageFormat", 1)
    
    pc.setAttr("redshiftOptions.imageFilePrefix", "<Camera>/<RenderLayer>/<RenderLayer>_<AOV>/<RenderLayer>_<AOV>_", type="string")
    
    RedshiftAOVTools.fixAOVPrefixes()
    
    setResolution()
    
    #pc.inViewMessage(amg='<hl>Scene setup successful</hl>', pos='midCenter', fade=True )
    #path = osp.join(r'D:\shot_test', ep, 'SEQUENCES', seq, 'SHOTS', '_'.join([seq, sh]), 'lighting', 'files')
    path = osp.join(r'P:\external\Al_Mansour_Season_02\02_production', ep, 'SEQUENCES', seq, 'SHOTS', '_'.join([seq, sh]), 'lighting', 'file')
    if not osp.exists(path):
        msgBox.showMessage(qtfy.getMayaWindow(), title=__title__,
                           msg='Unable to save the file because the system could not find the constructed path\n'+path,
                           icon=QMessageBox.Information)
        return
    fileName = '_'.join([ep, seq, sh])
    btn = msgBox.showMessage(qtfy.getMayaWindow(), title=__title__,
                             msg='Your scene will be saved at\n'+path,
                             icon=QMessageBox.Question,
                             ques='Do you want to proceed?',
                             btns=QMessageBox.Yes|QMessageBox.No)
    if btn == QMessageBox.No:
        return
    saveScene(path, fileName)
        
    appUsageApp.updateDatabase('setupSaveScene')