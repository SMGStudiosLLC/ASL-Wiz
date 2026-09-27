"""
All design dimensions for the DELTA chair-desk, in millimetres, at full (real) scale.

Coordinate system (used everywhere):
    X  forward, from the backrest toward the desk (the student faces +X)
    Y  sideways, +Y is the student's left
    Z  up, Z = 0 is the floor
    X = 0 sits roughly at the backrest's front face at seat level.

Every value that drives ergonomics is sourced in docs/DESIGN.md (research section).
"""

INCH = 25.4

# ---------------------------------------------------------------- seat shell
SEAT_HEIGHT = 430.0          # top of seat at the front crest (16.9 in); EN 1729 size 5 (430) .. 6 (460) via glides
SEAT_WIDTH = 480.0           # 18.9 in; hip room for 95th pct + clothing, open sides for larger bodies
SHELL_T = 5.0                # polypropylene wall (real product)

# Mid-surface centreline of the one-piece shell at Y = 0, side view (X, Z).
# Runs from the waterfall tip, along the seat, through the junction, up the back
# and ends in the rolled top lip.  Tuned so that:
#   seat pan tilt ~4.5 deg rearward, seat-to-back ~104 deg overall and ~109 deg to the
#   upper back (EN 1729: 95-110), lumbar apex ~227 mm above the seat
#   (Dowell 1995 mean ~250, range 150-360), backrest top ~460 mm above the seat.
SHELL_PATH = [
    (430.0, 385.0),   # 0  waterfall tip
    (422.0, 411.0),   # 1
    (402.0, 427.5),   # 2  front crest (top surface = SEAT_HEIGHT)
    (330.0, 423.0),   # 3
    (230.0, 412.0),   # 4
    (140.0, 402.5),   # 5  sit-bone pocket
    (75.0, 401.0),    # 6
    (30.0, 409.0),    # 7  junction starts
    (8.0, 442.0),     # 8
    (2.0, 510.0),     # 9  flex zone
    (6.0, 588.0),     # 10
    (8.5, 632.0),     # 11 lumbar apex
    (-8.0, 710.0),    # 12
    (-28.0, 790.0),   # 13
    (-50.0, 849.0),   # 14 top region
    (-66.0, 866.0),   # 15
    (-82.0, 865.0),   # 16 end of rolled lip
]

# Per-landmark section shape (one value per SHELL_PATH point):
#   half width, dish/wrap (edges raised toward the sitter), edge roll radius (edge curls away)
SHELL_HALF_W = [183, 222, 238, 240, 240, 240, 240, 238, 226, 215, 208, 212, 224, 238, 240, 213, 176]
SHELL_DISH = [3, 8, 14, 18, 18, 18, 18, 22, 26, 24, 24, 24, 24, 24, 22, 14, 6]
SHELL_ROLL = [10, 20, 24, 24, 24, 24, 24, 28, 24, 14, 14, 14, 14, 12, 12, 10, 7]
# Flex: the whole lower/mid back is evenly wrapped (~24 mm) so it bends over ~300 mm
# instead of kinking at one spot; that keeps the plastic strain low (see analysis.py).
SHELL_DISH_PRINT_FACTOR = {9: 0.55, 10: 0.5, 11: 0.5, 12: 0.6}   # gentler wrap on the PLA model so it visibly flexes

# Bearing pads moulded under the seat where the frames meet it
PAD_H = 27.0                         # pad height above the frame apex
PAD_BLEND_R = 55.0                   # fillet radius flowing the pad into the seat

# hidden aluminium cross beam under the seat, bolted to both frame apexes (real product only)
SEAT_BEAM = (50.0, 25.0)             # section, x by z

# -------------------------------------------------------------- side frames
FRAME_T = 30.0                       # frame thickness (Y)
FRAME_Y_OUT = SEAT_WIDTH / 2         # outer face flush with the seat side (240)
FRAME_Y_IN = FRAME_Y_OUT - FRAME_T   # 210
FRAME_FRONT = (400.0, 0.0)           # virtual front-foot corner
FRAME_REAR = (-125.0, 0.0)           # virtual rear-foot corner (removed by the heel round)
FRAME_APEX_X = 172.0                 # apex sits under the sit bones
FRAME_R_FRONT = 42.0
FRAME_R_REAR = 66.0                  # the rounded "cut-off" heel
FRAME_R_APEX = 64.0
FRAME_LEG_W = 40.0                   # leg member width
FRAME_RUNNER_W = 34.0                # floor runner member width
FRAME_WIN_R = (28.0, 30.0, 26.0)     # window corner radii (front, apex, rear)
FRAME_EDGE_R = 11.0                  # edge round on the frame (full round would be 15)
# glide feet on the outside of each frame: widen the footprint for sitting sideways
POD_X = ((-5.0, 75.0), (250.0, 330.0))   # rear and front, along X
POD_OUT = 18.0                       # how far they stand out past the frame (stays inside the desk outline)
POD_H = 24.0

