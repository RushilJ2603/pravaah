"""Synthetic Delhi bus network (SOLUTION.md section 28.9).

Delhi's official GTFS is form-gated and its file host was unreachable when this
was built, so the demo network is generated rather than imported. Everything
here is therefore **synthetic and must be labelled as such** -- but it is not
arbitrary:

* Stop names and coordinates are real Delhi places, so the map reads as Delhi
  and distances between stops are real distances.
* Corridors follow real arterial alignments (the Ring Road, the Outer Ring, GT
  Karnal Road, Mathura Road, and so on), so route shapes are plausible rather
  than random walks.
* Route lengths and stop spacing are set from the Delhi figures in the city
  profile, not invented per route.

Swapping this for the real GTFS later is a data change, not a code change: the
importer produces the same tables this module writes into.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass

log = logging.getLogger(__name__)

#: Real Delhi locations, (name, lat, lon), grouped loosely by corridor. These are
#: actual places at actual coordinates -- the synthesis is in which of them a
#: route connects, not in where they are.
DELHI_PLACES: list[tuple[str, float, float]] = [
    # Central
    ("Connaught Place", 28.6315, 77.2167),
    ("New Delhi Railway Station", 28.6425, 77.2199),
    ("Paharganj", 28.6465, 77.2120),
    ("Chandni Chowk", 28.6506, 77.2303),
    ("Red Fort", 28.6562, 77.2410),
    ("Kashmere Gate ISBT", 28.6675, 77.2285),
    ("Civil Lines", 28.6820, 77.2230),
    ("India Gate", 28.6129, 77.2295),
    ("Mandi House", 28.6258, 77.2340),
    ("ITO", 28.6289, 77.2410),
    # South
    ("AIIMS", 28.5672, 77.2100),
    ("Green Park", 28.5590, 77.2070),
    ("Hauz Khas", 28.5494, 77.2001),
    ("Malviya Nagar", 28.5355, 77.2110),
    ("Saket", 28.5245, 77.2066),
    ("Chirag Delhi", 28.5400, 77.2240),
    ("Nehru Place", 28.5494, 77.2500),
    ("Kalkaji", 28.5490, 77.2590),
    ("Govindpuri", 28.5390, 77.2630),
    ("Lajpat Nagar", 28.5700, 77.2430),
    ("Defence Colony", 28.5730, 77.2300),
    ("Moolchand", 28.5680, 77.2350),
    ("Ashram", 28.5720, 77.2590),
    ("Sarai Kale Khan ISBT", 28.5900, 77.2580),
    ("Nizamuddin", 28.5890, 77.2510),
    ("Badarpur", 28.4930, 77.3020),
    ("Tughlakabad", 28.5070, 77.2600),
    ("Vasant Kunj", 28.5200, 77.1590),
    ("Munirka", 28.5540, 77.1740),
    ("RK Puram", 28.5640, 77.1800),
    # West
    ("Karol Bagh", 28.6510, 77.1900),
    ("Rajouri Garden", 28.6490, 77.1200),
    ("Tilak Nagar", 28.6390, 77.0950),
    ("Janakpuri", 28.6210, 77.0810),
    ("Uttam Nagar", 28.6210, 77.0590),
    ("Dwarka Sector 21", 28.5520, 77.0580),
    ("Dwarka Mor", 28.6190, 77.0330),
    ("Najafgarh", 28.6090, 76.9800),
    ("Punjabi Bagh", 28.6740, 77.1310),
    ("Vikas Puri", 28.6370, 77.0680),
    ("Naraina", 28.6300, 77.1400),
    # North
    ("Azadpur", 28.7070, 77.1750),
    ("Model Town", 28.7020, 77.1930),
    ("Pitampura", 28.6980, 77.1320),
    ("Rohini Sector 18", 28.7380, 77.1200),
    ("Jahangirpuri", 28.7290, 77.1620),
    ("GTB Nagar", 28.6990, 77.2070),
    ("Mukherjee Nagar", 28.7050, 77.2110),
    ("Wazirabad", 28.7180, 77.2300),
    ("Narela", 28.8530, 77.0920),
    ("Alipur", 28.7970, 77.1350),
    # East
    ("Anand Vihar ISBT", 28.6470, 77.3160),
    ("Preet Vihar", 28.6410, 77.2950),
    ("Laxmi Nagar", 28.6300, 77.2770),
    ("Mayur Vihar", 28.6090, 77.2950),
    ("Shahdara", 28.6730, 77.2890),
    ("Seelampur", 28.6700, 77.2670),
    ("Welcome", 28.6720, 77.2780),
    ("Dilshad Garden", 28.6810, 77.3210),
    ("Vivek Vihar", 28.6720, 77.3150),
    ("Yamuna Vihar", 28.6960, 77.2720),
]

#: Corridors as ordered lists of indices into DELHI_PLACES. Each is a plausible
#: real alignment; routes are built by walking a corridor and branching.
CORRIDORS: list[list[str]] = [
    ["Narela", "Alipur", "Jahangirpuri", "Azadpur", "Model Town", "GTB Nagar",
     "Civil Lines", "Kashmere Gate ISBT", "Chandni Chowk", "New Delhi Railway Station",
     "Connaught Place"],
    ["Connaught Place", "Mandi House", "ITO", "Nizamuddin", "Sarai Kale Khan ISBT",
     "Ashram", "Govindpuri", "Tughlakabad", "Badarpur"],
    ["Kashmere Gate ISBT", "Red Fort", "Chandni Chowk", "Karol Bagh", "Naraina",
     "Rajouri Garden", "Tilak Nagar", "Janakpuri", "Uttam Nagar", "Dwarka Mor",
     "Najafgarh"],
    ["Connaught Place", "India Gate", "AIIMS", "Green Park", "Hauz Khas",
     "Malviya Nagar", "Saket"],
    ["Anand Vihar ISBT", "Preet Vihar", "Laxmi Nagar", "ITO", "Connaught Place",
     "Karol Bagh", "Punjabi Bagh", "Pitampura", "Rohini Sector 18"],
    ["Dilshad Garden", "Vivek Vihar", "Shahdara", "Welcome", "Seelampur",
     "Yamuna Vihar", "Wazirabad", "Civil Lines", "Azadpur"],
    ["Mayur Vihar", "Laxmi Nagar", "Nizamuddin", "Moolchand", "Defence Colony",
     "Lajpat Nagar", "Nehru Place", "Kalkaji", "Chirag Delhi", "Malviya Nagar"],
    ["Dwarka Sector 21", "Vasant Kunj", "Munirka", "RK Puram", "AIIMS",
     "Green Park", "Nehru Place"],
    ["Vikas Puri", "Janakpuri", "Rajouri Garden", "Punjabi Bagh", "Azadpur",
     "Model Town", "Mukherjee Nagar", "GTB Nagar"],
    ["Najafgarh", "Uttam Nagar", "Tilak Nagar", "Naraina", "AIIMS", "Lajpat Nagar",
     "Ashram", "Sarai Kale Khan ISBT", "Anand Vihar ISBT"],
]


@dataclass(frozen=True)
class Stop:
    stop_id: str
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Route:
    route_id: str
    short_name: str
    long_name: str
    stops: list[Stop]

    @property
    def length_km(self) -> float:
        return sum(
            haversine_km(a.lat, a.lon, b.lat, b.lon)
            for a, b in zip(self.stops, self.stops[1:], strict=False)
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance. Real coordinates mean these are real distances."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _interpolate(a: Stop, b: Stop, spacing_km: float, seq: int) -> list[Stop]:
    """Insert intermediate stops between two named places.

    Real Delhi routes stop far more often than the named landmarks alone. These
    intermediate stops are synthetic and named for the segment they sit on, so
    they are never mistaken for real named places.
    """
    distance = haversine_km(a.lat, a.lon, b.lat, b.lon)
    count = max(0, int(distance / spacing_km) - 1)
    out: list[Stop] = []
    for i in range(1, count + 1):
        f = i / (count + 1)
        out.append(
            Stop(
                stop_id=f"DLS{seq:05d}{i:02d}",
                name=f"{a.name} - {b.name} ({i})",
                lat=round(a.lat + (b.lat - a.lat) * f, 6),
                lon=round(a.lon + (b.lon - a.lon) * f, 6),
            )
        )
    return out


def build(
    route_count: int = 60,
    stop_spacing_km: float = 0.9,
    seed: int = 20260830,
) -> tuple[list[Stop], list[Route]]:
    """Generate the network. Deterministic for a given seed (section 18.1)."""
    rng = random.Random(seed)
    by_name = {name: (lat, lon) for name, lat, lon in DELHI_PLACES}

    named: dict[str, Stop] = {}
    for index, (name, lat, lon) in enumerate(DELHI_PLACES):
        named[name] = Stop(stop_id=f"DLN{index:04d}", name=name, lat=lat, lon=lon)

    routes: list[Route] = []
    all_stops: dict[str, Stop] = dict(named)

    for route_index in range(route_count):
        corridor = CORRIDORS[route_index % len(CORRIDORS)]
        # Vary the segment so routes on one corridor are not identical.
        if len(corridor) > 4:
            start = rng.randint(0, max(0, len(corridor) - 4))
            end = rng.randint(start + 3, len(corridor))
            leg = corridor[start:end]
        else:
            leg = corridor

        stops: list[Stop] = []
        for i, place in enumerate(leg):
            if place not in by_name:
                continue
            current = named[place]
            if stops:
                filler = _interpolate(stops[-1], current, stop_spacing_km, route_index * 100 + i)
                for stop in filler:
                    all_stops[stop.stop_id] = stop
                stops.extend(filler)
            stops.append(current)

        if len(stops) < 5:
            continue

        number = 400 + route_index
        routes.append(
            Route(
                route_id=f"DL{number}",
                short_name=str(number),
                long_name=f"{stops[0].name} to {stops[-1].name}",
                stops=stops,
            )
        )

    log.info(
        "built %d routes over %d stops (%d named Delhi places, %d intermediate)",
        len(routes), len(all_stops), len(named), len(all_stops) - len(named),
    )
    return list(all_stops.values()), routes
