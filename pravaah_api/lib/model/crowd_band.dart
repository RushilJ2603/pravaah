//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class CrowdBand {
  /// Returns a new [CrowdBand] instance.
  CrowdBand({
    required this.p10Class,
    required this.p50Class,
    required this.p90Class,
    required this.p10Onboard,
    required this.p50Onboard,
    required this.p90Onboard,
    required this.p50Ratio,
    required this.capacity,
    required this.modelVersion,
    this.isFallback = false,
  });

  OccupancyClass p10Class;

  OccupancyClass p50Class;

  OccupancyClass p90Class;

  int? p10Onboard;

  int? p50Onboard;

  int? p90Onboard;

  num? p50Ratio;

  int? capacity;

  String modelVersion;

  bool isFallback;

  @override
  bool operator ==(Object other) => identical(this, other) || other is CrowdBand &&
    other.p10Class == p10Class &&
    other.p50Class == p50Class &&
    other.p90Class == p90Class &&
    other.p10Onboard == p10Onboard &&
    other.p50Onboard == p50Onboard &&
    other.p90Onboard == p90Onboard &&
    other.p50Ratio == p50Ratio &&
    other.capacity == capacity &&
    other.modelVersion == modelVersion &&
    other.isFallback == isFallback;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (p10Class.hashCode) +
    (p50Class.hashCode) +
    (p90Class.hashCode) +
    (p10Onboard == null ? 0 : p10Onboard!.hashCode) +
    (p50Onboard == null ? 0 : p50Onboard!.hashCode) +
    (p90Onboard == null ? 0 : p90Onboard!.hashCode) +
    (p50Ratio == null ? 0 : p50Ratio!.hashCode) +
    (capacity == null ? 0 : capacity!.hashCode) +
    (modelVersion.hashCode) +
    (isFallback.hashCode);

  @override
  String toString() => 'CrowdBand[p10Class=$p10Class, p50Class=$p50Class, p90Class=$p90Class, p10Onboard=$p10Onboard, p50Onboard=$p50Onboard, p90Onboard=$p90Onboard, p50Ratio=$p50Ratio, capacity=$capacity, modelVersion=$modelVersion, isFallback=$isFallback]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'p10_class'] = this.p10Class;
      json[r'p50_class'] = this.p50Class;
      json[r'p90_class'] = this.p90Class;
    if (this.p10Onboard != null) {
      json[r'p10_onboard'] = this.p10Onboard;
    } else {
      json[r'p10_onboard'] = null;
    }
    if (this.p50Onboard != null) {
      json[r'p50_onboard'] = this.p50Onboard;
    } else {
      json[r'p50_onboard'] = null;
    }
    if (this.p90Onboard != null) {
      json[r'p90_onboard'] = this.p90Onboard;
    } else {
      json[r'p90_onboard'] = null;
    }
    if (this.p50Ratio != null) {
      json[r'p50_ratio'] = this.p50Ratio;
    } else {
      json[r'p50_ratio'] = null;
    }
    if (this.capacity != null) {
      json[r'capacity'] = this.capacity;
    } else {
      json[r'capacity'] = null;
    }
      json[r'model_version'] = this.modelVersion;
      json[r'is_fallback'] = this.isFallback;
    return json;
  }

  /// Returns a new [CrowdBand] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static CrowdBand? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'p10_class'), 'Required key "CrowdBand[p10_class]" is missing from JSON.');
        assert(json[r'p10_class'] != null, 'Required key "CrowdBand[p10_class]" has a null value in JSON.');
        assert(json.containsKey(r'p50_class'), 'Required key "CrowdBand[p50_class]" is missing from JSON.');
        assert(json[r'p50_class'] != null, 'Required key "CrowdBand[p50_class]" has a null value in JSON.');
        assert(json.containsKey(r'p90_class'), 'Required key "CrowdBand[p90_class]" is missing from JSON.');
        assert(json[r'p90_class'] != null, 'Required key "CrowdBand[p90_class]" has a null value in JSON.');
        assert(json.containsKey(r'p10_onboard'), 'Required key "CrowdBand[p10_onboard]" is missing from JSON.');
        assert(json.containsKey(r'p50_onboard'), 'Required key "CrowdBand[p50_onboard]" is missing from JSON.');
        assert(json.containsKey(r'p90_onboard'), 'Required key "CrowdBand[p90_onboard]" is missing from JSON.');
        assert(json.containsKey(r'p50_ratio'), 'Required key "CrowdBand[p50_ratio]" is missing from JSON.');
        assert(json.containsKey(r'capacity'), 'Required key "CrowdBand[capacity]" is missing from JSON.');
        assert(json.containsKey(r'model_version'), 'Required key "CrowdBand[model_version]" is missing from JSON.');
        assert(json[r'model_version'] != null, 'Required key "CrowdBand[model_version]" has a null value in JSON.');
        return true;
      }());

      return CrowdBand(
        p10Class: OccupancyClass.fromJson(json[r'p10_class'])!,
        p50Class: OccupancyClass.fromJson(json[r'p50_class'])!,
        p90Class: OccupancyClass.fromJson(json[r'p90_class'])!,
        p10Onboard: mapValueOfType<int>(json, r'p10_onboard'),
        p50Onboard: mapValueOfType<int>(json, r'p50_onboard'),
        p90Onboard: mapValueOfType<int>(json, r'p90_onboard'),
        p50Ratio: json[r'p50_ratio'] == null
            ? null
            : num.parse('${json[r'p50_ratio']}'),
        capacity: mapValueOfType<int>(json, r'capacity'),
        modelVersion: mapValueOfType<String>(json, r'model_version')!,
        isFallback: mapValueOfType<bool>(json, r'is_fallback') ?? false,
      );
    }
    return null;
  }

  static List<CrowdBand> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <CrowdBand>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = CrowdBand.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, CrowdBand> mapFromJson(dynamic json) {
    final map = <String, CrowdBand>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = CrowdBand.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of CrowdBand-objects as value to a dart map
  static Map<String, List<CrowdBand>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<CrowdBand>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = CrowdBand.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'p10_class',
    'p50_class',
    'p90_class',
    'p10_onboard',
    'p50_onboard',
    'p90_onboard',
    'p50_ratio',
    'capacity',
    'model_version',
  };
}

