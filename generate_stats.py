
# Imports ----------------------------------------------------------------------
import os
from typing import List
from datetime import datetime, time, timedelta
import numpy as np
from src.CSV import CSV
from src.Activity import REFERENCE_DATETIME, HOURS_BY_LINE, SECONDS_BY_LINE
from src.Activity import add_dayshifts, get_coords, get_seconds, Activity, Predator
from src.bootstrap_standard_error import bootstrap_standard_error

# Constants --------------------------------------------------------------------

# Names and paths
NAMES_LIST = ["N1_video1-2", "N2_video3-4-5-6-7", "N3_video8", "N3_video9"]              # File names to run on
DATA_DIR = "./data/"                                   # Directory of .csv data files (input)
STATS_DIR = "./stats/"                                 # Directory of stats (output)

# Data parameters
NESTS = ["1", "2", "3"]
CAMERAS = ["cam_inf", "cam_sup"]
ACTIVITIES_SPLITTES = ["resting", "column", "foraging", "transport", "construction", "transport+construction"]
ACTIVITIES_GROUPED = ["resting", "column", "foraging", "transport/construction"]
ACTIVE_STATUS = ["active", "inactive"]
PREDATORS = ["Opiliones", "Reduviidae"]

# Functions --------------------------------------------------------------------
def read_activities(do_print: bool=False) -> List[Activity]:
    activities_list = []
    for NAME in NAMES_LIST:
        ACTIVITY_PATH = os.path.join(DATA_DIR, f"{NAME}_Activity.csv")
        activities_data = CSV().read(ACTIVITY_PATH)
        add_dayshifts(activities_data)
        for activity in Activity.parse_activies(activities_data, NAME):
            if do_print: print(activity)
            activities_list.append(activity)
    return activities_list

def read_predators(do_print: bool=False) -> List[Predator]:
    predators_list = []
    for NAME in NAMES_LIST:
        PREDATORS_PATH = os.path.join(DATA_DIR, f"{NAME}_Predator.csv")
        predators_data = CSV().read(PREDATORS_PATH)
        add_dayshifts(predators_data)
        for predator in Predator.parse_predators(predators_data, NAME):
            if do_print: print(predator)
            predators_list.append(predator)
    return predators_list

def read_complete_activities() -> List[Activity]:
    IMCOMPLETE_ACTIVITY_DURATION_THR = 5
    complete_activities = []
    for NAME in NAMES_LIST:
        ACTIVITY_PATH = os.path.join(DATA_DIR, f"{NAME}_Activity.csv")
        activities_data = CSV().read(ACTIVITY_PATH)
        activities_video = []
        add_dayshifts(activities_data)
        for activity in Activity.parse_activies(activities_data, NAME):
            activities_video.append(activity)
        activities_lists_by_cam = [
            [a for a in activities_video if a.cam == cam]
            for cam in CAMERAS
        ]
        for activities_list_cam in activities_lists_by_cam:
            for i, a in enumerate(activities_list_cam):
                
                # Case of activities cutted by the video
                if (i == 0 or i == len(activities_list_cam)-1) or a.start != activities_list_cam[i-1].end or a.end != activities_list_cam[i+1].start:
                    # Skip cutted activities that are clearly too short
                    if a.duration_minutes() <= IMCOMPLETE_ACTIVITY_DURATION_THR:
                        continue

                complete_activities.append(a)
    return complete_activities

def merge_activities(activities_list: List[Activity]) -> List[Activity]:
    merged_activities_list = []
    for i, activity in enumerate(activities_list):
        previous = activities_list[i-1]
        if previous.video == activity.video and previous.cam == activity.cam and previous.activity_groupped == activity.activity_groupped and previous.end == activity.start:
            merged_activity = Activity(previous.start, activity.end, activity.type, activity.cam, activity.video)
            merged_activities_list.append(merged_activity)
        else:
            merged_activities_list.append(activity)
    return merged_activities_list

def get_duration(activities: List[Activity], day_part: str="all") -> int:
    n_min = 0
    for activity in activities:
        n_min += activity.duration_minutes(day_part)
    return n_min

# Execution --------------------------------------------------------------------


# Read Activities and Predators
activities_list = read_activities(do_print=False)
predators_list = read_predators(do_print=False)
complete_activities_list = read_complete_activities()


