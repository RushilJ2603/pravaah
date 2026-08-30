//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ShiftPositionRequest {
  /// Returns a new [ShiftPositionRequest] instance.
  ShiftPositionRequest({
    required this.lat,
    required this.lon,
    required this.accuracyM,
    this.speedMps,
    required this.timestamp,
  });

  /// Minimum value: -90.0
  /// Maximum value: 90.0
  num lat;

  /// Minimum value: -180.0
  /// Maximum value: 180.0
  num lon;

  /// Minimum value: 0.0
  /// Maximum value: 500.0
  num accuracyM;

  /// Minimum value: 0.0
  num? speedMps;

  DateTime timestamp;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ShiftPositionRequest &&
    other.lat == lat &&
    other.lon == lon &&
    other.accuracyM == accuracyM &&
    other.speedMps == speedMps &&
    other.timestamp == timestamp;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (lat.hashCode) +
    (lon.hashCode) +
    (accuracyM.hashCode) +
    (speedMps == null ? 0 : speedMps!.hashCode) +
    (timestamp.hashCode);

  @override
  String toString() => 'ShiftPositionRequest[lat=$lat, lon=$lon, accuracyM=$accuracyM, speedMps=$speedMps, timestamp=$timestamp]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'lat'] = this.lat;
      json[r'lon'] = this.lon;
      json[r'accuracy_m'] = this.accuracyM;
    if (this.speedMps != null) {
      json[r'speed_mps'] = this.speedMps;
    } else {
      json[r'speed_mps'] = null;
    }
      json[r'timestamp'] = this.timestamp.toUtc().toIso8601String();
    return json;
  }

  /// Returns a new [ShiftPositionRequest] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ShiftPositionRequest? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'lat'), 'Required key "ShiftPositionRequest[lat]" is missing from JSON.');
        assert(json[r'lat'] != null, 'Required key "ShiftPositionRequest[lat]" has a null value in JSON.');
        assert(json.containsKey(r'lon'), 'Required key "ShiftPositionRequest[lon]" is missing from JSON.');
        assert(json[r'lon'] != null, 'Required key "ShiftPositionRequest[lon]" has a null value in JSON.');
        assert(json.containsKey(r'accuracy_m'), 'Required key "ShiftPositionRequest[accuracy_m]" is missing from JSON.');
        assert(json[r'accuracy_m'] != null, 'Required key "ShiftPositionRequest[accuracy_m]" has a null value in JSON.');
        assert(json.containsKey(r'timestamp'), 'Required key "ShiftPositionRequest[timestamp]" is missing from JSON.');
        assert(json[r'timestamp'] != null, 'Required key "ShiftPositionRequest[timestamp]" has a null value in JSON.');
        return true;
      }());

      return ShiftPositionRequest(
        lat: num.parse('${json[r'lat']}'),
        lon: num.parse('${json[r'lon']}'),
        accuracyM: num.parse('${json[r'accuracy_m']}'),
        speedMps: json[r'speed_mps'] == null
            ? null
            : num.parse('${json[r'speed_mps']}'),
        timestamp: mapDateTime(json, r'timestamp', r'')!,
      );
    }
    return null;
  }

  static List<ShiftPositionRequest> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ShiftPositionRequest>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ShiftPositionRequest.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ShiftPositionRequest> mapFromJson(dynamic json) {
    final map = <String, ShiftPositionRequest>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ShiftPositionRequest.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ShiftPositionRequest-objects as value to a dart map
  static Map<String, List<ShiftPositionRequest>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ShiftPositionRequest>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ShiftPositionRequest.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'lat',
    'lon',
    'accuracy_m',
    'timestamp',
  };
}

