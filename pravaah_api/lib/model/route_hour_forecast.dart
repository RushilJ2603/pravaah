//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class RouteHourForecast {
  /// Returns a new [RouteHourForecast] instance.
  RouteHourForecast({
    required this.hour,
    required this.crowd,
  });

  int hour;

  CrowdBand crowd;

  @override
  bool operator ==(Object other) => identical(this, other) || other is RouteHourForecast &&
    other.hour == hour &&
    other.crowd == crowd;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (hour.hashCode) +
    (crowd.hashCode);

  @override
  String toString() => 'RouteHourForecast[hour=$hour, crowd=$crowd]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'hour'] = this.hour;
      json[r'crowd'] = this.crowd;
    return json;
  }

  /// Returns a new [RouteHourForecast] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static RouteHourForecast? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'hour'), 'Required key "RouteHourForecast[hour]" is missing from JSON.');
        assert(json[r'hour'] != null, 'Required key "RouteHourForecast[hour]" has a null value in JSON.');
        assert(json.containsKey(r'crowd'), 'Required key "RouteHourForecast[crowd]" is missing from JSON.');
        assert(json[r'crowd'] != null, 'Required key "RouteHourForecast[crowd]" has a null value in JSON.');
        return true;
      }());

      return RouteHourForecast(
        hour: mapValueOfType<int>(json, r'hour')!,
        crowd: CrowdBand.fromJson(json[r'crowd'])!,
      );
    }
    return null;
  }

  static List<RouteHourForecast> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <RouteHourForecast>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = RouteHourForecast.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, RouteHourForecast> mapFromJson(dynamic json) {
    final map = <String, RouteHourForecast>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = RouteHourForecast.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of RouteHourForecast-objects as value to a dart map
  static Map<String, List<RouteHourForecast>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<RouteHourForecast>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = RouteHourForecast.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'hour',
    'crowd',
  };
}

