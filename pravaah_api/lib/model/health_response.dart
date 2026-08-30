//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class HealthResponse {
  /// Returns a new [HealthResponse] instance.
  HealthResponse({
    required this.status,
    required this.cityId,
    required this.generatedAt,
    required this.database,
    required this.redis,
    required this.vehiclesTracked,
    this.feedVersionId,
  });

  String status;

  String cityId;

  DateTime generatedAt;

  bool database;

  bool redis;

  int vehiclesTracked;

  int? feedVersionId;

  @override
  bool operator ==(Object other) => identical(this, other) || other is HealthResponse &&
    other.status == status &&
    other.cityId == cityId &&
    other.generatedAt == generatedAt &&
    other.database == database &&
    other.redis == redis &&
    other.vehiclesTracked == vehiclesTracked &&
    other.feedVersionId == feedVersionId;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (status.hashCode) +
    (cityId.hashCode) +
    (generatedAt.hashCode) +
    (database.hashCode) +
    (redis.hashCode) +
    (vehiclesTracked.hashCode) +
    (feedVersionId == null ? 0 : feedVersionId!.hashCode);

  @override
  String toString() => 'HealthResponse[status=$status, cityId=$cityId, generatedAt=$generatedAt, database=$database, redis=$redis, vehiclesTracked=$vehiclesTracked, feedVersionId=$feedVersionId]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'status'] = this.status;
      json[r'city_id'] = this.cityId;
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'database'] = this.database;
      json[r'redis'] = this.redis;
      json[r'vehicles_tracked'] = this.vehiclesTracked;
    if (this.feedVersionId != null) {
      json[r'feed_version_id'] = this.feedVersionId;
    } else {
      json[r'feed_version_id'] = null;
    }
    return json;
  }

  /// Returns a new [HealthResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static HealthResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'status'), 'Required key "HealthResponse[status]" is missing from JSON.');
        assert(json[r'status'] != null, 'Required key "HealthResponse[status]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "HealthResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "HealthResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'generated_at'), 'Required key "HealthResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "HealthResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'database'), 'Required key "HealthResponse[database]" is missing from JSON.');
        assert(json[r'database'] != null, 'Required key "HealthResponse[database]" has a null value in JSON.');
        assert(json.containsKey(r'redis'), 'Required key "HealthResponse[redis]" is missing from JSON.');
        assert(json[r'redis'] != null, 'Required key "HealthResponse[redis]" has a null value in JSON.');
        assert(json.containsKey(r'vehicles_tracked'), 'Required key "HealthResponse[vehicles_tracked]" is missing from JSON.');
        assert(json[r'vehicles_tracked'] != null, 'Required key "HealthResponse[vehicles_tracked]" has a null value in JSON.');
        return true;
      }());

      return HealthResponse(
        status: mapValueOfType<String>(json, r'status')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        database: mapValueOfType<bool>(json, r'database')!,
        redis: mapValueOfType<bool>(json, r'redis')!,
        vehiclesTracked: mapValueOfType<int>(json, r'vehicles_tracked')!,
        feedVersionId: mapValueOfType<int>(json, r'feed_version_id'),
      );
    }
    return null;
  }

  static List<HealthResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <HealthResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = HealthResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, HealthResponse> mapFromJson(dynamic json) {
    final map = <String, HealthResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = HealthResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of HealthResponse-objects as value to a dart map
  static Map<String, List<HealthResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<HealthResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = HealthResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'status',
    'city_id',
    'generated_at',
    'database',
    'redis',
    'vehicles_tracked',
  };
}

