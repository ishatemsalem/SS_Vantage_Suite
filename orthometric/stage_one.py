import bpy
import math
import os

def import_assets(self, context):
    # append assets from local blend file
    base_path = os.path.dirname(__file__)
    blend_path = os.path.join(base_path, "assets", "heads.blend")
    
    if not os.path.exists(blend_path):
        self.report({'ERROR'}, f"Asset file not found at: {blend_path}")
        return False

    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        if "OM_Assets" in data_from.collections:
            data_to.collections = ["OM_Assets"]
        else:
            self.report({'ERROR'}, "Collection 'OM_Assets' not found in library")
            return False

    for col in data_to.collections:
        if col is not None:
            context.scene.collection.children.link(col)
            for obj in col.objects:
                if obj.name in ["OM_Cage", "OM_Anchor_TearDuct", "OM_Anchor_Chin"]:
                    obj.show_in_front = True 
    return True

class ORTHOMETRIC_OT_init_front(bpy.types.Operator):
    # init front view & import assets
    bl_idname = "orthometric.init_front"
    bl_label = "Import Front Image"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        props = scene.orthometric

        if not import_assets(self, context):
            return {'CANCELLED'}

        # camera setup
        cam_data = bpy.data.cameras.new(name="Ortho_Cam_Front")
        cam_obj = bpy.data.objects.new("Ortho_Cam_Front", cam_data)
        scene.collection.objects.link(cam_obj)
        
        # fixed: use ratio formula for initial pos
        # formula: y = (fl / 50.0) * (2.0 + offset)
        base_dist = 2.0
        ratio = props.focal_length_front / 50.0
        calc_y = ratio * (base_dist + props.front_cam_y)
        
        cam_obj.location = (0, calc_y, 1.47)
        cam_obj.rotation_euler = (math.radians(90), 0, math.radians(180))
        cam_data.lens = props.focal_length_front
        scene.camera = cam_obj

        # image setup
        if not self.filepath: return {'CANCELLED'}

        # image placed at y=0, not parented to cam
        bpy.ops.object.empty_add(type='IMAGE', location=(0, 0, 1.47))
        img_obj = context.active_object
        img_obj.name = "Ref_Img_Front"
        img_obj.rotation_euler = (math.radians(90), 0, math.radians(180))
        img_obj.empty_display_size = 0.9
        
        try:
            img_obj.data = bpy.data.images.load(self.filepath)
        except:
            pass
        
        # trigger update
        props.focal_length_front = props.focal_length_front

        # force viewport to camera
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'

        img_obj.rotation_mode = 'XYZ'
        img_obj.rotation_euler = (math.radians(90), 0, math.radians(180))

        props.stage = 'FRONT_SETUP'
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ORTHOMETRIC_OT_center_tool(bpy.types.Operator):
    # start centering tool
    bl_idname = "orthometric.center_tool"
    bl_label = "Center Image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        img_obj = bpy.data.objects.get("Ref_Img_Front")
        if not img_obj: return {'CANCELLED'}

        # helper generated at 0, 0, -2.5
        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, -2.5))
        helper = context.active_object
        helper.name = "Helper_Center"
        helper.rotation_euler = (0, 0, 0)
        helper.scale = (10, 10, 10)

        # 0 = x, 1 = y, 2 = z
        helper.lock_location[1] = True
        helper.lock_location[2] = True
        helper.lock_rotation[0] = True
        helper.lock_rotation[1] = True
        helper.lock_rotation[2] = True
        
        bpy.ops.object.select_all(action='DESELECT')
        helper.select_set(True)
        context.view_layer.objects.active = helper
        
        props.is_centering = True
        return {'FINISHED'}


class ORTHOMETRIC_OT_confirm_center(bpy.types.Operator):
    # confirm centering
    bl_idname = "orthometric.confirm_center"
    bl_label = "Confirm"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        img_obj = bpy.data.objects.get("Ref_Img_Front")
        helper = bpy.data.objects.get("Helper_Center")

        if img_obj and helper:
            img_obj.parent = helper
            img_obj.matrix_parent_inverse = helper.matrix_world.inverted()
            helper.location.x = 0
            context.view_layer.update()
            bpy.ops.object.select_all(action='DESELECT')
            img_obj.select_set(True)
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.data.objects.remove(helper)

        props.is_centering = False
        return {'FINISHED'}

## Stage 1.1.3: Calibration