# ---------------------------------------------------------------- floor base
BASE_H = 42.0                        # spine + cross bar + T-foot height; the spine is a footrest for shorter students
CROSSBAR_X = (285.0, 339.0)          # cross bar between the two front feet
SPINE_W = 62.0
FOOTREST_X = (455.0, 640.0)          # wider pad on the spine where short students' feet land
FOOTREST_HALF_W = 105.0
TFOOT_X = (715.0, 815.0)             # T-foot under the desk's far end
TFOOT_HALF_W = 285.0
POST_X = 728.0                       # desk post centre (leaves knee room for a 95th pct male)
POST_BOSS = (104.0, 84.0, 60.0)      # socket boss on the T-foot (x, y, z)
BASE_PLAN_R = 24.0                   # plan-view corner radius of the base outline

# ------------------------------------------------------------ post and head
SLEEVE = (76.0, 66.0)                # lower (outer) post section, x by y
SLEEVE_TOP = 575.0                   # high enough that unused height holes stay hidden inside it
INNER = (56.0, 46.0)                 # upper (inner) post section (as wide as the dovetail)
POST_R = 12.0                        # corner radius of post sections
DESK_HEIGHTS = [655.0, 680.0, 705.0, 730.0, 755.0]    # desktop surface heights (25.8-29.7 in), 1 in steps
SLEEVE_PIN_Z = 458.0                 # height of the height-lock pin (runs front to back, knob on the far side)

# dovetail head: the tenon sits inside a track in the desktop's underside
TENON_H = 10.0                       # depth into the desktop
TENON_W_TOP = 46.0                   # 45-degree flanks, narrow face at the desk's underside
TENON_X = (-200.0, 10.0)             # extent relative to the post centre
HEAD_GAP = 1.0                       # gap between the post top and the desk underside
DETENT_OFF = -48.0                   # reach index pin, just behind the post (clear of the thighs)
INDEX_BOSS = (15.0, 18.0)            # radius, height of the pin guide under the tenon
TRACK_START = 130.0                  # track starts this far from the near edge
PLUG_LEN = 15.0                      # end plug that closes the track's far end after assembly

# ----------------------------------------------------------------- desktop
TOP_W_NEAR = 510.0                   # 20.1 in across at the student's edge (easier to slide in from the side)
TOP_W = 590.0                        # 23.2 in across at the far edge
TOP_D = 525.0                        # 20.7 in deep -> ~427 sq in, about 8% more than the 3700BRM paddle (~395 sq in)
BELLY = (20.0, 320.0)                # gentle concave cut in the near edge: depth, width
TOP_T = 25.0
TOP_CORNER_R = 45.0                  # far corners
TOP_CORNER_R_NEAR = 55.0             # near corners
TOP_EDGE_R = 8.0
DESK_GAPS = [230.0, 275.0, 320.0, 365.0]   # backrest to desk near corners at elbow height; +20 at the belly
BACK_X_AT_ELBOW = 10.0               # backrest front face X at elbow height (measured on the shell)
COVE_RAMP = 45.0                     # length of the groove's wipe-out ramps
COVE_LEN = 380.0                     # pencil cove near the far edge
COVE_W = 22.0
COVE_D = 6.0
COVE_FROM_FAR = 42.0                 # cove centreline distance from far edge

# default configuration shown in renders / assembled model
DEFAULT_HEIGHT_INDEX = 3             # 730 mm
DEFAULT_GAP_INDEX = 1                # 275 mm (295 at the belly)


def desk_near_x(gap_index):
    return BACK_X_AT_ELBOW + DESK_GAPS[gap_index]


# -------------------------------------------------------------- print kit
KIT_SCALE = 1.0 / 6.0
KIT = dict(
    shell_t_seat=1.7,     # seat pan
    shell_t_flex=1.3,     # lower back flex zone
    shell_t_back=1.45,    # upper back
    rib_h=0.45,           # grip ribs: height, width, pitch  (>= 0.6 mm wide for a 0.4 nozzle)
    rib_w=0.85,
    rib_pitch=1.7,
    slide=0.30,           # per-side clearance, sliding fits (post in sleeve, dovetail)
    snug=0.15,            # per-side clearance, press fits (with lead-in chamfers)
    pin_d=1.75,           # pins are cut from 1.75 mm filament
    pin_hole=2.0,         # free holes
    pin_grip=1.9,         # holes that should hold a pin by friction
    pin_guide=1.85,       # the upward reach pin's guide (must not fall out)
    head_gap=0.5,         # gap between post top and desk underside
    track_top=0.25,       # extra track depth
    tab_len=10.0, tab_t=2.6, tab_h=3.2,           # frame apex tab into the seat pad
    xbar_tab_len=5.0, xbar_tab_h=3.6, xbar_tab_depth=2.6,   # base cross-bar tab into the frame
    chamfer=0.4,          # lead-in on tabs
)
