/// Wire models for the PRAVAAH API (SOLUTION.md sections 29.1-29.5).
///
/// Two rules from the backend contract are enforced here rather than left to
/// each screen:
///
///   * **Unknown is never empty.** A missing occupancy arrives as the string
///     `"UNKNOWN"`, never as null and never as zero. `CrowdLevel.unknown` is a
///     real member, and `ratio` stays null for it so no bar can be drawn.
///   * **A forecast is a band, not a number.** `CrowdBand` has no single-value
///     constructor; p10/p50/p90 always travel together.
library;

/// The GTFS occupancy ladder, plus UNKNOWN.
enum CrowdLevel {
  empty('EMPTY', 'Empty', 0),
  manySeats('MANY_SEATS_AVAILABLE', 'Plenty of seats', 1),
  fewSeats('FEW_SEATS_AVAILABLE', 'A few seats left', 2),
  standing('STANDING_ROOM_ONLY', 'Standing room only', 3),
  crushed('CRUSHED_STANDING_ROOM_ONLY', 'Very crowded', 4),
  full('FULL', 'Full', 5),
  notAccepting('NOT_ACCEPTING_PASSENGERS', 'Not accepting passengers', 5),
  unknown('UNKNOWN', 'Crowding unknown', -1);

  const CrowdLevel(this.wire, this.label, this.rank);

  /// The exact string the API sends.
  final String wire;

  /// Human-readable text. Crowding must never be conveyed by colour alone
  /// (SOLUTION.md section 33.5), so every level carries a label.
  final String label;

  /// Position on the ladder; -1 for unknown, which is deliberately not zero.
  final int rank;

  bool get isKnown => this != CrowdLevel.unknown;

  static CrowdLevel fromWire(String? value) {
    if (value == null) return CrowdLevel.unknown;
    for (final level in CrowdLevel.values) {
      if (level.wire == value) return level;
    }
    // An unrecognised class is unknown, never a guess. The backend enum can
    // grow; rendering a new value as "empty" would be the worst failure mode.
    return CrowdLevel.unknown;
  }
}

/// A crowd prediction as a distribution. Never collapse this to one number.
class CrowdBand {
  const CrowdBand({
    required this.p10,
    required this.p50,
    required this.p90,
    required this.modelVersion,
    required this.isFallback,
    this.p10Onboard,
    this.p50Onboard,
    this.p90Onboard,
    this.ratio,
    this.capacity,
  });

  final CrowdLevel p10;
  final CrowdLevel p50;
  final CrowdLevel p90;
  final int? p10Onboard;
  final int? p50Onboard;
  final int? p90Onboard;
  final double? ratio;
  final int? capacity;
  final String modelVersion;

  /// True when the forecast came from a coarser key than the most specific one.
  /// Section 33.3 rule 5 requires this to be disclosed as "estimated from
  /// history" rather than silently presented as a precise prediction.
  final bool isFallback;

  bool get isKnown => p50.isKnown;

  /// "Standing room only, could be very crowded" — the band in words.
  String get summary {
    if (!isKnown) return CrowdLevel.unknown.label;
    if (p90 != p50) return '${p50.label}, could be ${p90.label.toLowerCase()}';
    return p50.label;
  }

  static CrowdBand fromJson(Map<String, dynamic> json) => CrowdBand(
        p10: CrowdLevel.fromWire(json['p10_class'] as String?),
        p50: CrowdLevel.fromWire(json['p50_class'] as String?),
        p90: CrowdLevel.fromWire(json['p90_class'] as String?),
        p10Onboard: json['p10_onboard'] as int?,
        p50Onboard: json['p50_onboard'] as int?,
        p90Onboard: json['p90_onboard'] as int?,
        ratio: (json['p50_ratio'] as num?)?.toDouble(),
        capacity: json['capacity'] as int?,
        modelVersion: (json['model_version'] as String?) ?? 'unknown',
        isFallback: (json['is_fallback'] as bool?) ?? false,
      );
}

/// One leg of a journey.
class JourneyLeg {
  const JourneyLeg({
    required this.routeId,
    required this.boardStopName,
    required this.alightStopName,
    required this.departure,
    required this.arrival,
    required this.stops,
    required this.crowd,
    this.routeName,
  });

