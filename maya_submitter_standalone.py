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
        sharedPath = cmds.textField( "sharedPath", w=400 )
        selectPathButton = cmds.button(label = "...", command=self.pickSharedPath, width=25)
        cmds.setParent("..")

        cmds.text( label='base URL' )
        baseURL = cmds.textField( "baseURL", text="http://dire.btf.de" )

        cmds.text( label='username' )
        username = cmds.textField( "username" )

        cmds.text( label='password' )
        password = cmds.textField( "password" )
        
        cmds.text( label='block size' )
        blockSize = cmds.textField( "blockSize", w=200 )
        
        cmds.text( label = '')
        
        cmds.columnLayout()
        
        cmds.rowLayout(numberOfColumns=7)
        transcodeResult = cmds.checkBox( 'transcode_result' )
        
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
        labels = ["sharedPath", "baseURL", "username", "password", "blockSize"]
        checkboxes = ["transcode_result", "h264", "prores", "dnxhd", "proxy"]
        
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
        
        for label in ["sharedPath", "baseURL", "username", "password", "blockSize"]:    
            inputs[label] = cmds.textField( label, query=True, text=True )

        inputs["fps"] = cmds.intField( "fps", query=True, value=True )
            
        for checkbox in ["transcode_result", "h264", "prores", "dnxhd", "proxy"]:
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

        for label in ["sharedPath","baseURL","username","password"]:
            if not self.config[label]:
                self.message('%s is not set' % (label))
                return

        

        if not check_saved():
            self.message( "Project must be saved first")
            return

        if not cmds.file(query=True, sceneName=True).startswith(self.config["sharedPath"]) or not self.project_directory():
            self.message('Project is not saved on shared path')
            return
        
        login_url = urlparse.urljoin(self.config['baseURL'], 'admin/')
        add_url = urlparse.urljoin(login_url, 'tasks/mayaproject/add/')
        cookies = urllib2.HTTPCookieProcessor()
        urlopen = urllib2.build_opener(cookies)
        csrftoken = ''      

        self.info(login_url)
        try:
            page = urlopen.open(login_url)
        except urllib2.HTTPError as e:
            self.info("HTTP Error code: " + str(e.code))
            raise

        
        for cookie in cookies.cookiejar:
            if cookie.name == 'csrftoken':
                csrftoken = cookie.value
        params = urllib.urlencode([('csrfmiddlewaretoken', csrftoken),
                                   ('username', self.config['username']),
                                   ('password', self.config['password']),
                                   ('this_is_the_login_form', '1'),
                                   ('next', '/admin/')])
        page = urlopen.open(login_url, params)
        content = page.read()
        if "Welcome," not in content:
            self.message('Login unsuccessful')
            return

        submit_path = self.submit_path()
        self.info( "Submit Path: " + submit_path )
        if os.path.exists(submit_path):
            if cmds.confirmDialog(message='File was already submitted, submit again? (overwrites submitted file)', button=["Yes","No"], defaultButton="No", dismissString="No", cancelButton="No") == "No":
                return
            cmds.sysFile(submit_path, delete=True)
        if not make_paths_relative():
            return
        
        #copy project file to submit_path
        src = cmds.file(query=True, sceneName=True)
        cmds.sysFile(src, copy=submit_path)
        
        post_hook = ''
        if self.config['transcode_result']:
            post_hook = '0'
        post_hook_options = {'fps': self.config['fps']}
        if self.config['proxy']:
            post_hook_options['proxy'] = True
        if self.config['h264']:
            post_hook_options['h264'] = True
        if self.config['prores']:
            post_hook_options['prores'] = True
        if self.config['dnxhd']:
            post_hook_options['dnxhd'] = True
        post_hook_options = json.dumps(post_hook_options)

        params = [('csrfmiddlewaretoken', csrftoken),
                  ('tasks-job-content_type-object_id-TOTAL_FORMS', '1'),
                  ('tasks-job-content_type-object_id-INITIAL_FORMS', '0'),
                  ('tasks-job-content_type-object_id-0-status', '0'),
                  ('tasks-job-content_type-object_id-0-priority', '50'),
                  ('tasks-job-content_type-object_id-0-pool', '1'),
                  ('tasks-job-content_type-object_id-0-post_hook', post_hook),
                  ('tasks-job-content_type-object_id-0-post_hook_options', post_hook_options),
                  ('project_file', self.relative_path()),
                  ('project_directory', self.project_directory()),
                  ('block_size', self.config['blockSize']),
                  ('frame_start', str(int(cmds.playbackOptions(query=True, ast=True)))),
                  ('frame_end', str(int(cmds.playbackOptions(query=True, aet=True)))),
                  ('_save', 'Save')]
        
        page = urlopen.open(add_url, urllib.urlencode(params))
        content = page.read()
        if 'added successfully' not in content:
            self.info(content)
            self.message('Job submission failed')
            return
        self.message('Job submission successful')
            
    def project_directory(self):
        path = cmds.workspace(query=True, rootDirectory=True)
        if not path.startswith(self.config['sharedPath']):
            return false
        else:
            relative_path = path[len(self.config['sharedPath']):]
            while relative_path.startswith('/'):
                relative_path = relative_path[1:]
            return relative_path
    
    def pickSharedPath(self,*args):
        path = openFileDialog()
        if path != "":
            cmds.textField("sharedPath",edit=True,text=path)

    def submit_path(self):
        path = cmds.file(query=True, sceneName=True)
        name, ext = os.path.splitext(path)
        dirname, basename = os.path.split(name)
        return os.path.join(dirname, '_' + basename + '_submit' + ext).replace(os.sep, '/')

    def relative_path(self):
        relative_path = self.submit_path()[len(self.config['sharedPath']):]
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
