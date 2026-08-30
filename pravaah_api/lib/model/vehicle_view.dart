//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class VehicleView {
  /// Returns a new [VehicleView] instance.
  VehicleView({
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
    this.occupancyClass = OccupancyClass.UNKNOWN,
    this.occupancyRatio,
    required this.ts,
    required this.ageS,
    required this.isStale,
    required this.sourceType,
    required this.qualityScore,
  });

  String vehicleId;

  String? tripId;

  String? routeId;

  int? directionId;

  num lat;

  num lon;

  num? bearing;

  num? speedMps;

  String? stopId;

  VehicleStopStatus? currentStatus;

  OccupancyClass occupancyClass;

  num? occupancyRatio;

  DateTime ts;

  /// Minimum value: 0
  int ageS;

  bool isStale;

  SourceType sourceType;

  /// Minimum value: 0.0
  /// Maximum value: 1.0
  num qualityScore;

  @override
  bool operator ==(Object other) => identical(this, other) || other is VehicleView &&
    other.vehicleId == vehicleId &&
    other.tripId == tripId &&
    other.routeId == routeId &&
    other.directionId == directionId &&
    other.lat == lat &&
    other.lon == lon &&
    other.bearing == bearing &&
    other.speedMps == speedMps &&
    other.stopId == stopId &&
    other.currentStatus == currentStatus &&
    other.occupancyClass == occupancyClass &&
    other.occupancyRatio == occupancyRatio &&
    other.ts == ts &&
    other.ageS == ageS &&
    other.isStale == isStale &&
    other.sourceType == sourceType &&
    other.qualityScore == qualityScore;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (vehicleId.hashCode) +
    (tripId == null ? 0 : tripId!.hashCode) +
    (routeId == null ? 0 : routeId!.hashCode) +
    (directionId == null ? 0 : directionId!.hashCode) +
    (lat.hashCode) +
    (lon.hashCode) +
    (bearing == null ? 0 : bearing!.hashCode) +
    (speedMps == null ? 0 : speedMps!.hashCode) +
    (stopId == null ? 0 : stopId!.hashCode) +
    (currentStatus == null ? 0 : currentStatus!.hashCode) +
    (occupancyClass.hashCode) +
    (occupancyRatio == null ? 0 : occupancyRatio!.hashCode) +
    (ts.hashCode) +
    (ageS.hashCode) +
    (isStale.hashCode) +
    (sourceType.hashCode) +
    (qualityScore.hashCode);

  @override
  String toString() => 'VehicleView[vehicleId=$vehicleId, tripId=$tripId, routeId=$routeId, directionId=$directionId, lat=$lat, lon=$lon, bearing=$bearing, speedMps=$speedMps, stopId=$stopId, currentStatus=$currentStatus, occupancyClass=$occupancyClass, occupancyRatio=$occupancyRatio, ts=$ts, ageS=$ageS, isStale=$isStale, sourceType=$sourceType, qualityScore=$qualityScore]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'vehicle_id'] = this.vehicleId;
    if (this.tripId != null) {
      json[r'trip_id'] = this.tripId;
    } else {
      json[r'trip_id'] = null;
    }
    if (this.routeId != null) {
      json[r'route_id'] = this.routeId;
    } else {
      json[r'route_id'] = null;
    }
    if (this.directionId != null) {
      json[r'direction_id'] = this.directionId;
    } else {
      json[r'direction_id'] = null;
    }
      json[r'lat'] = this.lat;
      json[r'lon'] = this.lon;
    if (this.bearing != null) {
      json[r'bearing'] = this.bearing;
    } else {
      json[r'bearing'] = null;
    }
    if (this.speedMps != null) {
      json[r'speed_mps'] = this.speedMps;
    } else {
      json[r'speed_mps'] = null;
    }
    if (this.stopId != null) {
      json[r'stop_id'] = this.stopId;
    } else {
      json[r'stop_id'] = null;
    }
    if (this.currentStatus != null) {
      json[r'current_status'] = this.currentStatus;
    } else {
      json[r'current_status'] = null;
    }
      json[r'occupancy_class'] = this.occupancyClass;
    if (this.occupancyRatio != null) {
      json[r'occupancy_ratio'] = this.occupancyRatio;
    } else {
      json[r'occupancy_ratio'] = null;
    }
      json[r'ts'] = this.ts.toUtc().toIso8601String();
      json[r'age_s'] = this.ageS;
      json[r'is_stale'] = this.isStale;
      json[r'source_type'] = this.sourceType;
      json[r'quality_score'] = this.qualityScore;
    return json;
  }

  /// Returns a new [VehicleView] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static VehicleView? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'vehicle_id'), 'Required key "VehicleView[vehicle_id]" is missing from JSON.');
        assert(json[r'vehicle_id'] != null, 'Required key "VehicleView[vehicle_id]" has a null value in JSON.');
        assert(json.containsKey(r'lat'), 'Required key "VehicleView[lat]" is missing from JSON.');
        assert(json[r'lat'] != null, 'Required key "VehicleView[lat]" has a null value in JSON.');
        assert(json.containsKey(r'lon'), 'Required key "VehicleView[lon]" is missing from JSON.');
        assert(json[r'lon'] != null, 'Required key "VehicleView[lon]" has a null value in JSON.');
        assert(json.containsKey(r'ts'), 'Required key "VehicleView[ts]" is missing from JSON.');
        assert(json[r'ts'] != null, 'Required key "VehicleView[ts]" has a null value in JSON.');
        assert(json.containsKey(r'age_s'), 'Required key "VehicleView[age_s]" is missing from JSON.');
        assert(json[r'age_s'] != null, 'Required key "VehicleView[age_s]" has a null value in JSON.');
        assert(json.containsKey(r'is_stale'), 'Required key "VehicleView[is_stale]" is missing from JSON.');
        assert(json[r'is_stale'] != null, 'Required key "VehicleView[is_stale]" has a null value in JSON.');
        assert(json.containsKey(r'source_type'), 'Required key "VehicleView[source_type]" is missing from JSON.');
        assert(json[r'source_type'] != null, 'Required key "VehicleView[source_type]" has a null value in JSON.');
        assert(json.containsKey(r'quality_score'), 'Required key "VehicleView[quality_score]" is missing from JSON.');
        assert(json[r'quality_score'] != null, 'Required key "VehicleView[quality_score]" has a null value in JSON.');
        return true;
      }());

      return VehicleView(
        vehicleId: mapValueOfType<String>(json, r'vehicle_id')!,
        tripId: mapValueOfType<String>(json, r'trip_id'),
        routeId: mapValueOfType<String>(json, r'route_id'),
        directionId: mapValueOfType<int>(json, r'direction_id'),
        lat: num.parse('${json[r'lat']}'),
        lon: num.parse('${json[r'lon']}'),
        bearing: json[r'bearing'] == null
            ? null
            : num.parse('${json[r'bearing']}'),
        speedMps: json[r'speed_mps'] == null
            ? null
            : num.parse('${json[r'speed_mps']}'),
        stopId: mapValueOfType<String>(json, r'stop_id'),
        currentStatus: VehicleStopStatus.fromJson(json[r'current_status']),
        occupancyClass: OccupancyClass.fromJson(json[r'occupancy_class']) ?? OccupancyClass.UNKNOWN,
        occupancyRatio: json[r'occupancy_ratio'] == null
            ? null
            : num.parse('${json[r'occupancy_ratio']}'),
        ts: mapDateTime(json, r'ts', r'')!,
        ageS: mapValueOfType<int>(json, r'age_s')!,
        isStale: mapValueOfType<bool>(json, r'is_stale')!,
        sourceType: SourceType.fromJson(json[r'source_type'])!,
        qualityScore: num.parse('${json[r'quality_score']}'),
      );
    }
    return null;
  }

  static List<VehicleView> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <VehicleView>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = VehicleView.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, VehicleView> mapFromJson(dynamic json) {
    final map = <String, VehicleView>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = VehicleView.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of VehicleView-objects as value to a dart map
  static Map<String, List<VehicleView>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<VehicleView>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = VehicleView.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'vehicle_id',
    'lat',
    'lon',
    'ts',
    'age_s',
    'is_stale',
    'source_type',
    'quality_score',
  };
}

