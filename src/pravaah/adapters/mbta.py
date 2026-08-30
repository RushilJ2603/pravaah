"""MBTA adapter.

SOLUTION.md ADR-08: MBTA is the **development substrate**, not the deployment
target. It is used because Delhi OTD publishes no occupancy at all, and crowd
labels are the entire product. See section 2.4 and section 6.2.

Measured characteristics of this feed (section 6.2.1, sampled over the recorded
corpus) that shape the code here:

    trip_id            100.0%   safe join key
    stop_id             92.3%
    occupancy_status    68.8%   the crowd label
    bearing             80.5%
    speed                9.8%   unusable -- derived instead (section 28.4)

This module is intentionally thin. Everything configurable lives in
`config/cities/mbta.toml`; only genuine MBTA quirks belong here.
"""

from __future__ import annotations

from ..config import CityProfile, load_city
from .gtfs_rt import GTFSRealtimeAdapter


class MBTAAdapter(GTFSRealtimeAdapter):
    """MBTA VehiclePositions, with occupancy carried inline on the same feed.

    MBTA publishes both `occupancy_status` and `occupancy_percentage`, and needs
    no API key, which is what makes it usable as a substrate at all.
    """

    @property
    def source_name(self) -> str:
        # Matches the value the recorder wrote, so replayed corpus rows and live
        # events carry the same provenance and remain comparable.
        return "mbta_cdn"

    def capacity_for(self, route_id: str | None) -> int:
        """Fallback capacity when fleet master data is absent (section 6.1).

        MBTA route_type is not carried on the realtime feed, so this uses the
        route_id convention: the rapid-transit lines are named, numbered routes
        are buses. Replace this with fleet master data when it exists.
        """
        rail_prefixes = ("Red", "Orange", "Blue", "Green", "Mattapan", "CR-")
        if route_id and route_id.startswith(rail_prefixes):
            return self.city.capacity.default_rail_capacity
        return self.city.capacity.default_bus_capacity


def build(city: CityProfile | None = None) -> MBTAAdapter:
    """Construct the adapter for the MBTA profile."""
    return MBTAAdapter(city or load_city("mbta"))
