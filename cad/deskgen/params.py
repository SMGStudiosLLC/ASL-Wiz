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
SEAT_HEIGHT = 440.0          # top of seat at the front crest (17.3 in); EN 1729 size 5/6 split
SEAT_WIDTH = 460.0           # 18.1 in, covers 95th pct hip breadth + clothing, open sides for larger bodies
SHELL_T = 5.0                # polypropylene wall (real product)

# Mid-surface centreline of the one-piece shell at Y = 0, side view (X, Z).
# Runs from the waterfall tip, along the seat, through the junction, up the back
# and ends in the rolled top lip.  Tuned so that:
#   seat pan tilt ~4.5 deg rearward, seat-to-back angle ~106 deg (EN 1729: 95-110),
#   lumbar apex ~225 mm above the seat (Dowell 1995 mean ~250, range 150-360),
#   backrest top ~445 mm above the seat.
SHELL_PATH = [
    (430.0, 395.0),   # 0  waterfall tip
    (422.0, 421.0),   # 1
    (402.0, 437.5),   # 2  front crest (top surface = SEAT_HEIGHT)
    (330.0, 433.0),   # 3
    (230.0, 422.0),   # 4
    (140.0, 412.5),   # 5  sit-bone pocket
    (75.0, 411.0),    # 6
    (30.0, 419.0),    # 7  junction starts
    (8.0, 452.0),     # 8
    (2.0, 520.0),     # 9  flex zone
    (6.0, 598.0),     # 10
    (8.5, 642.0),     # 11 lumbar apex
    (-8.0, 720.0),    # 12
    (-38.0, 800.0),   # 13
    (-66.0, 857.0),   # 14 top region
    (-84.0, 873.0),   # 15
    (-100.0, 871.0),  # 16 end of rolled lip
]

# Per-landmark section shape (one value per SHELL_PATH point):
#   half width, dish/wrap (edges raised toward the sitter), edge roll radius (edge curls away)
SHELL_HALF_W = [175, 212, 228, 230, 230, 230, 230, 228, 214, 191, 183, 186, 205, 228, 230, 204, 168]
SHELL_DISH = [3, 8, 14, 18, 18, 18, 18, 12, 6, 3, 3, 8, 16, 22, 22, 14, 6]
SHELL_ROLL = [10, 20, 26, 28, 28, 28, 28, 24, 14, 8, 8, 10, 12, 12, 12, 10, 7]

# Frame bearing pads moulded under the seat (where the side frames meet the shell)
PAD_X = (95.0, 255.0)

# -------------------------------------------------------------- side frames
FRAME_T = 32.0                       # frame thickness (Y)
FRAME_Y_OUT = SEAT_WIDTH / 2         # outer face flush with the seat side (230)
FRAME_Y_IN = FRAME_Y_OUT - FRAME_T   # 198
FRAME_FRONT = (400.0, 0.0)           # virtual front-foot corner
FRAME_REAR = (-105.0, 0.0)           # virtual rear-foot corner (removed by the heel round)
FRAME_APEX_X = 172.0                 # apex sits under the sit bones
FRAME_R_FRONT = 42.0
FRAME_R_REAR = 66.0                  # the rounded "cut-off" heel
FRAME_R_APEX = 64.0
FRAME_LEG_W = 44.0                   # leg member width
FRAME_RUNNER_W = 38.0                # floor runner member width
FRAME_WIN_R = (28.0, 30.0, 26.0)     # window corner radii (front, apex, rear)
FRAME_EDGE_R = 12.0                  # edge round on the frame (full round would be 16)

# ---------------------------------------------------------------- floor base
BASE_H = 30.0                        # height of spine and cross bar
CROSSBAR_X = (285.0, 339.0)          # cross bar between the two front feet
SPINE_W = 62.0
TFOOT_X = (668.0, 770.0)             # T-foot under the desk's far end
TFOOT_HALF_W = 255.0
TFOOT_H = 40.0                       # doubles as a footrest for shorter students
POST_X = 712.0                       # desk post centre
POST_BOSS = (104.0, 84.0, 72.0)      # socket boss on the T-foot (x, y, z)

# ------------------------------------------------------------ post and head
SLEEVE = (76.0, 66.0)                # lower (outer) post section, x by y
SLEEVE_TOP = 480.0
INNER = (56.0, 46.0)                 # upper (inner) post section (as wide as the dovetail)
POST_R = 12.0                        # corner radius of post sections
DESK_HEIGHTS = [680.0, 705.0, 730.0, 755.0]    # desktop surface heights (26.8-29.7 in), 1 in steps
SLEEVE_PIN_Z = 458.0                 # height of the height-lock pin through the sleeve

RAIL_LEN = 250.0                     # head rail along X
RAIL_BACK = 190.0                    # rail runs this far behind the post centre (toward the student)
RAIL_W_TOP = 46.0                    # dovetail rail, wide face up (against the desk)
RAIL_W_BOT = 34.0
RAIL_H = 18.0

# ----------------------------------------------------------------- desktop
TOP_W = 610.0                        # 24.0 in across (Y)
TOP_D = 495.0                        # 19.5 in deep (X)  -> ~465 sq in, about 10% more than the 3700BRM tablet
TOP_T = 25.0
TOP_CORNER_R = 45.0
TOP_EDGE_R = 8.0
DESK_GAPS = [250.0, 300.0, 350.0]    # backrest-to-desk-edge settings (at elbow height)
BACK_X_AT_ELBOW = -10.0              # backrest front face X at elbow height
COVE_LEN = 380.0                     # pencil cove near the far edge
COVE_W = 22.0
COVE_D = 6.0
COVE_FROM_FAR = 42.0                 # cove centreline distance from far edge

# default configuration shown in renders / assembled model
DEFAULT_HEIGHT_INDEX = 2             # 730 mm
DEFAULT_GAP_INDEX = 1                # 300 mm


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
    slide=0.22,           # per-side clearance, sliding fits
    snug=0.10,            # per-side clearance, press fits
    pin_d=1.75,           # pins are cut from 1.75 mm filament
    pin_hole=2.0,
)
