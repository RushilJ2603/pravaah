/// Live vehicle state from `GET /v1/vehicles`.
///
/// `tripId`, `routeId`, `bearing` and `currentStatus` are nullable because the
/// API declares them so. They happen to be populated by the Delhi simulator,
/// but a real feed omits them routinely -- a vehicle between assignments has no
/// trip -- and casting them non-null crashed the parse for the entire list.
class Vehicle {
  final String vehicleId;
  final String? tripId;
  final String? routeId;
  final int? directionId;
  final double lat;
  final double lon;
  final double? bearing;
  final double? speedMps;
  final String? stopId;
  final String? currentStatus;
  final String occupancyClass;
  final double? occupancyRatio;
  final DateTime ts;
  final int ageS;
  final bool isStale;
  final String sourceType;
  final double qualityScore;

  Vehicle({
    required this.vehicleId,
    this.tripId,
    this.routeId,
    this.directionId,
    required this.lat,
    required this.lon,
    this.bearing,
    this.speedMps,
    this.stopId,
    this.currentStatus,
    required this.occupancyClass,
    this.occupancyRatio,
    required this.ts,
    required this.ageS,
    required this.isStale,
    required this.sourceType,
    required this.qualityScore,
  });

  factory Vehicle.fromJson(Map<String, dynamic> json) {
    return Vehicle(
      vehicleId: json['vehicle_id'] as String,
      tripId: json['trip_id'] as String?,
      routeId: json['route_id'] as String?,
      directionId: json['direction_id'] as int?,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      bearing: (json['bearing'] as num?)?.toDouble(),
      speedMps: (json['speed_mps'] as num?)?.toDouble(),
      stopId: json['stop_id'] as String?,
      currentStatus: json['current_status'] as String?,
      occupancyClass: json['occupancy_class'] as String? ?? 'UNKNOWN',
      occupancyRatio: (json['occupancy_ratio'] as num?)?.toDouble(),
      ts: DateTime.parse(json['ts'] as String),
      ageS: json['age_s'] as int,
      isStale: json['is_stale'] as bool,
      sourceType: json['source_type'] as String,
      qualityScore: (json['quality_score'] as num).toDouble(),
    );
  }
}

class VehiclesResponse {
  final DateTime generatedAt;
  final String cityId;
  final int count;
  final List<Vehicle> vehicles;

  VehiclesResponse({
    required this.generatedAt,
    required this.cityId,
    required this.count,
    required this.vehicles,
  });

  factory VehiclesResponse.fromJson(Map<String, dynamic> json) {
    return VehiclesResponse(
      generatedAt: DateTime.parse(json['generated_at'] as String),
      cityId: json['city_id'] as String,
      count: json['count'] as int,
      vehicles: (json['vehicles'] as List)
          .map((v) => Vehicle.fromJson(v as Map<String, dynamic>))
          .toList(),
    );
  }
}
