//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class PlanResponse {
  /// Returns a new [PlanResponse] instance.
  PlanResponse({
    required this.generatedAt,
    required this.cityId,
    required this.profile,
    this.options = const [],
  });

  DateTime generatedAt;

  String cityId;

  String profile;

  List<JourneyOption> options;

  @override
  bool operator ==(Object other) => identical(this, other) || other is PlanResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.profile == profile &&
    _deepEquality.equals(other.options, options);

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (profile.hashCode) +
    (options.hashCode);

  @override
  String toString() => 'PlanResponse[generatedAt=$generatedAt, cityId=$cityId, profile=$profile, options=$options]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'profile'] = this.profile;
      json[r'options'] = this.options;
    return json;
  }

  /// Returns a new [PlanResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static PlanResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "PlanResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "PlanResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "PlanResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "PlanResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'profile'), 'Required key "PlanResponse[profile]" is missing from JSON.');
        assert(json[r'profile'] != null, 'Required key "PlanResponse[profile]" has a null value in JSON.');
        assert(json.containsKey(r'options'), 'Required key "PlanResponse[options]" is missing from JSON.');
        assert(json[r'options'] != null, 'Required key "PlanResponse[options]" has a null value in JSON.');
        return true;
      }());

      return PlanResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        profile: mapValueOfType<String>(json, r'profile')!,
        options: JourneyOption.listFromJson(json[r'options']),
      );
    }
    return null;
  }

  static List<PlanResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <PlanResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = PlanResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, PlanResponse> mapFromJson(dynamic json) {
    final map = <String, PlanResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = PlanResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of PlanResponse-objects as value to a dart map
  static Map<String, List<PlanResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<PlanResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = PlanResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'profile',
    'options',
  };
}

