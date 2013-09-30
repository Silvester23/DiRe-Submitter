import bpy

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


class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "DiRe Submitter"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text=" Simple Row:")

        row = layout.row()
        row.prop(scene, "shared_path")


def register():
    bpy.types.Scene.my_string_prop = bpy.props.StringProperty \
      (
        name = "My String",
        description = "My description",
        default = "default"
      )
    bpy.utils.register_class(LayoutDemoPanel)


def unregister():
    bpy.utils.unregister_class(LayoutDemoPanel)


if __name__ == "__main__":
    register()
