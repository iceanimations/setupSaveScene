'''
Created on Feb 10, 2015

@author: qurban.ali
'''
import pymel.core as pc
from loader.command.python import RedshiftAOVTools
import fillinout
reload(fillinout)
import re

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
    
    pc.inViewMessage(amg='<hl>Scene setup successful</hl>', pos='midCenter', fade=True )
    
    

def saveScene():
    pass