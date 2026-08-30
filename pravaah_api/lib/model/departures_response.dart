//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class DeparturesResponse {
  /// Returns a new [DeparturesResponse] instance.
  DeparturesResponse({
    required this.generatedAt,
    required this.cityId,
    required this.stopId,
    required this.stopName,
    required this.feedVersionId,
    this.departures = const [],
  });

  DateTime generatedAt;

  String cityId;

  String stopId;

  String stopName;

  int feedVersionId;

  List<DepartureView> departures;

  @override
  bool operator ==(Object other) => identical(this, other) || other is DeparturesResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.stopId == stopId &&
    other.stopName == stopName &&
    other.feedVersionId == feedVersionId &&
    _deepEquality.equals(other.departures, departures);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (stopId.hashCode) +
    (stopName.hashCode) +
    (feedVersionId.hashCode) +
    (departures.hashCode);

  @override
  String toString() => 'DeparturesResponse[generatedAt=$generatedAt, cityId=$cityId, stopId=$stopId, stopName=$stopName, feedVersionId=$feedVersionId, departures=$departures]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'stop_id'] = this.stopId;
      json[r'stop_name'] = this.stopName;
      json[r'feed_version_id'] = this.feedVersionId;
      json[r'departures'] = this.departures;
    return json;
  }

  /// Returns a new [DeparturesResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static DeparturesResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "DeparturesResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "DeparturesResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "DeparturesResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "DeparturesResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'stop_id'), 'Required key "DeparturesResponse[stop_id]" is missing from JSON.');
        assert(json[r'stop_id'] != null, 'Required key "DeparturesResponse[stop_id]" has a null value in JSON.');
        assert(json.containsKey(r'stop_name'), 'Required key "DeparturesResponse[stop_name]" is missing from JSON.');
        assert(json[r'stop_name'] != null, 'Required key "DeparturesResponse[stop_name]" has a null value in JSON.');
        assert(json.containsKey(r'feed_version_id'), 'Required key "DeparturesResponse[feed_version_id]" is missing from JSON.');
        assert(json[r'feed_version_id'] != null, 'Required key "DeparturesResponse[feed_version_id]" has a null value in JSON.');
        assert(json.containsKey(r'departures'), 'Required key "DeparturesResponse[departures]" is missing from JSON.');
        assert(json[r'departures'] != null, 'Required key "DeparturesResponse[departures]" has a null value in JSON.');
        return true;
      }());

      return DeparturesResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        stopId: mapValueOfType<String>(json, r'stop_id')!,
        stopName: mapValueOfType<String>(json, r'stop_name')!,
        feedVersionId: mapValueOfType<int>(json, r'feed_version_id')!,
        departures: DepartureView.listFromJson(json[r'departures']),
      );
    }
    return null;
  }

  static List<DeparturesResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <DeparturesResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = DeparturesResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, DeparturesResponse> mapFromJson(dynamic json) {
    final map = <String, DeparturesResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = DeparturesResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of DeparturesResponse-objects as value to a dart map
  static Map<String, List<DeparturesResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<DeparturesResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = DeparturesResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'stop_id',
    'stop_name',
    'feed_version_id',
    'departures',
  };
}

