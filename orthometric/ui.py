import bpy

class ORTHOMETRIC_UL_view_list(bpy.types.UIList):
    # list of custom views
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # allow renaming directly
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='CAMERA_DATA')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CAMERA_DATA')

class ORTHOMETRIC_PT_main(bpy.types.Panel):
    bl_label = "SS Vantage Suite: OrthoMetric Tools"
    bl_idname = "ORTHOMETRIC_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SS: OrthoMetric'

    def draw(self, context):
        layout = self.layout
        props = context.scene.orthometric

        # stage 0: lobby
        if props.stage == 'START':
            box = layout.box()
            box.label(text="Lobby: Asset Manager")
            
            col = box.column(align=True)
            
            # front view logic
            if not props.has_front:
                col.operator("orthometric.init_front", text="Add Front View", icon='AXIS_FRONT')
            else:
                col.operator("orthometric.edit_front", text="Open Front Controller", icon='SETTINGS')

            col.separator()

            # side view logic
            if not props.has_side:
                col.operator("orthometric.init_side", text="Add Side View", icon='AXIS_SIDE')
            else:
                col.operator("orthometric.edit_side", text="Open Side Controller", icon='SETTINGS')

            box.separator()

            # stage 3: custom views list
            box.label(text="Additional Views:")
            row = box.row()
            row.template_list("ORTHOMETRIC_UL_view_list", "custom_views", props, "custom_views", props, "active_view_index")
            
            col = row.column(align=True)
            col.operator("orthometric.add_custom_view", icon='ADD', text="")
            col.operator("orthometric.remove_custom_view", icon='REMOVE', text="")
            
            if len(props.custom_views) > 0:
                box.operator("orthometric.enter_config", text="Enter Configuration", icon='PREFERENCES')
        
        ## Front Controller
        if props.stage in ['FRONT_SETUP', 'FRONT_CALIBRATE']:
            # 1. return btn
            row = layout.row()
            row.scale_y = 1.5
            row.operator("orthometric.finish_stage_one", text="Return to Lobby", icon='GRIP')
            
            # 2. cam controls
            box = layout.box()
            box.label(text="Camera Settings")
            box.prop(props, "focal_length_front", slider=True)
            box.prop(props, "front_cam_y", slider=True, text="Camera Y Offset")
            
        # 3. front image tools
        if props.stage == 'FRONT_SETUP':
            box = layout.box()
            box.label(text="Image Adjustment", icon='IMAGE_DATA')
            
            if not props.is_centering:
                col = box.column(align=True)
                col.operator("orthometric.center_tool", text="Center Image", icon='TRANSFORM_ORIGINS')
                col.operator("orthometric.start_calibration", text="Start Calibration", icon='TRACKING_FORWARDS')
            else:
                # centering mode
                box.alert = True
                box.label(text="Move 'Helper_Center' to X symmetry line")
                box.operator("orthometric.confirm_center", text="Confirm Centering")

        # 4. calibration wizard
        elif props.stage == 'FRONT_CALIBRATE':
            box = layout.box()
            box.label(text="Calibration Active", icon='PREFERENCES')
            
            msg = box.column(align=True)
            msg.label(text="Align anchors to Tear Duct & Chin")
            
            box.separator()
            box.operator("orthometric.apply_calibration", text="Apply & Reset", icon='CHECKMARK')

        ## Side Controller
        if props.stage in ['SIDE_SETUP', 'SIDE_CALIBRATE']:
            # 1. return btn
            row = layout.row()
            row.scale_y = 1.5
            row.operator("orthometric.finish_stage_two", text="Return to Lobby", icon='GRIP')

            # 2. cam controls
            box = layout.box()
            box.label(text="Side Camera Settings")
            box.prop(props, "focal_length_side", slider=True)
            box.prop(props, "side_cam_x", slider=True, text="Camera X Offset")

        # 3. side image tools
        if props.stage == 'SIDE_SETUP':
            box = layout.box()
            box.label(text="Image Adjustment", icon='IMAGE_DATA')
            
            col = box.column(align=True)
            col.operator("orthometric.mirror_side", text="Mirror Image (180°)", icon='MOD_MIRROR')
            col.separator()
            col.operator("orthometric.start_calibration_side", text="Start Calibration", icon='TRACKING_FORWARDS')

        # 4. calibration wizard
        elif props.stage == 'SIDE_CALIBRATE':
            box = layout.box()
            box.label(text="Calibration Active", icon='PREFERENCES')
            
            msg = box.column(align=True)
            msg.label(text="Align anchors to Image")
            
            box.separator()
            box.operator("orthometric.apply_calibration_side", text="Apply & Reset", icon='CHECKMARK')
        

        ## Stage 3: Custom View Controller
        if props.stage in ['STAGE_3_SETUP', 'STAGE_3_CALIBRATE']:
            # 1. return
            row = layout.row()
            row.scale_y = 1.5
            row.operator("orthometric.finish_stage_three", text="Return to Lobby", icon='GRIP')
            
            # 2. master rot
            box = layout.box()
            box.label(text="Global Rotation (Master)", icon='DRIVER')
            col = box.column(align=True)
            col.prop(props, "stage_3_rot_x", text="X Rotation")
            col.prop(props, "stage_3_rot_z", text="Z Rotation")
            
            # 3. cam controls (local)
            if len(props.custom_views) > 0:
                item = props.custom_views[props.active_view_index]
                
                box = layout.box()
                box.label(text="Camera Settings (Local)")
                box.prop(item, "fov", slider=True) 
                box.prop(item, "dist_off", slider=True, text="Distance Offset")

            # 4. calibration
            if props.stage == 'STAGE_3_SETUP':
                box = layout.box()
                box.label(text="Calibration", icon='TRACKING')
                box.operator("orthometric.start_calibration_s3", text="Start Calibration", icon='TRACKING_FORWARDS')
                
            elif props.stage == 'STAGE_3_CALIBRATE':
                box = layout.box()
                box.alert = True
                box.label(text="Align Duplicates (X,Y,Z)")
                box.operator("orthometric.apply_calibration_s3", text="Apply Calibration", icon='CHECKMARK')