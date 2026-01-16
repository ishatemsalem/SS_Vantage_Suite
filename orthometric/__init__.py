import bpy
import math
from . import ui, stage_one, stage_two, stage_three

bl_info = {
    "name": "SS Vantage Suite",
    "author": "Islam Hatem Salem",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N-Panel > SS: OrthoMetric",
    "description": "OrthoMetric Head Matching",
    "category": "3D View",
}

# ... cam update funcs ...

def update_front_cam_pos(self, context):
    # updates front cam y pos
    cam_obj = bpy.data.objects.get("Ortho_Cam_Front")
    if cam_obj:
        base_dist = 2.0
        ratio = self.focal_length_front / 50.0
        target_y = ratio * (base_dist + self.front_cam_y)
        cam_obj.location.y = target_y

def update_front_cam(self, context):
    # updates front lens and forces y update
    cam = bpy.data.cameras.get("Ortho_Cam_Front")
    if cam:
        cam.lens = self.focal_length_front
    update_front_cam_pos(self, context)

def update_side_cam_pos(self, context):
    # updates side cam x pos based on fl/offset
    cam_obj = bpy.data.objects.get("Ortho_Cam_Side")
    if cam_obj:
        base_dist = 2.0
        ratio = self.focal_length_side / 50.0
        target_x = ratio * (base_dist + self.side_cam_x)
        cam_obj.location.x = target_x

def update_side_cam(self, context):
    # updates side lens and forces x update
    cam = bpy.data.cameras.get("Ortho_Cam_Side")
    if cam:
        cam.lens = self.focal_length_side
    update_side_cam_pos(self, context)


## Stage 3 Updates

def update_stage_3_master(self, context):
    # rotates master controller via sliders
    if self.stage != 'STAGE_3_SETUP': return
    
    try:
        item = self.custom_views[self.active_view_index]
        master = bpy.data.objects.get(item.obj_name_master)
        if master:
            # x: -90 to 90, z: -180 to 180
            master.rotation_euler.x = math.radians(self.stage_3_rot_x)
            master.rotation_euler.z = math.radians(self.stage_3_rot_z)
    except:
        pass

def update_item_cam_settings(self, context):
    # update func for orthoviewitem
    # updates lens and dist without dolly zoom formula
    cam_obj = bpy.data.objects.get(self.obj_name_cam)
    if cam_obj:
        # 1. update lens
        if cam_obj.data:
            cam_obj.data.lens = self.fov
        
        # 2. update dist using dolly zoom formula
        # calc_pos = (focal_length / 50.0) * (2.0 + offset)
        base_dist = 2.0
        ratio = self.fov / 50.0
        
        # calc new z pos based on ratio and offset
        target_z = ratio * (base_dist + self.dist_off)
        
        cam_obj.location.z = target_z

        if context: 
            context.view_layer.update()

## Property Group

class OrthoViewItem(bpy.types.PropertyGroup):
    # stores data for each custom view
    name: bpy.props.StringProperty(name="View Name", default="New View")
    
    # obj refs
    obj_name_master: bpy.props.StringProperty()
    obj_name_minor: bpy.props.StringProperty()
    obj_name_cam: bpy.props.StringProperty()
    obj_name_img: bpy.props.StringProperty()

    # per-view settings
    fov: bpy.props.FloatProperty(
        name="Focal Length", 
        min=10, max=200, default=50.0, 
        update=update_item_cam_settings
    )
    dist_off: bpy.props.FloatProperty(
        name="Dist Offset", 
        default=0.0, soft_min=-2.0, soft_max=5.0, 
        update=update_item_cam_settings
    )

