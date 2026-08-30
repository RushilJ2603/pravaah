//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class OccupancyReportRequest {
  /// Returns a new [OccupancyReportRequest] instance.
  OccupancyReportRequest({
    this.tripId,
    required this.vehicleId,
    required this.occupancyClass,
    required this.reportedAt,
  });

  String? tripId;

  String vehicleId;

  OccupancyClass occupancyClass;

  DateTime reportedAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is OccupancyReportRequest &&
    other.tripId == tripId &&
    other.vehicleId == vehicleId &&
    other.occupancyClass == occupancyClass &&
    other.reportedAt == reportedAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (tripId == null ? 0 : tripId!.hashCode) +
    (vehicleId.hashCode) +
    (occupancyClass.hashCode) +
    (reportedAt.hashCode);

  @override
  String toString() => 'OccupancyReportRequest[tripId=$tripId, vehicleId=$vehicleId, occupancyClass=$occupancyClass, reportedAt=$reportedAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
    if (this.tripId != null) {
      json[r'trip_id'] = this.tripId;
    } else {
      json[r'trip_id'] = null;
    }
      json[r'vehicle_id'] = this.vehicleId;
      json[r'occupancy_class'] = this.occupancyClass;
      json[r'reported_at'] = this.reportedAt.toUtc().toIso8601String();
    return json;
  }

  /// Returns a new [OccupancyReportRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static OccupancyReportRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'vehicle_id'), 'Required key "OccupancyReportRequest[vehicle_id]" is missing from JSON.');
        assert(json[r'vehicle_id'] != null, 'Required key "OccupancyReportRequest[vehicle_id]" has a null value in JSON.');
        assert(json.containsKey(r'occupancy_class'), 'Required key "OccupancyReportRequest[occupancy_class]" is missing from JSON.');
        assert(json[r'occupancy_class'] != null, 'Required key "OccupancyReportRequest[occupancy_class]" has a null value in JSON.');
        assert(json.containsKey(r'reported_at'), 'Required key "OccupancyReportRequest[reported_at]" is missing from JSON.');
        assert(json[r'reported_at'] != null, 'Required key "OccupancyReportRequest[reported_at]" has a null value in JSON.');
        return true;
      }());

      return OccupancyReportRequest(
        tripId: mapValueOfType<String>(json, r'trip_id'),
        vehicleId: mapValueOfType<String>(json, r'vehicle_id')!,
        occupancyClass: OccupancyClass.fromJson(json[r'occupancy_class'])!,
        reportedAt: mapDateTime(json, r'reported_at', r'')!,
      );
    }
    return null;
  }

  static List<OccupancyReportRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <OccupancyReportRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = OccupancyReportRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, OccupancyReportRequest> mapFromJson(dynamic json) {
    final map = <String, OccupancyReportRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = OccupancyReportRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of OccupancyReportRequest-objects as value to a dart map
  static Map<String, List<OccupancyReportRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<OccupancyReportRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = OccupancyReportRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'vehicle_id',
    'occupancy_class',
    'reported_at',
  };
}

