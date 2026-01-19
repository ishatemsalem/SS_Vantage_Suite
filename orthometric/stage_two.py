import bpy
import math

## Stage 2 Initialization

class ORTHOMETRIC_OT_init_side(bpy.types.Operator):
    # init side view & import assets
    bl_idname = "orthometric.init_side"
    bl_label = "Import Side Image"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        props = scene.orthometric

        # master empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        master = context.active_object
        master.name = "OM_Master_Side"

        # camera
        cam_data = bpy.data.cameras.new(name="Ortho_Cam_Side")
        cam_obj = bpy.data.objects.new("Ortho_Cam_Side", cam_data)
        scene.collection.objects.link(cam_obj)
        
        # side view positioning
        # cam placed at +x looking towards -x
        base_dist = 2.0
        # simple initial placement
        cam_obj.location = (base_dist, 0, 1.47)
        # rotation (90 x, 0 y, 90 z) to look down -x axis
        cam_obj.rotation_euler = (math.radians(90), 0, math.radians(90))
        cam_data.lens = props.focal_length_side
        scene.camera = cam_obj

        # image
        if not self.filepath: return {'CANCELLED'}

        # image placed at 0, 0, 1.47 (centered)
        bpy.ops.object.empty_add(type='IMAGE', location=(0, 0, 1.47))
        img_obj = context.active_object
        img_obj.name = "Ref_Img_Side"
        # rot matches cam
        img_obj.rotation_euler = (math.radians(90), 0, math.radians(90))
        img_obj.empty_display_size = 0.9
        
        try:
            img_obj.data = bpy.data.images.load(self.filepath)
        except:
            pass
        
        # trigger update
        props.focal_length_side = props.focal_length_side

        # viewport
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'

        img_obj.rotation_mode = 'XYZ'

        # Master becomes supreme ruler of all
        cam_obj.parent = master
        img_obj.parent = master
        img_obj.matrix_parent_inverse = master.matrix_world.inverted()

        # add to list
        item = props.custom_views.add()
        item.name = "Side View"
        item.view_type = 'SIDE'
        item.obj_name_master = master.name
        item.obj_name_cam = cam_obj.name
        
        # set active index to this new item
        props.active_view_index = len(props.custom_views) - 1

        props.stage = 'SIDE_SETUP'
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


## Mirroring Tool

class ORTHOMETRIC_OT_mirror_side(bpy.types.Operator):
    # mirrors side image by rotating 180 on z
    bl_idname = "orthometric.mirror_side"
    bl_label = "Mirror Image"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        img_obj = bpy.data.objects.get("Ref_Img_Side")
        if not img_obj: return {'CANCELLED'}

        # rotate 180 degrees
        img_obj.rotation_euler.z += math.pi
        
        return {'FINISHED'}

## Stage 2.1.3: Calibration

class ORTHOMETRIC_OT_start_calibration_side(bpy.types.Operator):
    # start stage 2.1.3: two-point calibration (side)
    bl_idname = "orthometric.start_calibration_side"
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
        # side view: move in y and z. lock x.
        dup_td.lock_location[0] = True 
        
        # 3. dup chin
        dup_chin = orig_chin.copy()
        if orig_chin.data: dup_chin.data = orig_chin.data.copy()
        dup_chin.name = "OM_Dup_Chin"
        context.collection.objects.link(dup_chin)
        # side view: move in y and z. lock x.
        dup_chin.lock_location[0] = True

        # 4. select both
        bpy.ops.object.select_all(action='DESELECT')
        dup_td.select_set(True)
        dup_chin.select_set(True)
        context.view_layer.objects.active = dup_td
        
        props.stage = 'SIDE_CALIBRATE'
        self.report({'INFO'}, "Align the duplicates to the Image's Tear Duct and Chin (Side View)")
        return {'FINISHED'}