class OrthoMetricProperties(bpy.types.PropertyGroup):
    stage: bpy.props.EnumProperty(
        items=[
            ('START', "Lobby", ""),
            ('FRONT_SETUP', "Front Setup", ""),
            ('FRONT_CALIBRATE', "Front Calibration", ""),
            ('SIDE_SETUP', "Side Setup", ""),
            ('SIDE_CALIBRATE', "Side Calibration", ""),
            ('STAGE_3_SETUP', "Custom View Setup", ""),
            ('STAGE_3_CALIBRATE', "Custom Calibration", "")
        ],
        default='START'
    )
    
    # lobby logic props
    has_front: bpy.props.BoolProperty(default=False)
    has_side: bpy.props.BoolProperty(default=False)
    
    is_centering: bpy.props.BoolProperty(default=False)
    
    focal_length_front: bpy.props.FloatProperty(
        name="Front Focal Length",
        default=50.0, min=10.0, max=200.0,
        update=update_front_cam
    )
    
    front_cam_y: bpy.props.FloatProperty(
        name="Camera Y Offset", 
        default=0.0, soft_min=-1.9, soft_max=5.0,
        update=update_front_cam_pos
    )

    # side props
    focal_length_side: bpy.props.FloatProperty(
        name="Side Focal Length",
        default=50.0, min=10.0, max=200.0,
        update=update_side_cam
    )
    
    side_cam_x: bpy.props.FloatProperty(
        name="Side Camera X Offset", 
        default=0.0, soft_min=-1.9, soft_max=5.0,
        update=update_side_cam_pos
    )


    # stage 3 props
    custom_views: bpy.props.CollectionProperty(type=OrthoViewItem)
    active_view_index: bpy.props.IntProperty(name="Index", default=0)
    
    stage_3_rot_x: bpy.props.FloatProperty(
        name="Rotation X", min=0, max=180, default=0, update=update_stage_3_master
    )
    stage_3_rot_z: bpy.props.FloatProperty(
        name="Rotation Z", min=-180, max=180, default=0, update=update_stage_3_master
    )
    
    # stage_3_fov: bpy.props.FloatProperty(
    #    name="Focal Length", min=10, max=200, default=50.0, update=update_stage_3_cam
    # )
    # stage_3_dist_off: bpy.props.FloatProperty(
    #    name="Dist Offset", default=0.0, soft_min=-2.0, soft_max=5.0, update=update_stage_3_cam
    # )

classes = (
    OrthoViewItem,
    OrthoMetricProperties,

    # stage 1
    stage_one.ORTHOMETRIC_OT_init_front,
    stage_one.ORTHOMETRIC_OT_center_tool,
    stage_one.ORTHOMETRIC_OT_confirm_center,
    stage_one.ORTHOMETRIC_OT_start_calibration,
    stage_one.ORTHOMETRIC_OT_apply_calibration,
    stage_one.ORTHOMETRIC_OT_finish_stage_one,
    stage_one.ORTHOMETRIC_OT_edit_front, 

    # stage 2
    stage_two.ORTHOMETRIC_OT_init_side,
    stage_two.ORTHOMETRIC_OT_mirror_side,
    stage_two.ORTHOMETRIC_OT_start_calibration_side,
    stage_two.ORTHOMETRIC_OT_apply_calibration_side,
    stage_two.ORTHOMETRIC_OT_finish_stage_two,
    stage_two.ORTHOMETRIC_OT_edit_side,
    
    stage_two.ORTHOMETRIC_OT_init_additional, 

    # stage 3
    stage_three.ORTHOMETRIC_OT_add_custom_view,
    stage_three.ORTHOMETRIC_OT_remove_custom_view,
    stage_three.ORTHOMETRIC_OT_enter_config,
    stage_three.ORTHOMETRIC_OT_finish_stage_three,
    stage_three.ORTHOMETRIC_OT_start_calibration_s3,
    stage_three.ORTHOMETRIC_OT_apply_calibration_s3,

    ui.ORTHOMETRIC_UL_view_list, 
    ui.ORTHOMETRIC_PT_main,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.orthometric = bpy.props.PointerProperty(type=OrthoMetricProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.orthometric