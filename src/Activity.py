
# Imports ----------------------------------------------------------------------
from typing import List, Tuple, Union
from datetime import datetime, time
from src.CSV import CSV


# Contants ---------------------------------------------------------------------
REFERENCE_DATETIME = datetime(2000, 1, 1, 6, 30, 0)    # Initial moment for the start of the record
HOURS_BY_LINE = 12                                     # Number of hours by line in plot
SECONDS_BY_LINE = HOURS_BY_LINE * 3600
REFERENCE_H, REFERENCE_M = REFERENCE_DATETIME.hour, REFERENCE_DATETIME.minute
REFERENCE_MIN_ID = 60*REFERENCE_H + REFERENCE_M

# ReferenceTime functions ------------------------------------------------------

def parse_datetime(time_str: str, dayshift: int=0) -> datetime:
    """Read a [datetime] object from a string of time and a dayshift (number of days to add to REFERENCE_DAY)."""
    h, m, s = time_str.split(":")
    h, m, s = int(h), int(m), int(s)
    return datetime(REFERENCE_DATETIME.year, REFERENCE_DATETIME.month, REFERENCE_DATETIME.day + dayshift, h, m, s)

def parse_time(time_str: str) -> time:
    """Read a [time] object from a string of time."""
    h, m, s = time_str.split(":")
    h, m, s = int(h), int(m), int(s)
    return time(h, m, s)

def add_dayshifts(csv: CSV) -> None:
    """Scan the CSV object and add a dayshift value for start and end of each entry."""

    # Init
    csv.add_empty_col("dayshift_start")
    csv.add_empty_col("dayshift_end")

    # Loop on entries
    for entry in csv:

        day = entry["day"]
        if len(day.split("/")) == 1:
            dayshift = int(day) - 1
            entry["dayshift_start"] = dayshift
            entry["dayshift_end"] = dayshift
        elif len(day.split("/")) == 2:
            dayshift_start, dayshift_end = [int(d) - 1 for d in day.split("/")]
            entry["dayshift_start"] = dayshift_start
            entry["dayshift_end"] = dayshift_end

def get_seconds(current_datetime: datetime) -> int:
    """"""
    dt = current_datetime - REFERENCE_DATETIME
    return int(dt.total_seconds())

def get_minute_id_in_day(current_datetime: datetime) -> int:
    """"""
    current_h, current_m = current_datetime.hour, current_datetime.minute
    current_min_id_shifted = 60*current_h + current_m
    return (current_min_id_shifted - REFERENCE_MIN_ID) % (60*24)

def get_coords(current_datetime: datetime) -> Tuple[int, int]:
    """"""
    seconds = get_seconds(current_datetime)
    return seconds % SECONDS_BY_LINE, seconds // SECONDS_BY_LINE


# Activity and Predator containers classes -------------------------------------

class Activity():
    """Contain class for an Activity."""

    def __init__(self, start: datetime, end: datetime, type: str, cam: str, video: str=""):
        self.start = start
        self.end = end
        self.type = type
        self.cam = cam
        self.video = video

    @property
    def nest(self) -> str:
        return self.video[1]
    
    @property
    def activity_splitted(self) -> str:
        return self.type

    @property
    def activity_groupped(self) -> str:
        if "transport" in self.type or "construction" in self.type:
            return "transport/construction"
        elif self.is_composed:
            raise ValueError(f"ERROR in {self}: activity='{self.type}' is composed but is ont 'transport' or 'construction'.")
        return self.type
    
    @ property
    def active_status(self) -> str:
        if self.type == "resting":
            return "inactive"
        else:
            return "active"
        
    @property
    def is_active(self) -> bool:
        return self.active_status == "active"
    
    @classmethod
    def parse_activity(cls, entry: dict, video: str="") -> "Activity":
        return Activity(
            parse_datetime(entry["start"], entry["dayshift_start"]),
            parse_datetime(entry["end"], entry["dayshift_end"]),
            entry["activity"], entry["cam"], video
        )
    
    @classmethod
    def parse_activies(cls, dataset: CSV, video: str="") -> List["Activity"]:
        return [cls.parse_activity(entry, video) for entry in dataset]

    def __str__(self) -> str:
        return f"Activity('{self.type}', c='{self.cam}', v='{self.video}'): {self.start} -> {self.end} ({self.duration_seconds} sec.)"
    
    def __contains__(self, input_datetime: datetime) -> bool:
        return self.start <= input_datetime < self.end
    
    @property
    def is_composed(self) -> bool:
        return len(self.type.split("+")) > 1
    
    @property
    def start_seconds(self) -> int:
        return get_seconds(self.start)

    @property
    def start_coords(self) -> Tuple[int, int]:
        return get_coords(self.start)
    
    @property
    def end_seconds(self) -> int:
        return get_seconds(self.end)
    
    @property
    def end_coords(self) -> Tuple[int, int]:
        return get_coords(self.end)
    
    @property
    def duration_seconds(self) -> int:
        return self.end_seconds - self.start_seconds
        
    def duration_minutes(self, day_part: Union[None, str]=None) -> int:
        coords_list = self.get_coords()
        if day_part is not None:
            assert day_part.lower() in ["", "all", "day", "night"], f"ERROR in duration_minutes(): day_part='{day_part}' should be in ['all', 'day', 'night']."
            if day_part.lower() == "day":
                coords_list = [c for c in coords_list if c[0][1] % 2 == 0]
            elif day_part.lower() == "night":
                coords_list = [c for c in coords_list if c[0][1] % 2 == 1]
        n_min = 0
        for coord_start, coord_end in coords_list:
            n_min += int((coord_end[0] - coord_start[0]) / 60)
        return n_min
    
    def get_coords(self) -> List[Tuple[int, int]]:
        coords_list = []
        start_coords = self.start_coords
        end_coords = self.end_coords
        current_coord = start_coords
        while True:
            if current_coord[1] < end_coords[1]:
                coords_list.append([current_coord, (SECONDS_BY_LINE, current_coord[1])])
                current_coord = (0, current_coord[1]+1)
            else:
                coords_list.append([current_coord, end_coords])
                break
        return coords_list

class Predator(Activity):
    """Contain class for an Predator."""

    def __init__(self, start: datetime, end: datetime, type: str, cam: str, video: str="", attacks: List[datetime]=[]):
        super().__init__(start, end, type, cam, video)
        self.attacks = attacks

    @classmethod
    def parse_predator(cls, entry: dict, video: str="") -> "Predator":

        # Parse attacks
        attacks = []
        dayshift_start = entry["dayshift_start"]
        previous_attack_time = parse_time(entry["start"])
        i = 1
        while f"attack{i}" in entry:
            attack_str = entry[f"attack{i}"]
            if attack_str == "": break
            attack_time = parse_time(attack_str)
            if attack_time < previous_attack_time:
                dayshift_start += 1
            attack = parse_datetime(attack_str, dayshift_start)
            attacks.append(attack)
            previous_attack_time = attack_time
            i += 1
        
        # Generate predator
        return Predator(
            parse_datetime(entry["start"], entry["dayshift_start"]),
            parse_datetime(entry["end"], entry["dayshift_end"]),
            entry["predator"], entry["cam"], video, attacks
        )
    
    @classmethod
    def parse_predators(cls, dataset: CSV, video: str="") -> List["Predator"]:
        return [cls.parse_predator(entry, video) for entry in dataset]
    
    def __str__(self) -> str:
        return f"Predator('{self.type}', c='{self.cam}', n='{self.video}'): {self.start} -> {self.end} ({len(self.attacks)} attacks, {self.duration_seconds} sec.)"
