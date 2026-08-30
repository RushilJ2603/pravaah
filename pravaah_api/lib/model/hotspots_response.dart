//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class HotspotsResponse {
  /// Returns a new [HotspotsResponse] instance.
  HotspotsResponse({
    required this.generatedAt,
    required this.cityId,
    required this.horizonMin,
    required this.modelVersion,
    required this.count,
    this.hotspots = const [],
  });

  DateTime generatedAt;

  String cityId;

  int horizonMin;

  String modelVersion;

  int count;

  List<HotspotView> hotspots;

  @override
  bool operator ==(Object other) => identical(this, other) || other is HotspotsResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.horizonMin == horizonMin &&
    other.modelVersion == modelVersion &&
    other.count == count &&
    _deepEquality.equals(other.hotspots, hotspots);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (horizonMin.hashCode) +
    (modelVersion.hashCode) +
    (count.hashCode) +
    (hotspots.hashCode);

  @override
  String toString() => 'HotspotsResponse[generatedAt=$generatedAt, cityId=$cityId, horizonMin=$horizonMin, modelVersion=$modelVersion, count=$count, hotspots=$hotspots]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'horizon_min'] = this.horizonMin;
      json[r'model_version'] = this.modelVersion;
      json[r'count'] = this.count;
      json[r'hotspots'] = this.hotspots;
    return json;
  }

  /// Returns a new [HotspotsResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static HotspotsResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "HotspotsResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "HotspotsResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "HotspotsResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "HotspotsResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'horizon_min'), 'Required key "HotspotsResponse[horizon_min]" is missing from JSON.');
        assert(json[r'horizon_min'] != null, 'Required key "HotspotsResponse[horizon_min]" has a null value in JSON.');
        assert(json.containsKey(r'model_version'), 'Required key "HotspotsResponse[model_version]" is missing from JSON.');
        assert(json[r'model_version'] != null, 'Required key "HotspotsResponse[model_version]" has a null value in JSON.');
        assert(json.containsKey(r'count'), 'Required key "HotspotsResponse[count]" is missing from JSON.');
        assert(json[r'count'] != null, 'Required key "HotspotsResponse[count]" has a null value in JSON.');
        assert(json.containsKey(r'hotspots'), 'Required key "HotspotsResponse[hotspots]" is missing from JSON.');
        assert(json[r'hotspots'] != null, 'Required key "HotspotsResponse[hotspots]" has a null value in JSON.');
        return true;
      }());

      return HotspotsResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        horizonMin: mapValueOfType<int>(json, r'horizon_min')!,
        modelVersion: mapValueOfType<String>(json, r'model_version')!,
        count: mapValueOfType<int>(json, r'count')!,
        hotspots: HotspotView.listFromJson(json[r'hotspots']),
      );
    }
    return null;
  }

  static List<HotspotsResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <HotspotsResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = HotspotsResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, HotspotsResponse> mapFromJson(dynamic json) {
    final map = <String, HotspotsResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = HotspotsResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of HotspotsResponse-objects as value to a dart map
  static Map<String, List<HotspotsResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<HotspotsResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = HotspotsResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'horizon_min',
    'model_version',
    'count',
    'hotspots',
  };
}

