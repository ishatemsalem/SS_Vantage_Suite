import bpy
import math

## Stage 3 Initialization

class ORTHOMETRIC_OT_add_custom_view(bpy.types.Operator):
    # init and create new custom view hierarchy Master -> Minor -> cam & img
    bl_idname = "orthometric.add_custom_view"
    bl_label = "Add Custom View"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        props = scene.orthometric
        
        # 1. add entry to ui list
        item = props.custom_views.add()
        item.name = f"View {len(props.custom_views)}"
        
        # generate unique names
        idx = len(props.custom_views)
        n_master = f"OM_Master_{idx}"
        n_minor = f"OM_Minor_{idx}"
        n_cam = f"OM_Cam_{idx}"
        n_img = f"OM_Img_{idx}"
        
        # 2. create heoirarchy
        # a. master controller (rot) - centered at head height approx
        bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 1.47))
        master = context.active_object
        master.name = n_master
        master.show_name = True
        master.empty_display_size = 0.5
        master.rotation_euler = (math.radians(90),0,math.radians(135))

        # b. minor controller (calibration parent)
        bpy.ops.object.empty_add(type='CUBE', location=(0, 0, 1.47))
        minor = context.active_object
        minor.name = n_minor
        minor.parent = master
        minor.empty_display_size = 0.3
        
        # c. camera (child of minor)
        cam_data = bpy.data.cameras.new(name=n_cam)
        cam_obj = bpy.data.objects.new(n_cam, cam_data)
        context.collection.objects.link(cam_obj)
        cam_obj.parent = minor
        # default pos relative to minor (local)
        cam_obj.location = (0, 0, 2.0) # 2 meters away
        cam_obj.rotation_euler = (0, 0, 0)
        scene.camera = cam_obj

        # d. image (child of minor)
        if self.filepath:
            bpy.ops.object.empty_add(type='IMAGE', location=(0, 0, 1.47))
            img_obj = context.active_object
            img_obj.name = n_img
            
            # reparent to minor keeping transform, then zero out
            img_obj.parent = minor
            img_obj.matrix_parent_inverse = minor.matrix_world.inverted()
            img_obj.location = (0,0,1.47) 
            img_obj.rotation_euler = (math.radians(90),0,math.radians(135))
            
            try:
                img_obj.data = bpy.data.images.load(self.filepath)
            except:
                pass
            
            # store refs
            item.obj_name_master = n_master
            item.obj_name_minor = n_minor
            item.obj_name_cam = n_cam
            item.obj_name_img = n_img

        # 3. setup init orientation
        # align standard: cam at +y (2m), looking at 0.
        cam_obj.location = (0, 0, 2.0)
        cam_obj.rotation_euler = (0, 0, 0) 

        props.active_view_index = len(props.custom_views) - 1
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ORTHOMETRIC_OT_remove_custom_view(bpy.types.Operator):
    # remove selected view and its hierarchy
    bl_idname = "orthometric.remove_custom_view"
    bl_label = "Remove View"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.orthometric
        idx = props.active_view_index
        try:
            item = props.custom_views[idx]
            for n in [item.obj_name_master, item.obj_name_minor, item.obj_name_cam, item.obj_name_img]:
                obj = bpy.data.objects.get(n)
                if obj: bpy.data.objects.remove(obj, do_unlink=True)
            props.custom_views.remove(idx)
            props.active_view_index = max(0, idx - 1)
        except IndexError:
            pass
        return {'FINISHED'}

class ORTHOMETRIC_OT_enter_config(bpy.types.Operator):
    # enter config mode for selected view
    bl_idname = "orthometric.enter_config"
    bl_label = "Enter Configuration"
    
    def execute(self, context):
        props = context.scene.orthometric
        item = props.custom_views[props.active_view_index]
        
        # 1. switch cam
        cam = bpy.data.objects.get(item.obj_name_cam)
        if cam:
            context.scene.camera = cam
            
        # 2. viewport to cam
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
        
        # 3. sync sliders to current master rot
        master = bpy.data.objects.get(item.obj_name_master)
        if master:
            props.stage_3_rot_x = math.degrees(master.rotation_euler.x)
            props.stage_3_rot_z = math.degrees(master.rotation_euler.z)

        props.stage = 'STAGE_3_SETUP'
        return {'FINISHED'}

class ORTHOMETRIC_OT_finish_stage_three(bpy.types.Operator):
    # return to lobby from stage 3
    bl_idname = "orthometric.finish_stage_three"
    bl_label = "Return to Lobby"
    
    def execute(self, context):
        context.scene.orthometric.stage = 'START'
        return {'FINISHED'}

## Stage 3 Calibration

class ORTHOMETRIC_OT_start_calibration_s3(bpy.types.Operator):
    # start calibration for custom view
    bl_idname = "orthometric.start_calibration_s3"
    bl_label = "Start Calibration"
    
    def execute(self, context):
        props = context.scene.orthometric
        
        orig_td = bpy.data.objects.get("OM_Anchor_TearDuct")
        orig_chin = bpy.data.objects.get("OM_Anchor_Chin")
        if not (orig_td and orig_chin): return {'CANCELLED'}
        
        dup_td = orig_td.copy()
        dup_td.name = "OM_Dup_TearDuct_S3"
        context.collection.objects.link(dup_td)
        
        dup_chin = orig_chin.copy()
        dup_chin.name = "OM_Dup_Chin_S3"
        context.collection.objects.link(dup_chin)
        
        # ensure unlocked movement (x, y, z)
        for obj in [dup_td, dup_chin]:
            obj.lock_location = (False, False, False)
        
        bpy.ops.object.select_all(action='DESELECT')
        dup_td.select_set(True)
        dup_chin.select_set(True)
        context.view_layer.objects.active = dup_td
        
        props.stage = 'STAGE_3_CALIBRATE'
        return {'FINISHED'}

class ORTHOMETRIC_OT_apply_calibration_s3(bpy.types.Operator):
    # apply calibration to image
    bl_idname = "orthometric.apply_calibration_s3"
    bl_label = "Apply Calibration"
    
    def execute(self, context):
        props = context.scene.orthometric
        item = props.custom_views[props.active_view_index]
        
        img_obj = bpy.data.objects.get(item.obj_name_img)
        dup_td = bpy.data.objects.get("OM_Dup_TearDuct_S3")
        dup_chin = bpy.data.objects.get("OM_Dup_Chin_S3")
        orig_td = bpy.data.objects.get("OM_Anchor_TearDuct")
        orig_chin = bpy.data.objects.get("OM_Anchor_Chin")
        
        if not (img_obj and dup_td and dup_chin): return {'CANCELLED'}
        
        # 1. scale
        dist_target = (orig_td.matrix_world.translation - orig_chin.matrix_world.translation).length
        dist_current = (dup_td.matrix_world.translation - dup_chin.matrix_world.translation).length
        scale_factor = dist_target / dist_current if dist_current > 0 else 1.0
        
        img_obj.scale *= scale_factor
        context.view_layer.update()
        
        # 2. pos (x, y, z translation)
        mid_target = (orig_td.matrix_world.translation + orig_chin.matrix_world.translation) / 2
        mid_dup = (dup_td.matrix_world.translation + dup_chin.matrix_world.translation) / 2
        
        # calc full 3d diff
        diff = mid_target - mid_dup
        
        # apply full diff to image
        img_obj.matrix_world.translation += diff
        
        # cleanup
        bpy.data.objects.remove(dup_td, do_unlink=True)
        bpy.data.objects.remove(dup_chin, do_unlink=True)
        
        props.stage = 'STAGE_3_SETUP'
        return {'FINISHED'}