# STATS 0: Video Durations
print("\nVideos Durations ------------------------------------------------------")
videos_duration = CSV(["video", "cam", "duration_minutes", "duration_hours"])
for name in ["All"] + NAMES_LIST:
    name_activities = [a for a in activities_list if name == "All" or a.video == name]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in name_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        t = get_duration(cam_activities)
        h, m = t // 60, t % 60
        t_timedelta = timedelta(minutes=t)
        print(f"{name}-{cam}: {t} minutes ({h}h+{m}m)")
        entry = {"video": name, "cam": cam, "duration_minutes": t, "duration_hours": f"{h}h+{m}m"}
        videos_duration.add_entry(entry)
videos_duration_path = os.path.join(STATS_DIR, "0_video_durations.csv")
print(f"   -> Save file in '{videos_duration_path}'")
videos_duration.write(videos_duration_path)


# STAT 1a: temps en minutes par activités + temps total de la video: SPLITTED
print("\nTime by Activities: SPLITTED ------------------------------------------")
header = ["nest", "cam"]
for day_part in ["", "_day", "_night"]:
    for a in ACTIVITIES_SPLITTES:
        for measure in ["minutes", "ratio"]:
            header.append(f"{a}{day_part}_{measure}")
    header.append(f"total{day_part}_minutes")
time_by_activities = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": get_duration(cam_activities),
            "total_day_minutes": get_duration(cam_activities, "day"),
            "total_night_minutes": get_duration(cam_activities, "night"),
        }
        for a_type in ACTIVITIES_SPLITTES:
            type_activities = [a for a in cam_activities if a.activity_splitted == a_type]
            for day_part in["", "_day", "_night"]:
                minutes = get_duration(type_activities, day_part.removeprefix("_"))
                total = entry[f"total{day_part}_minutes"]
                entry[f"{a_type}{day_part}_minutes"] = minutes
                entry[f"{a_type}{day_part}_ratio"] = f"{minutes / total:.4f}"
        time_by_activities.add_entry(entry)
time_by_activities.show()
time_by_activities_path = os.path.join(STATS_DIR, "1a_time_by_acivities_splitted.csv")
print(f"   -> Save file in '{time_by_activities_path}'")
time_by_activities.write(time_by_activities_path)


# STAT 1b: temps en minutes par activités + temps total de la video: GROUPED
print("\nTime by Activities: GROUPED -------------------------------------------")
header = ["nest", "cam"]
for day_part in ["", "_day", "_night"]:
    for a in ACTIVITIES_GROUPED:
        for measure in ["minutes", "ratio"]:
            header.append(f"{a}{day_part}_{measure}")
    header.append(f"total{day_part}_minutes")
time_by_activities = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": get_duration(cam_activities),
            "total_day_minutes": get_duration(cam_activities, "day"),
            "total_night_minutes": get_duration(cam_activities, "night"),
        }
        for a_type in ACTIVITIES_GROUPED:
            type_activities = [a for a in cam_activities if a.activity_groupped == a_type]
            for day_part in["", "_day", "_night"]:
                minutes = get_duration(type_activities, day_part.removeprefix("_"))
                total = entry[f"total{day_part}_minutes"]
                entry[f"{a_type}{day_part}_minutes"] = minutes
                entry[f"{a_type}{day_part}_ratio"] = f"{minutes / total:.4f}"
        time_by_activities.add_entry(entry)
time_by_activities.show()
time_by_activities_path = os.path.join(STATS_DIR, "1b_time_by_acivities_grouped.csv")
print(f"   -> Save file in '{time_by_activities_path}'")
time_by_activities.write(time_by_activities_path)


# STAT 1c: temps en minutes par activités + temps total de la video: ACTIVE STATUS
print("\nTime by Activities: ACTIVE STATUS -------------------------------------")
header = ["nest", "cam"]
for day_part in ["", "_day", "_night"]:
    for a in ACTIVE_STATUS:
        for measure in ["minutes", "ratio"]:
            header.append(f"{a}{day_part}_{measure}")
    header.append(f"total{day_part}_minutes")
time_by_activities = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": get_duration(cam_activities),
            "total_day_minutes": get_duration(cam_activities, "day"),
            "total_night_minutes": get_duration(cam_activities, "night"),
        }
        for a_type in ACTIVE_STATUS:
            type_activities = [a for a in cam_activities if a.active_status == a_type]
            for day_part in["", "_day", "_night"]:
                minutes = get_duration(type_activities, day_part.removeprefix("_"))
                total = entry[f"total{day_part}_minutes"]
                entry[f"{a_type}{day_part}_minutes"] = minutes
                entry[f"{a_type}{day_part}_ratio"] = f"{minutes / total:.4f}"
        time_by_activities.add_entry(entry)
