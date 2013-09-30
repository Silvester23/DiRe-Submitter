import bpy
import os
import json

bl_info = {
    "name": "DiRe Submitter",
    "author": "Jan Murmann",
    "version": (1, 0),
    "blender": (2, 65, 0),
    "location": "VProperties > Render",
    "description": "Adds a panel to submit a render job to the DiRe tool",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"}


class DiRePanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "DiRe Submitter"
    bl_idname = "dire.DiRePanel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    # Define types
    bpy.types.Scene.shared_path = bpy.props.StringProperty (
        name = "Shared Path",
        description = "Shared Path",
        default = "X:"
      )
      
    bpy.types.Scene.base_url = bpy.props.StringProperty (
        name = "Base URL",
        description = "URL of the DiRe Tool",
        default = "http://dire.btf.de"
      )
      
    bpy.types.Scene.username = bpy.props.StringProperty  (
        name = "Username",
        description = "DiRe Tool username",
        default = "btf"
      )
      
    bpy.types.Scene.password = bpy.props.StringProperty (
        name = "Password",
        description = "DiRe Tool password",
        default = ""
      )
    
    bpy.types.Scene.blocksize = bpy.props.IntProperty (
        name = "Block size",
        description = "Block size",
        default = 10
      )
      
    bpy.types.Scene.fps = bpy.props.IntProperty (
        name = "fps",
        description = "fps",
        default = 25
      )
      
    bpy.types.Scene.posthook = bpy.props.BoolProperty (
        name = "Transcode result",
        description = "Transcode result",
        default = False
      )
      
    bpy.types.Scene.h264 = bpy.props.BoolProperty (
        name = "h264",
        description = "Transcode result",
        default = True
      )
    
    bpy.types.Scene.prores = bpy.props.BoolProperty (
        name = "prores",
        description = "Prores",
        default = False
      )
    
    bpy.types.Scene.dnxhd = bpy.props.BoolProperty (
        name = "dnxhd",
        description = "dnxhd",
        default = False
      )

    config_path = os.path.join(bpy.utils.user_resource("CONFIG"),"dire_submitter_config.txt")      
    
#    def __init__(self):    
#        config = self.read_config()
#        if config is not False:
#            self.populate_inputs(config)
    
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene        

        col = layout.column(align = True)
        
        col.prop(scene, "shared_path")  
        col.prop(scene, "base_url")
        col.prop(scene, "username")
        col.prop(scene, "password")
        col.prop(scene, "blocksize")

        row = col.row()
        row.prop(scene, "posthook")
        row.prop(scene, "h264")
        row.prop(scene, "fps")
        row.prop(scene, "prores")                
        row.prop(scene, "dnxhd")           
        
        layout.operator("dire.submit")
        
    def populate_inputs(self,config):
        for i in config.keys():
            if type(config[i]) is str:
                #eval("context.scene.%s = \"%s\"" % (i, config[i]))
                pass
            else:
                pass
                #eval("context.scene.%s = %s" % (i, config[i]))

        
    def read_inputs(self,context):
        config = {}
        inputs = ["shared_path", "base_url", "username", "password", "blocksize", "posthook", "h264", "fps", "prores", "dnxhd"]
        for i in inputs:
            config[i] = eval("context.scene.%s" %(i))
        return config
    
    def write_config(self,config):
        with open(self.config_path,"w") as fh:
            fh.write(json.dumps(config))
    
    def read_config(self):
        if(os.path.exists(self.config_path)):
            with open(self.config_path, "r") as fh:
                config = json.loads(fh.read())
            return config
        else:
            return False


class OBJECT_OT_SubmitButton(bpy.types.Operator):
    bl_idname = "dire.submit"
    bl_label = "Submit"
 
    def execute(self, context):
        config = DiRePanel.read_inputs(DiRePanel,context)
        #DiRePanel.write_config(DiRePanel,config)
        
        frame_start = context.scene.frame_start
        frame_end = context.scene.frame_end
        filepath = bpy.data.filepath        
        
        print(config)
        #print(frame_start, frame_end)
        return{'FINISHED'}
            
    

def register():
    bpy.utils.register_class(DiRePanel)
    bpy.utils.register_class(OBJECT_OT_SubmitButton)


def unregister():
    bpy.utils.unregister_class(DiRePanel)
    bpy.utils.unregister_class(OBJECT_OT_SubmitButton)


if __name__ == "__main__":
    register()