  final String routeId;
  final String? routeName;
  final String boardStopName;
  final String alightStopName;
  final DateTime departure;
  final DateTime arrival;
  final int stops;
  final CrowdBand crowd;

  static JourneyLeg fromJson(Map<String, dynamic> json) => JourneyLeg(
        routeId: json['route_id'] as String,
        routeName: json['route_name'] as String?,
        boardStopName: json['board_stop_name'] as String? ?? 'Origin',
        alightStopName: json['alight_stop_name'] as String? ?? 'Destination',
        departure: DateTime.parse(json['departure'] as String),
        arrival: DateTime.parse(json['arrival'] as String),
        stops: (json['stops'] as num?)?.toInt() ?? 0,
        crowd: CrowdBand.fromJson(
            (json['crowd'] as Map<String, dynamic>?) ?? const {}),
      );
}

/// One ranked itinerary. `reasons` is never empty — an option that cannot
/// explain itself is a contract violation on the backend side.
class JourneyOption {
  const JourneyOption({
    required this.optionId,
    required this.totalMinutes,
    required this.transfers,
    required this.departure,
    required this.arrival,
    required this.legs,
    required this.reasons,
    required this.isRecommended,
  });

  final String optionId;
  final int totalMinutes;
  final int transfers;
  final DateTime departure;
  final DateTime arrival;
  final List<JourneyLeg> legs;
  final List<String> reasons;
  final bool isRecommended;

  CrowdBand? get boardingCrowd => legs.isEmpty ? null : legs.first.crowd;

  String get routeLabel =>
      legs.isEmpty ? 'Journey' : 'Route ${legs.first.routeId}';

  static JourneyOption fromJson(Map<String, dynamic> json) => JourneyOption(
        optionId: json['option_id'] as String? ?? '',
        totalMinutes: (json['total_minutes'] as num?)?.toInt() ?? 0,
        transfers: (json['transfers'] as num?)?.toInt() ?? 0,
        departure: DateTime.parse(json['departure'] as String),
        arrival: DateTime.parse(json['arrival'] as String),
        legs: ((json['legs'] as List?) ?? const [])
            .map((l) => JourneyLeg.fromJson(l as Map<String, dynamic>))
            .toList(),
        reasons: ((json['reasons'] as List?) ?? const [])
            .map((r) => r.toString())
            .toList(),
        isRecommended: (json['is_recommended'] as bool?) ?? false,
      );
}

class PlanResponse {
  const PlanResponse({
    required this.generatedAt,
    required this.cityId,
    required this.profile,
    required this.options,
  });

  final DateTime generatedAt;
  final String cityId;
  final String profile;
  final List<JourneyOption> options;

  static PlanResponse fromJson(Map<String, dynamic> json) => PlanResponse(
        generatedAt: DateTime.parse(json['generated_at'] as String),
        cityId: json['city_id'] as String? ?? 'unknown',
        profile: json['profile'] as String? ?? 'balanced',
        options: ((json['options'] as List?) ?? const [])
            .map((o) => JourneyOption.fromJson(o as Map<String, dynamic>))
            .toList(),
      );
}

/// Predicted crowding when a vehicle reaches one upcoming stop. This is the
/// product's core claim, so it gets a first-class model.
class StopForecast {
  const StopForecast({
    required this.stopId,
    required this.stopName,
    required this.stopSequence,
    required this.scheduledArrival,
    required this.crowd,
  });

  final String stopId;
  final String stopName;
  final int stopSequence;
  final DateTime scheduledArrival;
  final CrowdBand crowd;

  static StopForecast fromJson(Map<String, dynamic> json) => StopForecast(
        stopId: json['stop_id'] as String,
        stopName: json['stop_name'] as String? ?? 'Stop',
        stopSequence: (json['stop_sequence'] as num?)?.toInt() ?? 0,
        scheduledArrival: DateTime.parse(json['scheduled_arrival'] as String),
        crowd: CrowdBand.fromJson(
            (json['crowd'] as Map<String, dynamic>?) ?? const {}),
      );
}

class TripForecast {
  const TripForecast({
    required this.tripId,
    required this.modelVersion,
    required this.stops,
    this.routeId,
  });

