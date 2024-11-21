
# Imports ----------------------------------------------------------------------
import os
from datetime import datetime, time, timedelta
#import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from src.CSV import CSV
from src.Activity import REFERENCE_DATETIME, HOURS_BY_LINE, SECONDS_BY_LINE
from src.Activity import add_dayshifts, get_coords, get_seconds, Activity, Predator


# Constants --------------------------------------------------------------------

# Names and paths
NAMES_LIST = [                                         # File names to run on
    "N1A", "N2A", "N3A", "N3B",
]
DATA_DIR = "./data/"                                   # Directory of .csv data files (input)
FIG_DIR = "./fig/"                                     # Directory of figures (output)
EXTENTIONS = ["png"]                                   # List of extentions to which save the figures
DPI = 300                                              # Dots per inch in saved figures

# Data parameters
RENAME_COLUMN_MAP = {                                  # Just a mapping for .csv column names for clarity
    "debut": "start",
    "ending": "end",
}
POSSIBLE_CAMERAS = ["cam_inf", "cam_sup"]              # List of possible cameras

# Color parameters
COLOR_MAP = {
    "resting": (200/255, 200/255, 200/255),
    "transport": (0/255, 95/255, 135/255),
    "construction": (0/255, 43/255, 51/255),
    "column": (0/255, 128/255, 0/255),
    "foraging": (115/255, 75/255, 155/255),
    "Opiliones": (20/255, 20/255, 60/255),
    "Reduviidae": (120/255, 20/255, 20/255),
    "hours_font_color": (80/255, 80/255, 80/255),
}

# Plot size parameters
DELTA_TICKS_HOURS = 1                                  # Indicate hh:mm each n hours
X_MARGIN = 1000
SPACE_TOP = 650
ATTACK_BAR_HEIGHT = 350
ATTACK_MARKER_SIZE = 12
ATTACK_ALPHA = 0.5
PREDATOR_BAR_HEIGHT = 650
SPACE_PREDATORS = 100
SPACE_PREDATOR_ACTIVITY = 200
ACTIVITY_BAR_HEIGHT = 4000
HOURS_BAR_HEIGHT = 700
HOURS_FONT_SIZE = 7
SPACE_BOTTOM = 650
SPACE_TIME = 5000

# Plot other parameters
#DARKGRID = False                          # Use seaborn darkgrid mode
X_TICKS, Y_TICKS = False, False           # Use ticks marks on the plot
HOURS_LINE_WIDTH = 0.6                    # Line width of the horizontal hour line
HOURS_LINE_N_TICKS = 12                   # Number of the hoursline ticks
HOURS_LINE_TICKS_LENGTH = 175             # Vertical length of the hoursline ticks
BAR_RECTANGLE_LINE_WIDTH = 0.6            # Width of the activity rectangle countour lines (rectangle is here even if there is not activity)
BAR_COUNTOUR_LINE_WIDTH = 0.5             # Width of the activity countour lines (around each activity)
BAR_COUNTOUR_COLOR = None                 # Color of the activity countour lines (around each activity): Set None to keep the same color as the activity bar

# Execution --------------------------------------------------------------------