class ORTHOMETRIC_OT_start_calibration(bpy.types.Operator):
    # start stage 1.1.3: two-point calibration
    bl_idname = "orthometric.start_calibration"
    bl_label = "Start Calibration"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        
        # 1. get originals
        orig_td = bpy.data.objects.get("OM_Anchor_TearDuct")
        orig_chin = bpy.data.objects.get("OM_Anchor_Chin")
        
        if not (orig_td and orig_chin):
            self.report({'ERROR'}, "Missing Anchors (TearDuct or Chin)!")
            return {'CANCELLED'}
            
        # 2. dup tearduct
        dup_td = orig_td.copy()
        if orig_td.data: dup_td.data = orig_td.data.copy()
        dup_td.name = "OM_Dup_TearDuct"
        context.collection.objects.link(dup_td)
        dup_td.lock_location[1] = True
        
        # 3. dup chin
        dup_chin = orig_chin.copy()
        if orig_chin.data: dup_chin.data = orig_chin.data.copy()
        dup_chin.name = "OM_Dup_Chin"
        context.collection.objects.link(dup_chin)
        dup_chin.lock_location[0] = True
        dup_chin.lock_location[1] = True

        # 4. select both
        bpy.ops.object.select_all(action='DESELECT')
        dup_td.select_set(True)
        dup_chin.select_set(True)
        context.view_layer.objects.active = dup_td
        
        props.stage = 'FRONT_CALIBRATE'
        self.report({'INFO'}, "Align the duplicates to the Image's Tear Duct and Chin")
        return {'FINISHED'}

class ORTHOMETRIC_OT_apply_calibration(bpy.types.Operator):
    # apply scale and pos calibration based on 2 points
    bl_idname = "orthometric.apply_calibration"
    bl_label = "Apply Calibration"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # get objs
        fwd_img = bpy.data.objects.get("Ref_Img_Front")
        
        orig_td = bpy.data.objects.get("OM_Anchor_TearDuct")
        orig_chin = bpy.data.objects.get("OM_Anchor_Chin")
        
        dup_td = bpy.data.objects.get("OM_Dup_TearDuct")
        dup_chin = bpy.data.objects.get("OM_Dup_Chin")
        
        # helper2 gen at 0, 0, 1.47
        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 1.47))
        helper2 = context.active_object
        helper2.name = "Helper2_Center"

        if not (fwd_img and orig_td and orig_chin and dup_td and dup_chin):
            self.report({'ERROR'}, "Missing calibration objects")
            return {'CANCELLED'}
            
        # parent dups to helper2
        for obj in [dup_td, dup_chin, fwd_img]:
            obj.parent = helper2
            obj.matrix_parent_inverse = helper2.matrix_world.inverted()
        
        # calc dist between originals
        dist_target = (orig_td.matrix_world.translation.xz - orig_chin.matrix_world.translation.xz).length
        
        # calc dist between dups (must use world translation)
        dist_current = (dup_td.matrix_world.translation.xz - dup_chin.matrix_world.translation.xz).length
        
        if dist_current < 0.0001:
            self.report({'ERROR'}, "Duplicates are too close together!")
            return {'CANCELLED'}
            
        scale_factor = dist_target / dist_current
        
        # apply scale
        helper2.scale.x *= scale_factor
        helper2.scale.z *= scale_factor
        
        context.view_layer.update()
        
        # align avg pt of dups to avg pt of originals
        mid_target = (orig_td.matrix_world.translation + orig_chin.matrix_world.translation) / 2
        mid_current = (dup_td.matrix_world.translation + dup_chin.matrix_world.translation) / 2
        
        # calc offset vector
        diff_vector = mid_target - mid_current
        
        # move helper2
        helper2.location.z += diff_vector.z
        
        if fwd_img.parent:
            # 1. save childs current world matrix
            matrix_copy = fwd_img.matrix_world.copy()
            # 2. clear parent relationship
            fwd_img.parent = None

            # 3. reapply saved world matrix
            fwd_img.matrix_world = matrix_copy

            # whatever you do this line below is the most crucial thing in this entire fucking file my goodness
            fwd_img.location.z = helper2.location.z
            
        # taking out the trash :]
        bpy.data.objects.remove(dup_td, do_unlink=True)
        bpy.data.objects.remove(dup_chin, do_unlink=True)
        bpy.data.objects.remove(helper2, do_unlink=True)
        
        self.report({'INFO'}, "Calibration Complete!")
        
        scene.orthometric.stage = 'FRONT_SETUP' 
        
        return {'FINISHED'}

class ORTHOMETRIC_OT_edit_front(bpy.types.Operator):
    # switch to front cam and controls
    bl_idname = "orthometric.edit_front"
    bl_label = "Open Front Controller"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        scene = context.scene
        
        # 1. switch ui stage back to setup
        props.stage = 'FRONT_SETUP'
        
        # 2. set active cam
        cam = bpy.data.objects.get("Ortho_Cam_Front")
        if cam:
            scene.camera = cam
            
        # 3. force viewport to camera
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                
        return {'FINISHED'}

# stage 1 complete :]
class ORTHOMETRIC_OT_finish_stage_one(bpy.types.Operator):
    # finish front stage and return to lobby
    bl_idname = "orthometric.finish_stage_one"
    bl_label = "Finish Front"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # modified: lobby logic
        props = context.scene.orthometric
        
        # mark front as done
        props.has_front = True
        
        # return to lobby
        props.stage = 'START'
        
        self.report({'INFO'}, "Front View Set. Returned to Lobby.")
        return {'FINISHED'}