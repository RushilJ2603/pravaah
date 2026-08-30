//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class DataHealthResponse {
  /// Returns a new [DataHealthResponse] instance.
  DataHealthResponse({
    required this.generatedAt,
    required this.cityId,
    required this.database,
    required this.redis,
    required this.feedVersionId,
    required this.vehiclesTracked,
    required this.vehiclesStale,
    required this.vehiclesWithOccupancy,
    required this.occupancyCoverage,
    required this.oldestPositionAgeS,
    this.sourceTypes = const {},
    required this.forecastModel,
  });

  DateTime generatedAt;

  String cityId;

  bool database;

  bool redis;

  int? feedVersionId;

  int vehiclesTracked;

  int vehiclesStale;

  int vehiclesWithOccupancy;

  num occupancyCoverage;

  int oldestPositionAgeS;

  Map<String, int> sourceTypes;

  String? forecastModel;

  @override
  bool operator ==(Object other) => identical(this, other) || other is DataHealthResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.database == database &&
    other.redis == redis &&
    other.feedVersionId == feedVersionId &&
    other.vehiclesTracked == vehiclesTracked &&
    other.vehiclesStale == vehiclesStale &&
    other.vehiclesWithOccupancy == vehiclesWithOccupancy &&
    other.occupancyCoverage == occupancyCoverage &&
    other.oldestPositionAgeS == oldestPositionAgeS &&
    _deepEquality.equals(other.sourceTypes, sourceTypes) &&
    other.forecastModel == forecastModel;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (database.hashCode) +
    (redis.hashCode) +
    (feedVersionId == null ? 0 : feedVersionId!.hashCode) +
    (vehiclesTracked.hashCode) +
    (vehiclesStale.hashCode) +
    (vehiclesWithOccupancy.hashCode) +
    (occupancyCoverage.hashCode) +
    (oldestPositionAgeS.hashCode) +
    (sourceTypes.hashCode) +
    (forecastModel == null ? 0 : forecastModel!.hashCode);

  @override
  String toString() => 'DataHealthResponse[generatedAt=$generatedAt, cityId=$cityId, database=$database, redis=$redis, feedVersionId=$feedVersionId, vehiclesTracked=$vehiclesTracked, vehiclesStale=$vehiclesStale, vehiclesWithOccupancy=$vehiclesWithOccupancy, occupancyCoverage=$occupancyCoverage, oldestPositionAgeS=$oldestPositionAgeS, sourceTypes=$sourceTypes, forecastModel=$forecastModel]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'database'] = this.database;
      json[r'redis'] = this.redis;
    if (this.feedVersionId != null) {
      json[r'feed_version_id'] = this.feedVersionId;
    } else {
      json[r'feed_version_id'] = null;
    }
      json[r'vehicles_tracked'] = this.vehiclesTracked;
      json[r'vehicles_stale'] = this.vehiclesStale;
      json[r'vehicles_with_occupancy'] = this.vehiclesWithOccupancy;
      json[r'occupancy_coverage'] = this.occupancyCoverage;
      json[r'oldest_position_age_s'] = this.oldestPositionAgeS;
      json[r'source_types'] = this.sourceTypes;
    if (this.forecastModel != null) {
      json[r'forecast_model'] = this.forecastModel;
    } else {
      json[r'forecast_model'] = null;
    }
    return json;
  }

  /// Returns a new [DataHealthResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static DataHealthResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "DataHealthResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "DataHealthResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "DataHealthResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "DataHealthResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'database'), 'Required key "DataHealthResponse[database]" is missing from JSON.');
        assert(json[r'database'] != null, 'Required key "DataHealthResponse[database]" has a null value in JSON.');
        assert(json.containsKey(r'redis'), 'Required key "DataHealthResponse[redis]" is missing from JSON.');
        assert(json[r'redis'] != null, 'Required key "DataHealthResponse[redis]" has a null value in JSON.');
        assert(json.containsKey(r'feed_version_id'), 'Required key "DataHealthResponse[feed_version_id]" is missing from JSON.');
        assert(json.containsKey(r'vehicles_tracked'), 'Required key "DataHealthResponse[vehicles_tracked]" is missing from JSON.');
        assert(json[r'vehicles_tracked'] != null, 'Required key "DataHealthResponse[vehicles_tracked]" has a null value in JSON.');
        assert(json.containsKey(r'vehicles_stale'), 'Required key "DataHealthResponse[vehicles_stale]" is missing from JSON.');
        assert(json[r'vehicles_stale'] != null, 'Required key "DataHealthResponse[vehicles_stale]" has a null value in JSON.');
        assert(json.containsKey(r'vehicles_with_occupancy'), 'Required key "DataHealthResponse[vehicles_with_occupancy]" is missing from JSON.');
        assert(json[r'vehicles_with_occupancy'] != null, 'Required key "DataHealthResponse[vehicles_with_occupancy]" has a null value in JSON.');
        assert(json.containsKey(r'occupancy_coverage'), 'Required key "DataHealthResponse[occupancy_coverage]" is missing from JSON.');
        assert(json[r'occupancy_coverage'] != null, 'Required key "DataHealthResponse[occupancy_coverage]" has a null value in JSON.');
        assert(json.containsKey(r'oldest_position_age_s'), 'Required key "DataHealthResponse[oldest_position_age_s]" is missing from JSON.');
        assert(json[r'oldest_position_age_s'] != null, 'Required key "DataHealthResponse[oldest_position_age_s]" has a null value in JSON.');
        assert(json.containsKey(r'source_types'), 'Required key "DataHealthResponse[source_types]" is missing from JSON.');
        assert(json[r'source_types'] != null, 'Required key "DataHealthResponse[source_types]" has a null value in JSON.');
        assert(json.containsKey(r'forecast_model'), 'Required key "DataHealthResponse[forecast_model]" is missing from JSON.');
        return true;
      }());

      return DataHealthResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        database: mapValueOfType<bool>(json, r'database')!,
        redis: mapValueOfType<bool>(json, r'redis')!,
        feedVersionId: mapValueOfType<int>(json, r'feed_version_id'),
        vehiclesTracked: mapValueOfType<int>(json, r'vehicles_tracked')!,
        vehiclesStale: mapValueOfType<int>(json, r'vehicles_stale')!,
        vehiclesWithOccupancy: mapValueOfType<int>(json, r'vehicles_with_occupancy')!,
        occupancyCoverage: num.parse('${json[r'occupancy_coverage']}'),
        oldestPositionAgeS: mapValueOfType<int>(json, r'oldest_position_age_s')!,
        sourceTypes: mapCastOfType<String, int>(json, r'source_types')!,
        forecastModel: mapValueOfType<String>(json, r'forecast_model'),
      );
    }
    return null;
  }

  static List<DataHealthResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <DataHealthResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = DataHealthResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, DataHealthResponse> mapFromJson(dynamic json) {
    final map = <String, DataHealthResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = DataHealthResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of DataHealthResponse-objects as value to a dart map
  static Map<String, List<DataHealthResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<DataHealthResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = DataHealthResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'database',
    'redis',
    'feed_version_id',
    'vehicles_tracked',
    'vehicles_stale',
    'vehicles_with_occupancy',
    'occupancy_coverage',
    'oldest_position_age_s',
    'source_types',
    'forecast_model',
  };
}

