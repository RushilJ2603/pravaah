//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class ShiftStartResponse {
  /// Returns a new [ShiftStartResponse] instance.
  ShiftStartResponse({
    required this.shiftId,
    required this.startedAt,
  });

  int shiftId;

  DateTime startedAt;

  @override
  bool operator ==(Object other) => identical(this, other) || other is ShiftStartResponse &&
    other.shiftId == shiftId &&
    other.startedAt == startedAt;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (shiftId.hashCode) +
    (startedAt.hashCode);

  @override
  String toString() => 'ShiftStartResponse[shiftId=$shiftId, startedAt=$startedAt]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'shift_id'] = this.shiftId;
      json[r'started_at'] = this.startedAt.toUtc().toIso8601String();
    return json;
  }

  /// Returns a new [ShiftStartResponse] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static ShiftStartResponse? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'shift_id'), 'Required key "ShiftStartResponse[shift_id]" is missing from JSON.');
        assert(json[r'shift_id'] != null, 'Required key "ShiftStartResponse[shift_id]" has a null value in JSON.');
        assert(json.containsKey(r'started_at'), 'Required key "ShiftStartResponse[started_at]" is missing from JSON.');
        assert(json[r'started_at'] != null, 'Required key "ShiftStartResponse[started_at]" has a null value in JSON.');
        return true;
      }());

      return ShiftStartResponse(
        shiftId: mapValueOfType<int>(json, r'shift_id')!,
        startedAt: mapDateTime(json, r'started_at', r'')!,
      );
    }
    return null;
  }

  static List<ShiftStartResponse> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <ShiftStartResponse>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = ShiftStartResponse.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, ShiftStartResponse> mapFromJson(dynamic json) {
    final map = <String, ShiftStartResponse>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = ShiftStartResponse.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of ShiftStartResponse-objects as value to a dart map
  static Map<String, List<ShiftStartResponse>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<ShiftStartResponse>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = ShiftStartResponse.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'shift_id',
    'started_at',
  };
}