  final String tripId;
  final String? routeId;
  final String modelVersion;
  final List<StopForecast> stops;

  static TripForecast fromJson(Map<String, dynamic> json) => TripForecast(
        tripId: json['trip_id'] as String,
        routeId: json['route_id'] as String?,
        modelVersion: json['model_version'] as String? ?? 'unknown',
        stops: ((json['stops'] as List?) ?? const [])
            .map((s) => StopForecast.fromJson(s as Map<String, dynamic>))
            .toList(),
      );
}

/// Preference profiles the backend accepts for `/v1/plan`.
enum PlanProfile {
  fastest('fastest', 'Fastest'),
  leastCrowded('least_crowded', 'Least crowded'),
  mostReliable('most_reliable', 'Most reliable'),
  balanced('balanced', 'Balanced');

  const PlanProfile(this.wire, this.label);
  final String wire;
  final String label;
}

/// One predicted crowding hotspot from `GET /v1/admin/hotspots`.
class Hotspot {
  const Hotspot({
    required this.stopId,
    required this.stopName,
    required this.routeId,
    required this.predictedAt,
    required this.leadTimeMin,
    required this.servicesInWindow,
    required this.severity,
    required this.crowd,
    required this.reason,
    this.routeShortName,
  });

  final String stopId;
  final String stopName;
  final String routeId;
  final String? routeShortName;
  final DateTime predictedAt;

  /// Minutes of warning. The operator's entire value is lead time -- a hotspot
  /// with none is a report of something already going wrong.
  final int leadTimeMin;
  final int servicesInWindow;
  final int severity;
  final CrowdBand crowd;
  final String reason;

  static Hotspot fromJson(Map<String, dynamic> json) => Hotspot(
        stopId: json['stop_id'] as String,
        stopName: json['stop_name'] as String? ?? 'Stop',
        routeId: json['route_id'] as String,
        routeShortName: json['route_short_name'] as String?,
        predictedAt: DateTime.parse(json['predicted_at'] as String),
        leadTimeMin: (json['lead_time_min'] as num?)?.toInt() ?? 0,
        servicesInWindow: (json['services_in_window'] as num?)?.toInt() ?? 0,
        severity: (json['severity'] as num?)?.toInt() ?? 0,
        crowd: CrowdBand.fromJson(
            (json['crowd'] as Map<String, dynamic>?) ?? const {}),
        reason: json['reason'] as String? ?? '',
      );
}

class HotspotsResponse {
  const HotspotsResponse({
    required this.horizonMin,
    required this.modelVersion,
    required this.hotspots,
  });

  final int horizonMin;
  final String modelVersion;
  final List<Hotspot> hotspots;

  static HotspotsResponse fromJson(Map<String, dynamic> json) => HotspotsResponse(
        horizonMin: (json['horizon_min'] as num?)?.toInt() ?? 60,
        modelVersion: json['model_version'] as String? ?? 'unknown',
        hotspots: ((json['hotspots'] as List?) ?? const [])
            .map((h) => Hotspot.fromJson(h as Map<String, dynamic>))
            .toList(),
      );
}

/// `GET /v1/admin/data-health`. Occupancy coverage is the field worth watching:
/// a silent drop means the map keeps moving while the crowd layer goes blank.
class DataHealth {
  const DataHealth({
    required this.database,
    required this.redis,
    required this.vehiclesTracked,
    required this.vehiclesStale,
    required this.vehiclesWithOccupancy,
    required this.occupancyCoverage,
    required this.oldestPositionAgeS,
    required this.sourceTypes,
    this.feedVersionId,
    this.forecastModel,
  });

  final bool database;
  final bool redis;
  final int vehiclesTracked;
  final int vehiclesStale;
  final int vehiclesWithOccupancy;
  final double occupancyCoverage;
  final int oldestPositionAgeS;
  final Map<String, int> sourceTypes;
  final int? feedVersionId;
  final String? forecastModel;

  bool get isHealthy => database && redis && vehiclesTracked > 0;

