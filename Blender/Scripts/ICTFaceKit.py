import os
import json
import itertools

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator


def loadICTFaceModel(folderpath):
    # Define names to use
    face_model_name = "ICTFaceModel"
    generic_neutral_filename = "generic_neutral_mesh.obj"
    identity_morph_target_name = "identity{:03d}"
    config_filename = "vertex_indices.json"
    
    # Specify paths
    generic_neutral_filepath = os.path.join(folderpath, generic_neutral_filename)
    config_filepath = os.path.join(folderpath, config_filename)
    config = None
    
    # Load settings
    with open(config_filepath) as jsonContent:
        config = json.load(jsonContent)    
    if config == None:
        return
    
    # Load generic neutral
    bpy.ops.import_scene.obj(filepath = generic_neutral_filepath)
    face_model_neutral_object = bpy.context.selected_objects[0]
    face_model_neutral_object.name = face_model_name
    
    # Load expression morph targets
    expression_names = []
    expression_models = []
    for expression_name in config['expressions']:
        print("Reading expression morph target: " + expression_name)
        filename = expression_name + '.obj'
        filepath = os.path.join(folderpath, filename)
        bpy.ops.import_scene.obj(filepath = filepath)
        imported_object = bpy.context.selected_objects[0]
        imported_object.name = expression_name
    
        expression_names.append(expression_name)
        expression_models.append(imported_object)
    
    identity_names = []
    identity_models = []
    # Load identity morph targets
    for identity_num in itertools.count():
        identity_name = identity_morph_target_name.format(identity_num)
        identity_filename = identity_name + ".obj"
        filepath = os.path.join(folderpath, identity_filename)
        
        try:
            print("Reading identity morph target: " + identity_name)
            bpy.ops.import_scene.obj(filepath = filepath)
            imported_object = bpy.context.selected_objects[0]
            imported_object.name = identity_name
        
            identity_names.append(identity_name)
            identity_models.append(imported_object)
        except Exception as e:
            print("Unable to read identity morph target. Continuing...")
            break
        else:
            continue
        finally:
            pass
    
    # Select all shape models
    for expression_model in expression_models:
        expression_model.select_set(True)
    for identity_model in identity_models:
        identity_model.select_set(True)
    bpy.context.view_layer.objects.active = face_model_neutral_object
   
    # Create blendshapes
    bpy.ops.object.join_shapes()

    # Delete selected shape objects
    bpy.ops.object.delete()

class BrowseFaceModel(Operator, ImportHelper):
    bl_idname = "ict_face_kit.browsemodel"
    bl_label = "Load model"
    
    filter_glob: StringProperty(
        default='',
        options={'HIDDEN'}
    )
    some_boolean: BoolProperty(
        name='Do a thing',
        description='Do a thing with the file you\'ve selected',
        default=True,
    )
    def execute(self, context):
        filename, extension = os.path.splitext(self.filepath)
        print('Selected file:', self.filepath)
        print('File name:', filename)
        print('File extension:', extension)
        print('Some Boolean:', self.some_boolean)

        loadICTFaceModel(filename)
        
        return {'FINISHED'}

class ICTFaceKitPanel(bpy.types.Panel):
    bl_idname = "panel.ict_face_kit_panel"
    bl_label = "ICT FaceKit"
    
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ICT FaceKit'

    def draw(self, context):
        self.layout.operator("ict_face_kit.browsemodel", icon='FILEBROWSER', text="Load Face Model")

def register() :
    bpy.utils.register_class(BrowseFaceModel)
    bpy.utils.register_class(ICTFaceKitPanel)
    

def unregister() :
    bpy.utils.unregister_class(BrowseFaceModel)
    bpy.utils.unregister_class(ICTFaceKitPanel)

if __name__ == "__main__" :
    register()