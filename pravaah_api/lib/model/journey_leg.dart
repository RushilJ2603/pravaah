//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class JourneyLeg {
  /// Returns a new [JourneyLeg] instance.
  JourneyLeg({
    required this.routeId,
    required this.routeName,
    required this.boardStopId,
    required this.boardStopName,
    required this.alightStopId,
    required this.alightStopName,
    required this.departure,
    required this.arrival,
    required this.stops,
    required this.crowd,
  });

  String routeId;

  String? routeName;

  String boardStopId;

  String boardStopName;

  String alightStopId;

  String alightStopName;

  DateTime departure;

  DateTime arrival;

  int stops;

  CrowdBand crowd;

  @override
  bool operator ==(Object other) => identical(this, other) || other is JourneyLeg &&
    other.routeId == routeId &&
    other.routeName == routeName &&
    other.boardStopId == boardStopId &&
    other.boardStopName == boardStopName &&
    other.alightStopId == alightStopId &&
    other.alightStopName == alightStopName &&
    other.departure == departure &&
    other.arrival == arrival &&
    other.stops == stops &&
    other.crowd == crowd;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (routeId.hashCode) +
    (routeName == null ? 0 : routeName!.hashCode) +
    (boardStopId.hashCode) +
    (boardStopName.hashCode) +
    (alightStopId.hashCode) +
    (alightStopName.hashCode) +
    (departure.hashCode) +
    (arrival.hashCode) +
    (stops.hashCode) +
    (crowd.hashCode);

  @override
  String toString() => 'JourneyLeg[routeId=$routeId, routeName=$routeName, boardStopId=$boardStopId, boardStopName=$boardStopName, alightStopId=$alightStopId, alightStopName=$alightStopName, departure=$departure, arrival=$arrival, stops=$stops, crowd=$crowd]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'route_id'] = this.routeId;
    if (this.routeName != null) {
      json[r'route_name'] = this.routeName;
    } else {
      json[r'route_name'] = null;
    }
      json[r'board_stop_id'] = this.boardStopId;
      json[r'board_stop_name'] = this.boardStopName;
      json[r'alight_stop_id'] = this.alightStopId;
      json[r'alight_stop_name'] = this.alightStopName;
      json[r'departure'] = this.departure.toUtc().toIso8601String();
      json[r'arrival'] = this.arrival.toUtc().toIso8601String();
      json[r'stops'] = this.stops;
      json[r'crowd'] = this.crowd;
    return json;
  }

  /// Returns a new [JourneyLeg] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static JourneyLeg? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'route_id'), 'Required key "JourneyLeg[route_id]" is missing from JSON.');
        assert(json[r'route_id'] != null, 'Required key "JourneyLeg[route_id]" has a null value in JSON.');
        assert(json.containsKey(r'route_name'), 'Required key "JourneyLeg[route_name]" is missing from JSON.');
        assert(json.containsKey(r'board_stop_id'), 'Required key "JourneyLeg[board_stop_id]" is missing from JSON.');
        assert(json[r'board_stop_id'] != null, 'Required key "JourneyLeg[board_stop_id]" has a null value in JSON.');
        assert(json.containsKey(r'board_stop_name'), 'Required key "JourneyLeg[board_stop_name]" is missing from JSON.');
        assert(json[r'board_stop_name'] != null, 'Required key "JourneyLeg[board_stop_name]" has a null value in JSON.');
        assert(json.containsKey(r'alight_stop_id'), 'Required key "JourneyLeg[alight_stop_id]" is missing from JSON.');
        assert(json[r'alight_stop_id'] != null, 'Required key "JourneyLeg[alight_stop_id]" has a null value in JSON.');
        assert(json.containsKey(r'alight_stop_name'), 'Required key "JourneyLeg[alight_stop_name]" is missing from JSON.');
        assert(json[r'alight_stop_name'] != null, 'Required key "JourneyLeg[alight_stop_name]" has a null value in JSON.');
        assert(json.containsKey(r'departure'), 'Required key "JourneyLeg[departure]" is missing from JSON.');
        assert(json[r'departure'] != null, 'Required key "JourneyLeg[departure]" has a null value in JSON.');
        assert(json.containsKey(r'arrival'), 'Required key "JourneyLeg[arrival]" is missing from JSON.');
        assert(json[r'arrival'] != null, 'Required key "JourneyLeg[arrival]" has a null value in JSON.');
        assert(json.containsKey(r'stops'), 'Required key "JourneyLeg[stops]" is missing from JSON.');
        assert(json[r'stops'] != null, 'Required key "JourneyLeg[stops]" has a null value in JSON.');
        assert(json.containsKey(r'crowd'), 'Required key "JourneyLeg[crowd]" is missing from JSON.');
        assert(json[r'crowd'] != null, 'Required key "JourneyLeg[crowd]" has a null value in JSON.');
        return true;
      }());

      return JourneyLeg(
        routeId: mapValueOfType<String>(json, r'route_id')!,
        routeName: mapValueOfType<String>(json, r'route_name'),
        boardStopId: mapValueOfType<String>(json, r'board_stop_id')!,
        boardStopName: mapValueOfType<String>(json, r'board_stop_name')!,
        alightStopId: mapValueOfType<String>(json, r'alight_stop_id')!,
        alightStopName: mapValueOfType<String>(json, r'alight_stop_name')!,
        departure: mapDateTime(json, r'departure', r'')!,
        arrival: mapDateTime(json, r'arrival', r'')!,
        stops: mapValueOfType<int>(json, r'stops')!,
        crowd: CrowdBand.fromJson(json[r'crowd'])!,
      );
    }
    return null;
  }

  static List<JourneyLeg> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <JourneyLeg>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = JourneyLeg.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, JourneyLeg> mapFromJson(dynamic json) {
    final map = <String, JourneyLeg>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = JourneyLeg.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of JourneyLeg-objects as value to a dart map
  static Map<String, List<JourneyLeg>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<JourneyLeg>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = JourneyLeg.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'route_id',
    'route_name',
    'board_stop_id',
    'board_stop_name',
    'alight_stop_id',
    'alight_stop_name',
    'departure',
    'arrival',
    'stops',
    'crowd',
  };
}

