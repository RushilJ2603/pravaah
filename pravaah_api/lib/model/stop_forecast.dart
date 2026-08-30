//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class StopForecast {
  /// Returns a new [StopForecast] instance.
  StopForecast({
    required this.stopId,
    required this.stopName,
    required this.stopSequence,
    required this.scheduledArrival,
    required this.crowd,
  });

  String stopId;

  String stopName;

  int stopSequence;

  DateTime scheduledArrival;

  CrowdBand crowd;

  @override
  bool operator ==(Object other) => identical(this, other) || other is StopForecast &&
    other.stopId == stopId &&
    other.stopName == stopName &&
    other.stopSequence == stopSequence &&
    other.scheduledArrival == scheduledArrival &&
    other.crowd == crowd;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (stopId.hashCode) +
    (stopName.hashCode) +
    (stopSequence.hashCode) +
    (scheduledArrival.hashCode) +
    (crowd.hashCode);

  @override
  String toString() => 'StopForecast[stopId=$stopId, stopName=$stopName, stopSequence=$stopSequence, scheduledArrival=$scheduledArrival, crowd=$crowd]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'stop_id'] = this.stopId;
      json[r'stop_name'] = this.stopName;
      json[r'stop_sequence'] = this.stopSequence;
      json[r'scheduled_arrival'] = this.scheduledArrival.toUtc().toIso8601String();
      json[r'crowd'] = this.crowd;
    return json;
  }

  /// Returns a new [StopForecast] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static StopForecast? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'stop_id'), 'Required key "StopForecast[stop_id]" is missing from JSON.');
        assert(json[r'stop_id'] != null, 'Required key "StopForecast[stop_id]" has a null value in JSON.');
        assert(json.containsKey(r'stop_name'), 'Required key "StopForecast[stop_name]" is missing from JSON.');
        assert(json[r'stop_name'] != null, 'Required key "StopForecast[stop_name]" has a null value in JSON.');
        assert(json.containsKey(r'stop_sequence'), 'Required key "StopForecast[stop_sequence]" is missing from JSON.');
        assert(json[r'stop_sequence'] != null, 'Required key "StopForecast[stop_sequence]" has a null value in JSON.');
        assert(json.containsKey(r'scheduled_arrival'), 'Required key "StopForecast[scheduled_arrival]" is missing from JSON.');
        assert(json[r'scheduled_arrival'] != null, 'Required key "StopForecast[scheduled_arrival]" has a null value in JSON.');
        assert(json.containsKey(r'crowd'), 'Required key "StopForecast[crowd]" is missing from JSON.');
        assert(json[r'crowd'] != null, 'Required key "StopForecast[crowd]" has a null value in JSON.');
        return true;
      }());

      return StopForecast(
        stopId: mapValueOfType<String>(json, r'stop_id')!,
        stopName: mapValueOfType<String>(json, r'stop_name')!,
        stopSequence: mapValueOfType<int>(json, r'stop_sequence')!,
        scheduledArrival: mapDateTime(json, r'scheduled_arrival', r'')!,
        crowd: CrowdBand.fromJson(json[r'crowd'])!,
      );
    }
    return null;
  }

  static List<StopForecast> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <StopForecast>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = StopForecast.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, StopForecast> mapFromJson(dynamic json) {
    final map = <String, StopForecast>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = StopForecast.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of StopForecast-objects as value to a dart map
  static Map<String, List<StopForecast>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<StopForecast>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = StopForecast.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'stop_id',
    'stop_name',
    'stop_sequence',
    'scheduled_arrival',
    'crowd',
  };
}

