import sys
import os
import pprint
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import json
import urllib, urllib2, urlparse

# Command
class Submitter(OpenMayaMPx.MPxCommand):
        
    def showSubmitter(self):
        self.config = _read_config('submit')
        if cmds.window("Submit Render",exists=True):
            cmds.deleteUI("Submit Render")
        
        submitterWindow = cmds.window( "Submit Render", sizeable=True, rtf=True )
        
        cmds.columnLayout("mainLayout", w=100)
        
        cmds.rowColumnLayout( numberOfColumns=2, columnAttach=(1, 'right', 0), rowAttach=(1,'top',0) )
        cmds.text( label='info')
        infoField = cmds.scrollField( "info", h=250, editable=False)
        
        cmds.text( label='shared path' )
        cmds.rowLayout( numberOfColumns=2, columnWidth=(2,25) )
        shared_path = cmds.textField( "shared_path", w=400 )
        selectPathButton = cmds.button(label = "...", command=self.pickshared_path, width=25)
        cmds.setParent("..")

        cmds.text( label='base URL' )
        base_url = cmds.textField( "base_url", text="http://dire.btf.de" )

        cmds.text( label='username' )
        username = cmds.textField( "username", text="btf" )

        cmds.text( label='password' )
        password = cmds.textField( "password" )
        
        cmds.text( label='block size' )
        block_size = cmds.textField( "block_size", w=200 )
        
        cmds.text( label = '')
        
        cmds.columnLayout()
        
        cmds.rowLayout(numberOfColumns=7)
        posthook = cmds.checkBox( 'posthook' )
        
        cmds.text( label='fps' )
        fps = cmds.intField( "fps", w=50, value=25 )
        
        h264 = cmds.checkBox( 'h264', value=True )
        prores = cmds.checkBox( 'prores' )
        dnxhd = cmds.checkBox( 'dnxhd' )
        proxy = cmds.checkBox( 'proxy' )

        cmds.setParent("..")
        
        cmds.text( label='' )
        submitButton = cmds.button( label='save and submit', command=self.submit )
        
        self.populateInputs()
        
        cmds.showWindow( submitterWindow )
    
    
    def populateInputs(self):
        labels = ["shared_path", "base_url", "username", "password", "block_size"]
        checkboxes = ["posthook", "h264", "prores", "dnxhd", "proxy"]
        
        for key in self.config:
            if key in labels:
                cmds.textField( key, edit=True, text=self.config[key] )
            elif key in checkboxes:
                cmds.checkBox( key, edit=True, value=self.config[key] )
        if "fps" in self.config:
            print self.config["fps"]
            cmds.intField( "fps", edit=True, value=self.config["fps"] )
        
        
    def readAllInputs(self):
        inputs = {}
        
        for label in ["shared_path", "base_url", "username", "password", "block_size"]:    
            inputs[label] = cmds.textField( label, query=True, text=True )

        inputs["fps"] = cmds.intField( "fps", query=True, value=True )
            
        for checkbox in ["posthook", "h264", "prores", "dnxhd", "proxy"]:
            inputs[checkbox] = cmds.checkBox( checkbox, query=True, value=True)

        
        return inputs

    def message(self, message):
        cmds.confirmDialog( message=message, button=['OK'], defaultButton='OK' )

    def info(self, message):
        cmds.scrollField( "info", edit=True, insertText=message+"\n\r" )
        
    def submit(self,*args):
        self.info("starting submit")
        self.config = self.readAllInputs()
        _write_config("submit",self.config)

        for label in ["shared_path","base_url","username","password"]:
            if not self.config[label]:
                self.message('%s is not set' % (label))
                return

        if not check_saved():
            self.message( "Project must be saved first")
            return

        if not cmds.file(query=True, sceneName=True).startswith(self.config["shared_path"]) or not self.project_directory():
            self.message('Project is not saved on shared path')
            return
            
        if os.path.exists(self.submit_path()):
            if cmds.confirmDialog(message='File was already submitted, submit again? (overwrites submitted file)', button=["Yes","No"], defaultButton="No", dismissString="No", cancelButton="No") == "No":
                return
            cmds.sysFile(self.submit_path(), delete=True)
        if not make_paths_relative():
            return
        
        src_path = cmds.file(query=True, sceneName=True)
        frame_start = int(cmds.playbackOptions(query=True, ast=True))
        frame_end = int(cmds.playbackOptions(query=True, aet=True))
        
        sys.path.append(os.path.join(self.config["shared_path"],"users/jan/murmann/DiRe-Submitter"))
        import submit_to_dire
        
        self.message(submit_to_dire.submit_to_dire([self.config, "blenderscene", src_path, frame_start, frame_end]))
        
            
    def project_directory(self):
        path = cmds.workspace(query=True, rootDirectory=True)
        if not path.startswith(self.config['shared_path']):
            return false
        else:
            relative_path = path[len(self.config['shared_path']):]
            while relative_path.startswith('/'):
                relative_path = relative_path[1:]
            return relative_path
    
    def pickshared_path(self,*args):
        path = openFileDialog()
        if path != "":
            cmds.textField("shared_path",edit=True,text=path)

    def submit_path(self):
        path = cmds.file(query=True, sceneName=True)
        name, ext = os.path.splitext(path)
        dirname, basename = os.path.split(name)
        return os.path.join(dirname, '_' + basename + '_submit' + ext).replace(os.sep, '/')

    def relative_path(self):
        relative_path = self.submit_path()[len(self.config['shared_path']):]
        while relative_path.startswith('/'):
            relative_path = relative_path[1:]
        return relative_path

def make_paths_relative():
    success = True
    check_saved()
    if not cmds.workspace(query=True, rootDirectory=True):
        return False

    return success


def openFileDialog(*args):
    returnPath = ""
    returnPaths = cmds.fileDialog2(ds=2, fm=3, fileFilter=None)
    if not returnPaths is None:
        returnPath = returnPaths[0]
    return returnPath


def check_saved():
    path = cmds.file(query=True, sceneName=True)
    return not (path is None)


def _read_config(key):
    if not os.path.exists(_config_filename(key)):
        return {}
    content = open(_config_filename(key)).read()
    if content:
        return eval(content)
    return {}

def _write_config(key, config):
    fp = open(_config_filename(key), 'w')
    pprint.pprint(config, fp)
    fp.close()
    
def _config_filename(key):
    prefdir = cmds.internalVar(upd=True)
    return os.path.join(prefdir, ".config_cache_%s.txt" % key)
        
s = Submitter()
s.showSubmitter()