  static DataHealth fromJson(Map<String, dynamic> json) => DataHealth(
        database: (json['database'] as bool?) ?? false,
        redis: (json['redis'] as bool?) ?? false,
        vehiclesTracked: (json['vehicles_tracked'] as num?)?.toInt() ?? 0,
        vehiclesStale: (json['vehicles_stale'] as num?)?.toInt() ?? 0,
        vehiclesWithOccupancy:
            (json['vehicles_with_occupancy'] as num?)?.toInt() ?? 0,
        occupancyCoverage:
            (json['occupancy_coverage'] as num?)?.toDouble() ?? 0.0,
        oldestPositionAgeS:
            (json['oldest_position_age_s'] as num?)?.toInt() ?? 0,
        sourceTypes: ((json['source_types'] as Map?) ?? const {})
            .map((k, v) => MapEntry(k.toString(), (v as num).toInt())),
        feedVersionId: (json['feed_version_id'] as num?)?.toInt(),
        forecastModel: json['forecast_model'] as String?,
      );
}

/// One hour of a route's predicted load, from `/v1/admin/routes/{id}/forecast`.
class RouteHourForecast {
  const RouteHourForecast({required this.hour, required this.crowd});
  final int hour;
  final CrowdBand crowd;

  static RouteHourForecast fromJson(Map<String, dynamic> json) =>
      RouteHourForecast(
        hour: (json['hour'] as num).toInt(),
        crowd: CrowdBand.fromJson(
            (json['crowd'] as Map<String, dynamic>?) ?? const {}),
      );
}

/// An active conductor shift. The shift is what binds a phone to a vehicle;
/// without one the backend rejects every position report.
class Shift {
  const Shift({
    required this.shiftId,
    required this.startedAt,
    required this.vehicleId,
    this.routeId,
  });

  final int shiftId;
  final DateTime startedAt;
  final String vehicleId;
  final String? routeId;

  static Shift fromJson(Map<String, dynamic> json, String vehicleId, String? routeId) =>
      Shift(
        shiftId: (json['shift_id'] as num).toInt(),
        startedAt: DateTime.parse(json['started_at'] as String),
        vehicleId: vehicleId,
        routeId: routeId,
      );
}

/// One point on a trip's path.
class StopPoint {
  const StopPoint({
    required this.stopId,
    required this.name,
    required this.lat,
    required this.lon,
    required this.stopSequence,
    this.scheduledArrival,
  });

  final String stopId;
  final String name;
  final double lat;
  final double lon;
  final int stopSequence;
  final DateTime? scheduledArrival;

  static StopPoint fromJson(Map<String, dynamic> json) => StopPoint(
        stopId: json['stop_id'] as String,
        name: json['name'] as String? ?? 'Stop',
        lat: (json['lat'] as num).toDouble(),
        lon: (json['lon'] as num).toDouble(),
        stopSequence: (json['stop_sequence'] as num?)?.toInt() ?? 0,
        scheduledArrival: json['scheduled_arrival'] == null
            ? null
            : DateTime.parse(json['scheduled_arrival'] as String),
      );
}

/// `GET /v1/trips/{tripId}` -- where a bus came from, where it is going, and
/// the path between. The path is the ordered stop coordinates; the network
/// carries no separate shape geometry, so drawing anything smoother would put
/// a line where no bus actually goes.
class TripDetail {
  const TripDetail({
    required this.tripId,
    required this.origin,
    required this.destination,
    required this.stops,
    this.routeId,
    this.routeName,
    this.directionId,
  });

  final String tripId;
  final String? routeId;
  final String? routeName;
  final int? directionId;
  final StopPoint origin;
  final StopPoint destination;
  final List<StopPoint> stops;

  static TripDetail fromJson(Map<String, dynamic> json) => TripDetail(
        tripId: json['trip_id'] as String,
        routeId: json['route_id'] as String?,
        routeName: json['route_name'] as String?,
        directionId: (json['direction_id'] as num?)?.toInt(),
        origin: StopPoint.fromJson(json['origin'] as Map<String, dynamic>),
        destination: StopPoint.fromJson(json['destination'] as Map<String, dynamic>),
        stops: ((json['stops'] as List?) ?? const [])
            .map((s) => StopPoint.fromJson(s as Map<String, dynamic>))
            .toList(),
      );
}
