//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class TripForecastResponse {
  /// Returns a new [TripForecastResponse] instance.
  TripForecastResponse({
    required this.generatedAt,
    required this.cityId,
    required this.tripId,
    required this.routeId,
    required this.modelVersion,
    this.stops = const [],
  });

  DateTime generatedAt;

  String cityId;

  String tripId;

  String? routeId;

  String modelVersion;

  List<StopForecast> stops;

  @override
  bool operator ==(Object other) => identical(this, other) || other is TripForecastResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.tripId == tripId &&
    other.routeId == routeId &&
    other.modelVersion == modelVersion &&
    _deepEquality.equals(other.stops, stops);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (tripId.hashCode) +
    (routeId == null ? 0 : routeId!.hashCode) +
    (modelVersion.hashCode) +
    (stops.hashCode);

  @override
  String toString() => 'TripForecastResponse[generatedAt=$generatedAt, cityId=$cityId, tripId=$tripId, routeId=$routeId, modelVersion=$modelVersion, stops=$stops]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'trip_id'] = this.tripId;
    if (this.routeId != null) {
      json[r'route_id'] = this.routeId;
    } else {
      json[r'route_id'] = null;
    }
      json[r'model_version'] = this.modelVersion;
      json[r'stops'] = this.stops;
    return json;
  }

  /// Returns a new [TripForecastResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static TripForecastResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "TripForecastResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "TripForecastResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "TripForecastResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "TripForecastResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'trip_id'), 'Required key "TripForecastResponse[trip_id]" is missing from JSON.');
        assert(json[r'trip_id'] != null, 'Required key "TripForecastResponse[trip_id]" has a null value in JSON.');
        assert(json.containsKey(r'route_id'), 'Required key "TripForecastResponse[route_id]" is missing from JSON.');
        assert(json.containsKey(r'model_version'), 'Required key "TripForecastResponse[model_version]" is missing from JSON.');
        assert(json[r'model_version'] != null, 'Required key "TripForecastResponse[model_version]" has a null value in JSON.');
        assert(json.containsKey(r'stops'), 'Required key "TripForecastResponse[stops]" is missing from JSON.');
        assert(json[r'stops'] != null, 'Required key "TripForecastResponse[stops]" has a null value in JSON.');
        return true;
      }());

      return TripForecastResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        tripId: mapValueOfType<String>(json, r'trip_id')!,
        routeId: mapValueOfType<String>(json, r'route_id'),
        modelVersion: mapValueOfType<String>(json, r'model_version')!,
        stops: StopForecast.listFromJson(json[r'stops']),
      );
    }
    return null;
  }

  static List<TripForecastResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <TripForecastResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = TripForecastResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, TripForecastResponse> mapFromJson(dynamic json) {
    final map = <String, TripForecastResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = TripForecastResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of TripForecastResponse-objects as value to a dart map
  static Map<String, List<TripForecastResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<TripForecastResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = TripForecastResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'trip_id',
    'route_id',
    'model_version',
    'stops',
  };
}

