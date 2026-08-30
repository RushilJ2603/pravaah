//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class RouteForecastResponse {
  /// Returns a new [RouteForecastResponse] instance.
  RouteForecastResponse({
    required this.generatedAt,
    required this.cityId,
    required this.routeId,
    required this.modelVersion,
    this.hours = const [],
  });

  DateTime generatedAt;

  String cityId;

  String routeId;

  String modelVersion;

  List<RouteHourForecast> hours;

  @override
  bool operator ==(Object other) => identical(this, other) || other is RouteForecastResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.routeId == routeId &&
    other.modelVersion == modelVersion &&
    _deepEquality.equals(other.hours, hours);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (routeId.hashCode) +
    (modelVersion.hashCode) +
    (hours.hashCode);

  @override
  String toString() => 'RouteForecastResponse[generatedAt=$generatedAt, cityId=$cityId, routeId=$routeId, modelVersion=$modelVersion, hours=$hours]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'route_id'] = this.routeId;
      json[r'model_version'] = this.modelVersion;
      json[r'hours'] = this.hours;
    return json;
  }

  /// Returns a new [RouteForecastResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static RouteForecastResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "RouteForecastResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "RouteForecastResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "RouteForecastResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "RouteForecastResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'route_id'), 'Required key "RouteForecastResponse[route_id]" is missing from JSON.');
        assert(json[r'route_id'] != null, 'Required key "RouteForecastResponse[route_id]" has a null value in JSON.');
        assert(json.containsKey(r'model_version'), 'Required key "RouteForecastResponse[model_version]" is missing from JSON.');
        assert(json[r'model_version'] != null, 'Required key "RouteForecastResponse[model_version]" has a null value in JSON.');
        assert(json.containsKey(r'hours'), 'Required key "RouteForecastResponse[hours]" is missing from JSON.');
        assert(json[r'hours'] != null, 'Required key "RouteForecastResponse[hours]" has a null value in JSON.');
        return true;
      }());

      return RouteForecastResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        routeId: mapValueOfType<String>(json, r'route_id')!,
        modelVersion: mapValueOfType<String>(json, r'model_version')!,
        hours: RouteHourForecast.listFromJson(json[r'hours']),
      );
    }
    return null;
  }

  static List<RouteForecastResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <RouteForecastResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = RouteForecastResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, RouteForecastResponse> mapFromJson(dynamic json) {
    final map = <String, RouteForecastResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = RouteForecastResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of RouteForecastResponse-objects as value to a dart map
  static Map<String, List<RouteForecastResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<RouteForecastResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = RouteForecastResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'route_id',
    'model_version',
    'hours',
  };
}