time_by_activities.show()
time_by_activities_path = os.path.join(STATS_DIR, "1c_time_by_acive_status.csv")
print(f"   -> Save file in '{time_by_activities_path}'")
time_by_activities.write(time_by_activities_path)


# STATS 2: temps de présence en minutes par prédateurs + temps total de la video
print("\nPredator Presence Time ------------------------------------------------")
header = ["nest", "cam"]
for day_part in ["", "_day", "_night"]:
    for p in PREDATORS:
        for measure in ["minutes", "ratio"]:
            header.append(f"{p}{day_part}_{measure}")
    header.append(f"total{day_part}_minutes")
predator_presence_times = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    nest_predators = [p for p in predators_list if nest == "All" or p.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        cam_predators = [p for p in nest_predators if cam == "All" or p.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": get_duration(cam_activities),
            "total_day_minutes": get_duration(cam_activities, "day"),
            "total_night_minutes": get_duration(cam_activities, "night"),
        }
        for p_type in PREDATORS:
            type_predators = [p for p in cam_predators if p.type == p_type]
            for day_part in["", "_day", "_night"]:
                minutes = get_duration(type_predators, day_part.removeprefix("_"))
                total = entry[f"total{day_part}_minutes"]
                entry[f"{p_type}{day_part}_minutes"] = minutes
                entry[f"{p_type}{day_part}_ratio"] = f"{minutes / total:.4f}"
        predator_presence_times.add_entry(entry)
predator_presence_times.show()
predator_presence_times_path = os.path.join(STATS_DIR, "2_predators_presence_time.csv")
print(f"   -> Save file in '{predator_presence_times_path}'")
predator_presence_times.write(predator_presence_times_path)


# STATS 3: nb d'attaque moyen par moment de présence par prédateurs, nb de présence par prédateur
print("\nPredator Counts and Attack Counts -------------------------------------")
header = ["nest", "cam"]
for p in PREDATORS:
    for measure in ["n_presences", "n_attacks", "n_attacks_by_presence"]:
        header.append(f"{p}_{measure}")
header.append(f"total_minutes")
predators_counts = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    nest_predators = [p for p in predators_list if nest == "All" or p.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        cam_predators = [p for p in nest_predators if cam == "All" or p.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": get_duration(cam_activities),
        }
        for p_type in PREDATORS:
            type_predators = [p for p in cam_predators if p.type == p_type]
            entry[f"{p_type}_n_presences"] = len(type_predators)
            entry[f"{p_type}_n_attacks"] = sum([len(p.attacks) for p in type_predators])
            entry[f"{p_type}_n_attacks_by_presence"] = f"{np.mean([len(p.attacks) for p in type_predators]):.4f}"
        predators_counts.add_entry(entry)
predators_counts.show()
predators_counts_path = os.path.join(STATS_DIR, "3_predators_counts.csv")
print(f"   -> Save file in '{predators_counts_path}'")
predators_counts.write(predators_counts_path)


# STATS 4a: temps moyen de présence des prédateurs
print("\nPredator Average Precence Duration -------------------------------------")
header = ["nest", "cam"]
for p in PREDATORS:
    for measure in ["n_presences", "average_duration_minutes", "median_duration_minutes"]:
        header.append(f"{p}_{measure}")
predators_average_times = CSV(header)
for nest in ["All"] + NESTS:
    nest_predators = [p for p in predators_list if nest == "All" or p.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_predators = [p for p in nest_predators if cam == "All" or p.cam == cam]
        if len(cam_predators) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
        }
        for p_type in PREDATORS:
            type_predators = [p for p in cam_predators if p.type == p_type]
            entry[f"{p_type}_n_presences"] = len(type_predators)
            entry[f"{p_type}_average_duration_minutes"] = f"{np.mean([p.duration_minutes() for p in type_predators]):.4f}"
            entry[f"{p_type}_median_duration_minutes"] = f"{np.median([p.duration_minutes() for p in type_predators]):.4f}"
        predators_average_times.add_entry(entry)
predators_average_times.show()
predators_average_times_path = os.path.join(STATS_DIR, "4a_predators_average_duration.csv")
print(f"   -> Save file in '{predators_average_times_path}'")
predators_average_times.write(predators_average_times_path)


# STATS 4b: temps moyen par activité (si on a le début et la fin de l'activité)
print("\nActivities durations SPLIEED ------------------------------------------")
header = ["nest", "cam"]
for a in ACTIVITIES_SPLITTES:
    for measure in ["n", "average_duration_minutes", "median_duration_minutes"]:
        header.append(f"{a}_{measure}")
activities_durations = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in complete_activities_list if nest == "All" or a.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
        }
        for a_type in ACTIVITIES_SPLITTES:
            type_activities = [a for a in cam_activities if a.activity_splitted == a_type]
            n = len(type_activities)
            average_duration = np.mean([a.duration_minutes() for a in type_activities])
            median_duration = np.median([a.duration_minutes() for a in type_activities])
            entry[f"{a_type}_n"] = n
            entry[f"{a_type}_average_duration_minutes"] = f"{average_duration:.4f}"
            entry[f"{a_type}_median_duration_minutes"] = f"{median_duration:.4f}"
        activities_durations.add_entry(entry)
activities_durations.show()
activities_durations_path = os.path.join(STATS_DIR, "4b_activities_splitted_average_duration.csv")
print(f"   -> Save file in '{activities_durations_path}'")
activities_durations.write(activities_durations_path)


# STATS 4c: temps moyen par activité GROUPED (si on a le début et la fin de l'activité)
print("\nActivities durations GROUPED ------------------------------------------")
header = ["nest", "cam"]
for a in ACTIVITIES_GROUPED:
    for measure in ["n", "average_duration_minutes", "median_duration_minutes"]:
        header.append(f"{a}_{measure}")
merged_activities = merge_activities(complete_activities_list)
activities_durations = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in merged_activities if nest == "All" or a.nest == nest]
    for cam in ["All"] + CAMERAS:
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        if len(cam_activities) == 0: continue
        entry = {
            "nest": nest, "cam": cam,
        }
        for a_type in ACTIVITIES_GROUPED:
            type_activities = [a for a in cam_activities if a.activity_groupped == a_type]
            n = len(type_activities)
            average_duration = np.mean([a.duration_minutes() for a in type_activities])
            median_duration = np.median([a.duration_minutes() for a in type_activities])
            entry[f"{a_type}_n"] = n
            entry[f"{a_type}_average_duration_minutes"] = f"{average_duration:.4f}"
            entry[f"{a_type}_median_duration_minutes"] = f"{median_duration:.4f}"
        activities_durations.add_entry(entry)