class ORTHOMETRIC_OT_apply_calibration_side(bpy.types.Operator):
    # apply scale and pos calibration based on 2 points (side view)
    bl_idname = "orthometric.apply_calibration_side"
    bl_label = "Apply Calibration"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # get objects
        side_img = bpy.data.objects.get("Ref_Img_Side")
        
        orig_td = bpy.data.objects.get("OM_Anchor_TearDuct")
        orig_chin = bpy.data.objects.get("OM_Anchor_Chin")
        
        dup_td = bpy.data.objects.get("OM_Dup_TearDuct")
        dup_chin = bpy.data.objects.get("OM_Dup_Chin")

        master = bpy.data.objects.get("OM_Master_Side")
        
        # helper2 generated at 0, 0, 1.47
        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 1.47))
        helper2 = context.active_object
        helper2.name = "Helper2_Center_Side"

        if not (side_img and orig_td and orig_chin and dup_td and dup_chin):
            self.report({'ERROR'}, "Missing calibration objects")
            return {'CANCELLED'}
            
        # parent dups to helper2
        for obj in [dup_td, dup_chin, side_img]:
            obj.parent = helper2
            obj.matrix_parent_inverse = helper2.matrix_world.inverted()
        
        # calc dist between originals
        dist_target = (orig_td.matrix_world.translation - orig_chin.matrix_world.translation).length
        
        # calc dist between dups
        dist_current = (dup_td.matrix_world.translation - dup_chin.matrix_world.translation).length
        
        if dist_current < 0.0001:
            self.report({'ERROR'}, "Duplicates are too close together!")
            return {'CANCELLED'}
            
        scale_factor = dist_target / dist_current
        
        # apply scale (side view affects y and z dimensions primarily)
        helper2.scale = (scale_factor, scale_factor, scale_factor)
        
        # force scene update
        context.view_layer.update()
        
        # align avg pt of dups to avg pt of originals
        mid_target = (orig_td.matrix_world.translation + orig_chin.matrix_world.translation) / 2
        mid_current = (dup_td.matrix_world.translation + dup_chin.matrix_world.translation) / 2
        
        # calc offset vector
        diff_vector = mid_target - mid_current
        
        # side view calibration logic
        # apply translation to y (depth) and z (height)
        helper2.location.y += diff_vector.y
        helper2.location.z += diff_vector.z
        
        if side_img.parent:
            # 1. save childs current world matrix
            matrix_copy = side_img.matrix_world.copy()
            # 2. clear parent relationship
            side_img.parent = None

            # 3. reapply saved world matrix
            side_img.matrix_world = matrix_copy

            # apply final pos from helper to image directly
            side_img.location.y = helper2.location.y
            side_img.location.z = helper2.location.z

        
        # master becomes regains custody
        if master:
            side_img.parent = master
            side_img.matrix_parent_inverse = master.matrix_world.inverted()

        # taking out the trash :]
        bpy.data.objects.remove(dup_td, do_unlink=True)
        bpy.data.objects.remove(dup_chin, do_unlink=True)
        bpy.data.objects.remove(helper2, do_unlink=True)
        
        self.report({'INFO'}, "Side Calibration Complete!")
        
        scene.orthometric.stage = 'SIDE_SETUP' 
        
        return {'FINISHED'}

# stage 2 complete :]
class ORTHOMETRIC_OT_finish_stage_two(bpy.types.Operator):
    # finish side stage and return to lobby
    bl_idname = "orthometric.finish_stage_two"
    bl_label = "Finish Side"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # modified: lobby logic
        props = context.scene.orthometric
        
        # mark side as done
        props.has_side = True
        
        # return to lobby
        props.stage = 'START'
        
        self.report({'INFO'}, "Side View Set. Returned to Lobby.")
        return {'FINISHED'}


class ORTHOMETRIC_OT_edit_side(bpy.types.Operator):
    # switch to side cam and controls
    bl_idname = "orthometric.edit_side"
    bl_label = "Open Side Controller"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        scene = context.scene
        
        # 1. switch ui stage back to setup
        props.stage = 'SIDE_SETUP'
        
        # 2. set active cam
        cam = bpy.data.objects.get("Ortho_Cam_Side")
        if cam:
            scene.camera = cam
            
        # 3. force viewport to camera
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                
        return {'FINISHED'}

## Stage 3 / Additional-views logic (RETIRED WORKING ON REMOVING)

class ORTHOMETRIC_OT_init_additional(bpy.types.Operator):
    # init additional view (reuses side logic)
    bl_idname = "orthometric.init_additional"
    bl_label = "Import Additional Image"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        # reuse side view logic for now as requested
        bpy.ops.orthometric.init_side(filepath=self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}