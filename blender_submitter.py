import bpy
import os
import json
import sys
import imp
import submit_to_dire
imp.reload(submit_to_dire)

bl_info = {
    "name": "DiRe Submitter",
    "author": "Jan Murmann",
    "version": (1, 0),
    "blender": (2, 65, 0),
    "location": "Properties > Render",
    "description": "Adds a panel to submit a render job to the DiRe tool",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}
    
def write_config(config_path,config):
    with open(config_path,"w") as fh:
        fh.write(json.dumps(config))

def read_config(config_path):
    if(os.path.exists(config_path)):
        with open(config_path, "r") as fh:
            config = json.loads(fh.read())
        return config
    else:
        return False

def get_submit_path(src_path):
    name, ext = os.path.splitext(src_path)
    dirname, basename = os.path.split(name)
    return os.path.join(dirname, '_' + basename + '_submit' + ext).replace(os.sep, '/')

def read_inputs(context):
    config = {}
    inputs = ["shared_path", "base_url", "username", "password", "block_size", "posthook", "h264", "fps", "prores", "dnxhd", "proxy"]
    for i in inputs:
        config[i] = eval("context.scene.dire_%s" %(i))
    return config

class DiRePanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "DiRe Submitter"
    bl_idname = "dire.DiRePanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    defaults = {
        "shared_path": "X:",
        "base_url": "http://dire.btf.de",
        "username": "btf",
        "password": "",
        "block_size": 10,
        "fps": 25,
        "posthook": False,
        "h264": True,
        "prores": False,
        "dnxhd": False,
        "proxy": False
    }
    
    config_path = os.path.join(bpy.utils.user_resource("CONFIG"),"dire_submitter_config.txt")
    config = read_config(config_path)
    if config != False:
        for key in config.keys():
            defaults[key] = config[key]
    
    # Define types
    bpy.types.Scene.dire_shared_path = bpy.props.StringProperty (
        name = "Shared Path",
        description = "Shared Path. Usually either X: or /Volumes/grid",
        default = defaults["shared_path"]
      )
      
    bpy.types.Scene.dire_base_url = bpy.props.StringProperty (
        name = "Base URL",
        description = "URL of the DiRe Tool",
        default = defaults["base_url"]
      )
      
    bpy.types.Scene.dire_username = bpy.props.StringProperty  (
        name = "Username",
        description = "DiRe Tool username",
        default = defaults["username"]
      )
      
    bpy.types.Scene.dire_password = bpy.props.StringProperty (
        name = "Password",
        description = "DiRe Tool password",
        default = defaults["password"]
      )
    
    bpy.types.Scene.dire_block_size = bpy.props.IntProperty (
        name = "Block size",
        description = "Block size",
        default = defaults["block_size"]
      )
      
    bpy.types.Scene.dire_fps = bpy.props.IntProperty (
        name = "fps",
        description = "fps",
        default = defaults["fps"]
      )
      
    bpy.types.Scene.dire_posthook = bpy.props.BoolProperty (
        name = "Transcode result",
        description = "Transcode result",
        default = defaults["posthook"]
      )  
      
    bpy.types.Scene.dire_h264 = bpy.props.BoolProperty (
        name = "h264",
        description = "h264",
        default = defaults["h264"]
      )
    
    bpy.types.Scene.dire_prores = bpy.props.BoolProperty (
        name = "prores",
        description = "Prores",
        default = defaults["prores"]
      )
    
    bpy.types.Scene.dire_dnxhd = bpy.props.BoolProperty (
        name = "dnxhd",
        description = "dnxhd",
        default = defaults["dnxhd"]
      )
    bpy.types.Scene.dire_proxy = bpy.props.BoolProperty (
        name = "proxy",
        description = "proxy",
        default = defaults["proxy"]
      )
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align = True)
        
        col.prop(scene, "dire_shared_path")  
        col.prop(scene, "dire_base_url")
        col.prop(scene, "dire_username")
        col.prop(scene, "dire_password")
        col.prop(scene, "dire_block_size")

        row = col.row()
        row.prop(scene, "dire_posthook")
        row.prop(scene, "dire_h264")
        row.prop(scene, "dire_fps")
        row.prop(scene, "dire_prores")                
        row.prop(scene, "dire_dnxhd")           
        row.prop(scene, "dire_proxy")
        
        layout.operator("dire.submit")

def submit():
    config = DiRePanel.config
    src_path = DiRePanel.src_path
    frame_start = DiRePanel.frame_start
    frame_end = DiRePanel.frame_end
    return submit_to_dire.submit_to_dire([config,"blenderscene",src_path,frame_start,frame_end])


class SubmitButton(bpy.types.Operator):
    bl_idname = "dire.submit"
    bl_label = "Submit"
 
    def execute(self, context):
        imp.reload(submit_to_dire)
        config = read_inputs(context)
        write_config(DiRePanel.config_path,config)
        
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        src_path = bpy.data.filepath
        submit_path = get_submit_path(src_path)
        render_path = os.path.abspath(bpy.path.abspath(context.scene.render.filepath))
        
        DiRePanel.config = config
        DiRePanel.src_path = src_path
        DiRePanel.submit_path = submit_path        
        DiRePanel.frame_start = frame_start
        DiRePanel.frame_end = frame_end
                
        if not src_path.startswith(config["shared_path"]):
            popup("Scene is not saved on shared path.")
            return{'CANCELLED'}
        
        if not render_path.startswith(os.path.abspath(config["shared_path"])):
            popup("Output is not on shared path")
            return{'CANCELLED'}
        
        if os.path.exists(submit_path):
            bpy.ops.object.confirm_operator('INVOKE_DEFAULT')
            return{'CANCELLED'}
        
        popup(submit())
        return{'FINISHED'}
    
def popup(message):
    PopupOperator.message = message
    bpy.ops.object.popup_operator('INVOKE_DEFAULT')
    
class PopupOperator(bpy.types.Operator):
    bl_idname = "object.popup_operator"
    bl_label = "Message"
    message = "Default Popup Message"
    def execute(self, context):
        return{'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
    
    def draw(self, context):
        layout = self.layout
        layout.label(self.message)

class ConfirmOperator(bpy.types.Operator):
    bl_idname = "object.confirm_operator"
    bl_label = "Project already submitted. Submit again? (Overwrites file)"
 
    def execute(self, context):
        popup(submit())
        return{'FINISHED'}
 
    def invoke(self, context, event):
        context.window_manager.invoke_confirm(self,event)
        return{'FINISHED'}        

def register():
    bpy.utils.register_class(DiRePanel)
    bpy.utils.register_class(SubmitButton)
    bpy.utils.register_class(ConfirmOperator)    
    bpy.utils.register_class(PopupOperator)

def unregister():
    bpy.utils.unregister_class(DiRePanel)
    bpy.utils.unregister_class(SubmitButton)
    bpy.utils.unregister_class(ConfirmOperator)  
    bpy.utils.unregister_class(PopupOperator)      

if __name__ == "__main__":
    register()