activities_durations.show()
activities_durations_path = os.path.join(STATS_DIR, "4c_activities_grouped_average_duration.csv")
print(f"   -> Save file in '{activities_durations_path}'")
activities_durations.write(activities_durations_path)


# STATS 4d: temps moyen des activités + standard deviation + standard error + bootstrap 
print("\nActivities durations + standard errors --------------------------------")
header = [
    "activity", "n_observations",
    "duration_mean", "duration_median", "duration_standard_deviation",
    "standard_error_on_mean", "considence_interval_95_on_mean",
    "standard_error_on_mean_bootstrap", "considence_interval_95_on_mean_bootstrap",
    "standard_error_on_median_bootstrap", "considence_interval_95_on_median_bootstrap",
]
activities_durations_se = CSV(header)
ZSCORE_95 = 1.96
for a_type in ACTIVITIES_GROUPED:

    # Get durations
    type_activities = [a for a in merged_activities if a.activity_groupped == a_type]
    durations = np.array([a.duration_minutes() for a in type_activities])
    entry = {
        "activity": a_type,
        "n_observations": len(durations)
    }

    # Base stats
    mean = np.mean(durations)
    median = np.median(durations)
    std = np.sqrt((1.0/(len(durations) - 1.0)) * np.sum((durations - mean)**2)) # Since N is low, we use the Bessel's correction (which np.std() does not).
    entry["duration_mean"] = f"{mean:.4f}"
    entry["duration_median"] = f"{median:.4f}"
    entry["duration_standard_deviation"] = f"{std:.4f}"


    # Classical SEM, CI computations on mean
    sem_mean = std / np.sqrt(len(durations))
    ci95_mean = mean + np.array([-sem_mean, +sem_mean])*ZSCORE_95
    entry["standard_error_on_mean"] = f"{sem_mean:4f}"
    entry["considence_interval_95_on_mean"] = f"{ci95_mean[0]:4f}:{ci95_mean[1]:.4f}"

    # Bootstrap SEM, CI computations on mean
    sem_mean_boot, ci95_mean_boot = bootstrap_standard_error(durations, np.mean)
    entry["standard_error_on_mean_bootstrap"] = f"{sem_mean_boot:4f}"
    entry["considence_interval_95_on_mean_bootstrap"] = f"{ci95_mean_boot[0]:4f}:{ci95_mean_boot[1]:.4f}"

    # Bootstrap SEM, CI computations on median
    sem_median_boot, ci95_median_boot = bootstrap_standard_error(durations, np.median)
    entry["standard_error_on_median_bootstrap"] = f"{sem_median_boot:4f}"
    entry["considence_interval_95_on_median_bootstrap"] = f"{ci95_median_boot[0]:4f}:{ci95_median_boot[1]:.4f}"

    activities_durations_se.add_entry(entry)
