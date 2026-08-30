//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class VehicleResponse {
  /// Returns a new [VehicleResponse] instance.
  VehicleResponse({
    required this.generatedAt,
    required this.cityId,
    required this.vehicle,
  });

  DateTime generatedAt;

  String cityId;

  VehicleView vehicle;

  @override
  bool operator ==(Object other) => identical(this, other) || other is VehicleResponse &&
    other.generatedAt == generatedAt &&
    other.cityId == cityId &&
    other.vehicle == vehicle;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (generatedAt.hashCode) +
    (cityId.hashCode) +
    (vehicle.hashCode);

  @override
  String toString() => 'VehicleResponse[generatedAt=$generatedAt, cityId=$cityId, vehicle=$vehicle]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'generated_at'] = this.generatedAt.toUtc().toIso8601String();
      json[r'city_id'] = this.cityId;
      json[r'vehicle'] = this.vehicle;
    return json;
  }

  /// Returns a new [VehicleResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static VehicleResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'generated_at'), 'Required key "VehicleResponse[generated_at]" is missing from JSON.');
        assert(json[r'generated_at'] != null, 'Required key "VehicleResponse[generated_at]" has a null value in JSON.');
        assert(json.containsKey(r'city_id'), 'Required key "VehicleResponse[city_id]" is missing from JSON.');
        assert(json[r'city_id'] != null, 'Required key "VehicleResponse[city_id]" has a null value in JSON.');
        assert(json.containsKey(r'vehicle'), 'Required key "VehicleResponse[vehicle]" is missing from JSON.');
        assert(json[r'vehicle'] != null, 'Required key "VehicleResponse[vehicle]" has a null value in JSON.');
        return true;
      }());

      return VehicleResponse(
        generatedAt: mapDateTime(json, r'generated_at', r'')!,
        cityId: mapValueOfType<String>(json, r'city_id')!,
        vehicle: VehicleView.fromJson(json[r'vehicle'])!,
      );
    }
    return null;
  }

  static List<VehicleResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <VehicleResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = VehicleResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, VehicleResponse> mapFromJson(dynamic json) {
    final map = <String, VehicleResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = VehicleResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of VehicleResponse-objects as value to a dart map
  static Map<String, List<VehicleResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<VehicleResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = VehicleResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'generated_at',
    'city_id',
    'vehicle',
  };
}

