# -*- coding: utf-8 -*-
"""
Records live GTFS-Realtime vehicle positions + occupancy to CSV.

No API key required. Run it and leave it running - every hour of recording
is real training data (position, delay, and REAL operator occupancy labels).

    python record_feed.py                # records MBTA, 20s interval
    python record_feed.py --interval 15
"""
import argparse, csv, os, time, datetime, urllib.request, traceback

from google.transit import gtfs_realtime_pb2 as rt

FEEDS = {
    # agency: (vehicle_positions_url, trip_updates_url)
    "mbta": ("https://cdn.mbta.com/realtime/VehiclePositions.pb",
             "https://cdn.mbta.com/realtime/TripUpdates.pb"),
}

VP_COLS = ["ingest_ts", "feed_ts", "agency", "vehicle_id", "trip_id", "route_id",
           "direction_id", "lat", "lon", "bearing", "speed", "stop_id",
           "current_stop_sequence", "current_status", "occupancy_status",
           "occupancy_pct", "vehicle_ts", "source_type"]

TU_COLS = ["ingest_ts", "agency", "trip_id", "route_id", "stop_id",
           "stop_sequence", "arrival_time", "arrival_delay",
           "departure_time", "departure_delay", "schedule_relationship"]


def _writer(path, cols):
    new = not os.path.exists(path)
    fh = open(path, "a", newline="", encoding="utf-8")
    w = csv.writer(fh)
    if new:
        w.writerow(cols)
    return fh, w


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sih-transit-recorder/1.0"})
    return urllib.request.urlopen(req, timeout=30).read()


def poll_vehicles(agency, url, w, raw_dir):
    raw = fetch(url)
    msg = rt.FeedMessage()
    msg.ParseFromString(raw)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    feed_ts = msg.header.timestamp

    if raw_dir:                                   # keep raw .pb for exact replay
        stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        with open(os.path.join(raw_dir, f"{agency}_vp_{stamp}.pb"), "wb") as fh:
            fh.write(raw)

    n = 0
    for e in msg.entity:
        if not e.HasField("vehicle"):
            continue
        v = e.vehicle
        occ = v.OccupancyStatus.Name(v.occupancy_status) if v.HasField("occupancy_status") else ""
        w.writerow([
            now, feed_ts, agency,
            v.vehicle.id, v.trip.trip_id, v.trip.route_id,
            v.trip.direction_id if v.trip.HasField("direction_id") else "",
            round(v.position.latitude, 6), round(v.position.longitude, 6),
            round(v.position.bearing, 1) if v.position.HasField("bearing") else "",
            round(v.position.speed, 2) if v.position.HasField("speed") else "",
            v.stop_id, v.current_stop_sequence,
            v.VehicleStopStatus.Name(v.current_status) if v.HasField("current_status") else "",
            occ,
            v.occupancy_percentage if v.HasField("occupancy_percentage") else "",
            v.timestamp, "PUBLIC_FEED",
        ])
        n += 1
    return n


def poll_trips(agency, url, w):
    raw = fetch(url)
    msg = rt.FeedMessage()
    msg.ParseFromString(raw)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    n = 0
    for e in msg.entity:
        if not e.HasField("trip_update"):
            continue
        tu = e.trip_update
        for stu in tu.stop_time_update:
            w.writerow([
                now, agency, tu.trip.trip_id, tu.trip.route_id, stu.stop_id,
                stu.stop_sequence,
                stu.arrival.time if stu.HasField("arrival") else "",
                stu.arrival.delay if stu.HasField("arrival") else "",
                stu.departure.time if stu.HasField("departure") else "",
                stu.departure.delay if stu.HasField("departure") else "",
                stu.ScheduleRelationship.Name(stu.schedule_relationship),
            ])
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agency", default="mbta", choices=list(FEEDS))
    ap.add_argument("--interval", type=int, default=20, help="seconds between polls")
    ap.add_argument("--outdir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--keep-raw", action="store_true", help="also archive raw .pb frames")
    ap.add_argument("--no-trips", action="store_true", help="skip TripUpdates polling")
    ap.add_argument("--trip-every", type=int, default=15,
                    help="poll TripUpdates only every Nth cycle (it is ~26k rows a poll)")
    a = ap.parse_args()

    vp_url, tu_url = FEEDS[a.agency]
    os.makedirs(a.outdir, exist_ok=True)
    raw_dir = os.path.join(a.outdir, "raw") if a.keep_raw else None
    if raw_dir:
        os.makedirs(raw_dir, exist_ok=True)

    vp_fh, vp_w = _writer(os.path.join(a.outdir, f"{a.agency}_vehicle_positions.csv"), VP_COLS)
    tu_fh, tu_w = (None, None)
    if not a.no_trips:
        tu_fh, tu_w = _writer(os.path.join(a.outdir, f"{a.agency}_trip_updates.csv"), TU_COLS)

    print(f"recording {a.agency} every {a.interval}s -> {a.outdir}")
    print("leave this running; Ctrl+C to stop\n")
    polls = tot_v = tot_t = 0
    try:
        while True:
            t0 = time.time()
            polls += 1
            try:
                nv = poll_vehicles(a.agency, vp_url, vp_w, raw_dir)
                vp_fh.flush()
                tot_v += nv
                nt = 0
                if tu_w is not None and polls % a.trip_every == 0:
                    nt = poll_trips(a.agency, tu_url, tu_w)
                    tu_fh.flush()
                    tot_t += nt
                print(f"[{datetime.datetime.now():%H:%M:%S}] poll {polls:5d}  "
                      f"vehicles {nv:4d} (total {tot_v:,})  stop-updates {nt:5d} "
                      f"(total {tot_t:,})", flush=True)
            except Exception:
                print(f"[{datetime.datetime.now():%H:%M:%S}] poll failed, retrying",
                      flush=True)
                traceback.print_exc()
            time.sleep(max(1.0, a.interval - (time.time() - t0)))
    except KeyboardInterrupt:
        print(f"\nstopped after {polls} polls: {tot_v:,} vehicle rows, {tot_t:,} stop updates")
    finally:
        vp_fh.close()
        if tu_fh:
            tu_fh.close()


if __name__ == "__main__":
    main()