activities_durations_se.show()
activities_durations_se_path = os.path.join(STATS_DIR, "4d_activities_durations_standard_errors.csv")
print(f"   -> Save file in '{activities_durations_se_path}'")
activities_durations_se.write(activities_durations_se_path)


# STATS 7: predateur temps de presence en presence de constricto et en absence
#   3temps : temps total de présence par prédateurs, en présence des constricto et en absence  = resting) + temps total de la video ou les constricto on été actif et inactif 
print("\nPredator times by Active/Inactive -------------------------------------")
header = ["nest", "cam"]
predator_properties = [
    "predator", "predator_active", "predator_inactive",
    "Opiliones", "Opiliones_active", "Opiliones_inactive",
    "Reduviidae", "Reduviidae_active", "Reduviidae_inactive",
]
for a in ACTIVE_STATUS:
    for measure in ["minutes", "ratio"]:
        header.append(f"{a}_{measure}")
for p in PREDATORS:
    for measure in ["minutes", "ratio"]:
            header.append(f"{p}_{measure}")
for p in PREDATORS:
    for a in ACTIVE_STATUS:
        for measure in ["minutes", "ratio"]:
            header.append(f"{p}_{a}_{measure}")
header.append(f"total_minutes")
predators_constricto_activity = CSV(header)
for nest in ["All"] + NESTS:
    nest_activities = [a for a in activities_list if nest == "All" or a.nest == nest]
    nest_predators = [p for p in predators_list if nest == "All" or p.nest == nest]
    for cam in ["All"] + CAMERAS:

        # List activities and predators of the cam
        cam_activities = [a for a in nest_activities if cam == "All" or a.cam == cam]
        cam_predators = [p for p in nest_predators if cam == "All" or p.cam == cam]

        # Skip when no occurances
        if len(cam_activities) == 0: continue
        if len(cam_predators) == 0: continue

        # Split active / inactive activities
        activities_active = [a for a in cam_activities if a.is_active]
        activities_inactive = [a for a in cam_activities if not a.is_active]

        # Get times and ratios
        total_minutes = get_duration(cam_activities)
        active_minutes = get_duration(activities_active)
        inactive_minutes = get_duration(activities_inactive)
        active_ratio = active_minutes / total_minutes
        inactive_ratio = inactive_minutes / total_minutes

        # Set entry base properties
        entry = {
            "nest": nest, "cam": cam,
            "total_minutes": total_minutes,
            "active_minutes": active_minutes,
            "active_ratio": f"{active_ratio:.4f}",
            "inactive_minutes": inactive_minutes,
            "inactive_ratio": f"{inactive_ratio:.4f}",
        }

        for p_type in PREDATORS:

            # Split predators if ther are during an active or an inactive activity
            predators = [p for p in cam_predators if p.type == p_type]
            predators_active =   [p for p in predators if any([p.start in a and p.cam == a.cam and p.video == a.video for a in activities_active])]
            predators_inactive = [p for p in predators if any([p.start in a and p.cam == a.cam and p.video == a.video for a in activities_inactive])]

            # Get times and ratios
            predator_minutes = get_duration(predators)
            predator_ratio = predator_minutes / total_minutes
            predator_active_minutes = get_duration(predators_active)
            predator_active_ratio = predator_active_minutes / active_minutes
            predator_inactive_minutes = get_duration(predators_inactive)
            predator_inactive_ratio = predator_inactive_minutes / inactive_minutes
            entry[f"{p_type}_minutes"] = predator_minutes
            entry[f"{p_type}_ratio"] = f"{predator_ratio:.4f}"
            entry[f"{p_type}_active_minutes"] = predator_active_minutes
            entry[f"{p_type}_active_ratio"] = f"{predator_active_ratio:.4f}"
            entry[f"{p_type}_inactive_minutes"] = predator_inactive_minutes
            entry[f"{p_type}_inactive_ratio"] = f"{predator_inactive_ratio:.4f}"
        predators_constricto_activity.add_entry(entry)
predators_constricto_activity.show()
predators_constricto_activity_path = os.path.join(STATS_DIR, "7_predators_constricto_activity.csv")
print(f"   -> Save file in '{predators_constricto_activity_path}'")
predators_constricto_activity.write(predators_constricto_activity_path)
