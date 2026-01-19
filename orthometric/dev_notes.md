SS Vantage Suite

OrthoMetric Conventions: first script of the suite. allows easy setup of viewport, references, quick camera switching, and tweaking

Hierarchy: 
SS_Vantage_Suite
├── .git/
├── README.md
└── OrthoMetric/           <-- Python Pack
    ├── __init__.py         <-- Handles Registration
    ├── ui.py               <-- Buttons and Panels
    ├── stage_one.py        <-- Front view image calibration & setting, includes importing of model
    ├── stage_two.py        <-- Side view image calibration & setting
    ├── stage_three.py      <-- Additional views image calibration & setting
    └── assets/             <-- New Folder
        └── heads.blend     <-- Asset blender file


inside heads.blend:

Collection: OM_Assets (OrthoMetric Assets)
		OM_Archives (Retired/Future Updates)

OM_Assets:
Low Poly Object: OM_Cage_Low_poly (Mesh Name: mesh_cage_low_poly)
Anchors: OM_Anchor_TearDuct, OM_Anchor_Chin

Sequence of events:

User is in lobby, they can choose between adding a front view and a side view

stage one:
	Imports objects "OM_Cage_Low_Poly", "OM_Anchor_TearDuct", "OM_Anchor_Chin"
	front view camera is created at (0, 2.0, 1.47) (90, 0, 180)
	front view image is created at (0, 0, 1.47) (90, 0, 180) fl 50.0 scale 0.9
	fl slider appears in n-menu changing fl automatically moves image according to equation:
	        base_dist = 2.0
        	ratio = props.focal_length_front / 50.0
        	calc_y = ratio * (base_dist + props.front_cam_y)
        	cam_obj.location = (0, calc_y, 1.47)

	user chooses button to center image:
		empty "Helper_Center" is created, same pos as image, user instructed to move till line of symmetry of imported image
		image parented to Helper_Center, helper center moved to x coord of zero, Helper_Center is deleted
	
	user chooses button to calibrate image:
		The empties "OM_Anchor_TearDuct", "OM_Anchor_Chin" are duplicated to "OM_Dup_TearDuct" & "OM_Dup_Chin" and selected
		user instructed to line them up with the image
		when user presses confirmation button two sequences occur:
			1- helper2 is scaled in xy exclusively so distance between OM_Dup_TearDuct & OM_Dup_Chin is same as OM_Anchor_TearDuct & OM_Anchor_Chin
			2- helper2 is moved along z exclusively so avg coord between the dup is same as original empties
			3-Scene is cleaned up, Dups are removed

	Then once user presses "Return to lobby" it returns to lobby, and button used to enter side view returns the same menu items except it does not ask for an image to be imported

stage two: 
	Immediately asks for image to import
	side view camera is created at (2.0, 0, 1.47) (90, 0, 90)
	side view image is created at (0, 0, 1.47) (90, 0, 90) fl 50.0 scale 0.9
	fl slider appears in n-menu changing fl automatically moves image according to equation:
	        base_dist = 2.0
        	ratio = props.focal_length_side / 50.0
        	calc_y = ratio * (base_dist + props.side_cam_y)
        	cam_obj.location = (0, calc_y, 1.47)

	user chooses button to "mirror" image:
		image rotated 180 along z
	
	user chooses button to calibrate image:
		The empties "OM_Anchor_TearDuct", "OM_Anchor_Chin" are duplicated to "OM_Dup_TearDuct" & "OM_Dup_Chin" and selected
		user instructed to line them up with the image
		when user presses confirmation button two sequences occur:
			1- helper2 is scaled in yz exclusively so distance between OM_Dup_TearDuct & OM_Dup_Chin is same as OM_Anchor_TearDuct & OM_Anchor_Chin
			2- helper2 is moved along yz (not just z like stage 1) so avg coord between the dup is same as original empties
			3-Scene is cleaned up, Dups are removed
	
	Then once user presses "Return to lobby" it returns to lobby, and button used to enter side view returns the same menu items except it does not ask for an image to be imported


User can use box with + button in lobby to add another view, going into configuration in a variable stage 3 sequence:

	Immediately asks for image to import
	Two empties created at  0 0 1.47, Major empty and minor empty
	camera is created at (2.0, 0, 1.47) (90, 0, 90)
	image is created at (0, 0, 1.47) (90, 0, 135) fl 50.0 scale 0.9
	minor empty parented to major empty, and image and cam parented to minor empty
	fl slider appears in n-menu changing fl automatically moves image according to equation:
	        base_dist = 2.0
        	ratio = props.focal_length_side / 50.0
        	calc_y = ratio * (base_dist + props.side_cam_y)
        	cam_obj.location = (0, calc_y, 1.47)

	user chooses button to "mirror" image:
		image rotated 180 along z
	
	user chooses button to calibrate image:
		The empties "OM_Anchor_TearDuct", "OM_Anchor_Chin" are duplicated to "OM_Dup_TearDuct" & "OM_Dup_Chin" and selected
		user instructed to line them up with the image
		when user presses confirmation button two sequences occur:
			1- helper2 is scaled in xyz so distance between OM_Dup_TearDuct & OM_Dup_Chin is same as OM_Anchor_TearDuct & OM_Anchor_Chin
			2- helper2 is moved along xyz so avg coord between the dup is same as original empties
			3-Scene is cleaned up, Dups are removed



TO DO: 
	- Focal length offset do NOT follow a formula to keep the object the same size for non-front/side views. i have a feel sqrt has a part in this
	- Add a mirror 180 for additional images. useless tho ill probs remove from side view before i add to additional views

	-Commence stage 4. god help me

stage 4 can possibly have multiple steps. 
step 1: decide critical values eg. as eye size and lining up, via points, using front and side views
step 2: select vertex and *pull*
step 3: if 45 degree image available for example, user gets to decide rotation values of camera always pointing towards 0,0,1.47
Laplacian smoothing: keywordS