for NAME in NAMES_LIST:
    print("\n")
    print("\n---------------------------------------------------------------------------------------")
    print(f"GENERATE TIME FIGURE ON '{NAME}' ---------------------------------------------------------")

    # Init constants
    ATTACK_OPI_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT / 2
    OPI_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT / 2
    RED_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATORS + PREDATOR_BAR_HEIGHT / 2
    ATTACK_RED_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATORS + PREDATOR_BAR_HEIGHT + ATTACK_BAR_HEIGHT / 2
    ACTIVITY_CENTER =  SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATORS + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT / 2
    HOURS_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATORS + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT + HOURS_BAR_HEIGHT / 2
    CAM_LINE_HEIGHT =  SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATORS + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT + HOURS_BAR_HEIGHT + SPACE_BOTTOM

    # Read activity data
    ACTIVITY_PATH = os.path.join(DATA_DIR, f"{NAME}_C.csv")
    activities_data = CSV().read(ACTIVITY_PATH)
    for old_name, new_name in RENAME_COLUMN_MAP.items():
        activities_data.rename_col(old_name, new_name)
    add_dayshifts(activities_data)
    activities_data.show(n_entries=25)

    # Parse activities
    activities_list = []
    for entry in activities_data:
        activity = Activity.parse_activity(entry, NAME)
        print(activity)
        activities_list.append(activity)
    print()

    # Detect existing cameras
    cameras = []
    for activity in activities_list:
        cam = activity.cam
        if cam not in POSSIBLE_CAMERAS:
            raise ValueError(f"Non-existing cam '{cam}'")
        if cam not in cameras:
            cameras.append(cam)
    TIME_LINE_HEIGHT = CAM_LINE_HEIGHT * len(cameras) + SPACE_TIME
    cameras = cameras[::-1] # Reverse the order so cam_sup is before cam_int

    # Verify coherence in activities
    for current_cam in cameras:
        previous_activity_start = REFERENCE_DATETIME
        for i, activity in enumerate(activities_list):
            if activity.cam != current_cam: continue
            if activity.end < activity.start:
                raise ValueError(f"ERROR in {activity}: \n activity end is before start.")
            if activity.start < previous_activity_start:
                raise ValueError(f"ERROR in {activity}: \n activity {i} starts before previous activity")
            previous_activity_start = activity.start

    # Read predators data
    PREDATORS_PATH = os.path.join(DATA_DIR, f"{NAME}_P.csv")
    predators_data = CSV().read(PREDATORS_PATH)
    for old_name, new_name in RENAME_COLUMN_MAP.items():
        predators_data.rename_col(old_name, new_name)
    add_dayshifts(predators_data)
    predators_data.show(n_entries=25)

    # Parse predators
    predators_list = []
    for entry in predators_data:
        if entry["predator"] == "video": continue
        predator = Predator.parse_predator(entry, NAME)
        print(predator)
        predators_list.append(predator)
    print()

    # Delete Reduviidae predator bar from plot when they are not present
    if "Reduviidae" not in [p.type for p in predators_list]:
        ATTACK_OPI_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT / 2
        OPI_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT / 2
        ACTIVITY_CENTER =  SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT / 2
        HOURS_CENTER = SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT + HOURS_BAR_HEIGHT / 2
        CAM_LINE_HEIGHT =  SPACE_TOP + ATTACK_BAR_HEIGHT + PREDATOR_BAR_HEIGHT + SPACE_PREDATOR_ACTIVITY + ACTIVITY_BAR_HEIGHT + HOURS_BAR_HEIGHT + SPACE_BOTTOM

    # Verify coherence in predators
    for current_cam in cameras:
        previous_predator_start = REFERENCE_DATETIME
        for i, predator in enumerate(predators_list):
            if predator.cam != current_cam: continue
            if predator.end < predator.start:
                print(f"ERROR in {predator}: \n predator end is before start.")
                #raise ValueError(f"ERROR in {predator}: \n predator end is before start.")
            if predator.start < previous_predator_start:
                print(f"ERROR in {predator}: \n predator end is before start.")
                #raise ValueError(f"ERROR in {predator}: \n predator {i} starts before previous predator")
            previous_predator_start = predator.start

    # Init plot
    first_start, last_end = activities_list[0].start, activities_list[-1].end
    last_y = get_coords(last_end)[1] + 1
    #if DARKGRID:
    #    sns.set_style("darkgrid")
    fig, ax = plt.subplots()
    #if not DARKGRID:
    # Hiding the spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    #plt.title(f"Timeline: {NAME}")
    x0, x1 = 0, SECONDS_BY_LINE
    dx = x1 - x0
    y0, y1 = -(TIME_LINE_HEIGHT*last_y - SPACE_TIME), 0
    dy = y1 - y0
    plt.xlim(x0-X_MARGIN, x1+X_MARGIN)
    plt.ylim(y0, y1)
    #print(dx/3600, dy/3600)
    plt.gcf().set_size_inches(dx/3600, dy/3600)

    # Set ticks
    if X_TICKS:
        ax.set_xticks([x0, x1], ["", ""])
    else:
        ax.set_xticks([], [])
    y_ticks = []
    for cam_i, cam in enumerate(cameras):
        for i in range(last_y):
            y_ticks.append(- SPACE_TOP - i*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT)
            y_ticks.append(- ACTIVITY_CENTER - ACTIVITY_BAR_HEIGHT/2 - i*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT)
    if Y_TICKS:
        ax.set_yticks(y_ticks, ["" for _ in y_ticks])
    else:
        ax.set_yticks([], [])

    # Draw hours line, line this: |----------|----------|----------|
    for i_hoursline, y0 in enumerate(y_ticks):
        if i_hoursline % 2 == 0: continue # only drown hour line at bottom
        plt.plot([x0, x1], [y0, y0], color="black", linewidth=HOURS_LINE_WIDTH)
        dx = (x1 - x0) / HOURS_LINE_N_TICKS
        for j_hoursline in range(HOURS_LINE_N_TICKS+1):
            x_hoursline = x0 + j_hoursline*dx
            plt.plot([x_hoursline, x_hoursline], [y0, y0-HOURS_LINE_TICKS_LENGTH], color="black", linewidth=HOURS_LINE_WIDTH)

    # Draw bar rectangle (even when there is no activity)
    for i_hoursline, y0 in enumerate(y_ticks):
        if i_hoursline % 2 == 0: continue # only drown hour line at bottom
        plt.plot([x0, x1], [y0, y0], color="black", linewidth=BAR_RECTANGLE_LINE_WIDTH)
        plt.plot([x0, x1], [y0+ACTIVITY_BAR_HEIGHT, y0+ACTIVITY_BAR_HEIGHT], color="black", linewidth=BAR_RECTANGLE_LINE_WIDTH)
        plt.plot([x0, x0], [y0, y0+ACTIVITY_BAR_HEIGHT], color="black", linewidth=BAR_RECTANGLE_LINE_WIDTH)
        plt.plot([x1, x1], [y0, y0+ACTIVITY_BAR_HEIGHT], color="black", linewidth=BAR_RECTANGLE_LINE_WIDTH)

    # Plot time steps
    for cam_i, cam in enumerate(cameras):
        current_datetime = REFERENCE_DATETIME
        current_coords = get_coords(current_datetime)
        color = COLOR_MAP["hours_font_color"]
        while current_coords[1] < last_y:
            plt.text( # Plot text-hours
                current_coords[0], -HOURS_CENTER - current_coords[1]*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT,
                current_datetime.strftime('%H:%M'),
                fontsize=HOURS_FONT_SIZE, horizontalalignment='center', verticalalignment='top', color=color,
            )
            if current_coords[0] == 0 and current_coords[1] != 0:
                plt.text( # Plot text-hours: repeat also starting hour above
                    SECONDS_BY_LINE, -HOURS_CENTER - (current_coords[1]-1)*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT,
                    current_datetime.strftime('%H:%M'),
                    fontsize=HOURS_FONT_SIZE, horizontalalignment='center', verticalalignment='top', color=color,
                )
            current_datetime += timedelta(hours=DELTA_TICKS_HOURS)
            current_coords = get_coords(current_datetime)
        plt.text( # Plot text-hours: plot last hour of the last line
            SECONDS_BY_LINE, -HOURS_CENTER - (current_coords[1]-1)*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT,
            current_datetime.strftime('%H:%M'),
            fontsize=HOURS_FONT_SIZE, horizontalalignment='center', verticalalignment='top', color=color,
        )

    # Plot activities
    mpl.rcParams['hatch.linewidth'] = 11
    for cam_i, cam in enumerate(cameras):
        for activity in activities_list:
            if activity.cam != cam: continue
            if not activity.is_composed:
                color = COLOR_MAP[activity.type]
                edgecolor = BAR_COUNTOUR_COLOR if BAR_COUNTOUR_COLOR is not None else color
                for (start_x, start_y), (end_x, end_y) in activity.get_coords():
                    duration = end_x - start_x
                    ax.barh(
                        [-ACTIVITY_CENTER - start_y*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT], [duration], left=[start_x],
                        height=ACTIVITY_BAR_HEIGHT,
                        color=color, edgecolor=edgecolor, alpha=1.0, linewidth=BAR_COUNTOUR_LINE_WIDTH,
                    )
            else:
                color1 = COLOR_MAP[activity.type.split("+")[0]]
                color2 = COLOR_MAP[activity.type.split("+")[1]]
                edgecolor1 = BAR_COUNTOUR_COLOR if BAR_COUNTOUR_COLOR is not None else color1
                for (start_x, start_y), (end_x, end_y) in activity.get_coords():
                    duration = end_x - start_x
                    ax.barh(
                        [-ACTIVITY_CENTER - start_y*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT], [duration], left=[start_x],
                        height=ACTIVITY_BAR_HEIGHT,
                        color=color1, edgecolor=edgecolor1, alpha=1.0, linewidth=BAR_COUNTOUR_LINE_WIDTH,
                    )
                    ax.barh(
                        [-ACTIVITY_CENTER - start_y*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT], [duration], left=[start_x],
                        height=ACTIVITY_BAR_HEIGHT,
                        color='none', edgecolor=color2, alpha=1.0, hatch='/', linewidth=BAR_COUNTOUR_LINE_WIDTH,
                    )

    # Plot predators
    for cam_i, cam in enumerate(cameras):
        for predator in predators_list:
            if predator.cam != cam: continue
            color = COLOR_MAP[predator.type]
            CENTER = OPI_CENTER if predator.type == "Opiliones" else RED_CENTER
            for (start_x, start_y), (end_x, end_y) in predator.get_coords():
                duration = end_x - start_x
                ax.barh(
                        [-CENTER - start_y*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT], [duration], left=[start_x],
                        color=[color], edgecolor="none", alpha=1.0, height=PREDATOR_BAR_HEIGHT, linewidth=BAR_COUNTOUR_LINE_WIDTH,
                )

    # Plot attacks
    for cam_i, cam in enumerate(cameras):
        for predator in predators_list:
            if predator.cam != cam: continue
            color = COLOR_MAP[predator.type]
            CENTER = ATTACK_OPI_CENTER if predator.type == "Opiliones" else ATTACK_RED_CENTER
            for attack in predator.attacks:
                x, y = get_coords(attack)
                plt.scatter([x], [-CENTER - y*TIME_LINE_HEIGHT - cam_i*CAM_LINE_HEIGHT], marker="x", color=color, sizes=[ATTACK_MARKER_SIZE], alpha=ATTACK_ALPHA)

    # Save figure
    for ext in EXTENTIONS:
        FIG_PATH = os.path.join(FIG_DIR, f"{NAME}.{ext}")
        print(f"Save file at '{FIG_PATH}'")
        plt.savefig(FIG_PATH, bbox_inches='tight', dpi=DPI)

