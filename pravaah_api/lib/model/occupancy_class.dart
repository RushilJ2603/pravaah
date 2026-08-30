//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

/// GTFS-Realtime occupancy ladder, preserved verbatim so the mapping is lossless.  UNKNOWN is a real member of this enum, distinct from both `None` and EMPTY. SOLUTION.md section 12.4 rule 3: missing occupancy must never silently become zero or \"empty bus\". Coercing UNKNOWN to EMPTY is a defect.
enum OccupancyClass {
  EMPTY._(r'EMPTY'),
  MANY_SEATS_AVAILABLE._(r'MANY_SEATS_AVAILABLE'),
  FEW_SEATS_AVAILABLE._(r'FEW_SEATS_AVAILABLE'),
  STANDING_ROOM_ONLY._(r'STANDING_ROOM_ONLY'),
  CRUSHED_STANDING_ROOM_ONLY._(r'CRUSHED_STANDING_ROOM_ONLY'),
  FULL._(r'FULL'),
  NOT_ACCEPTING_PASSENGERS._(r'NOT_ACCEPTING_PASSENGERS'),
  UNKNOWN._(r'UNKNOWN'),
  ;

  /// Instantiate a new enum with the provided value.
  const OccupancyClass._(this._value);

  /// The underlying value of this enum member.
  final String _value;

  @override
  String toString() => _value;

  /// Encodes this enum as a value suitable for JSON.
  String toJson() => _value;

  /// Returns the instance of [OccupancyClass] that was successfully decoded
  /// from the passed [value] on success, null otherwise.
  static OccupancyClass? fromJson(dynamic value) => OccupancyClassTypeTransformer().decode(value);

  /// Returns a [List] containing instances of [OccupancyClass]
  /// that were successfully decoded from the passed [JSON][json].
  static List<OccupancyClass> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <OccupancyClass>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = OccupancyClass.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [OccupancyClass] to String,
/// and [decode] dynamic data back to [OccupancyClass].
class OccupancyClassTypeTransformer {
  factory OccupancyClassTypeTransformer() => _instance ??= const OccupancyClassTypeTransformer._();

  const OccupancyClassTypeTransformer._();

  /// Encodes this enum as a value suitable for JSON.
  String encode(OccupancyClass data) => data._value;

  /// Returns the instance of [OccupancyClass] that was successfully decoded
  /// from the passed [data] value on success, null otherwise.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  OccupancyClass? decode(dynamic data, {bool allowNull = true}) {
    if (data is OccupancyClass) {
      return data;
    }
    if (data != null) {
      switch (data) {
        case r'EMPTY': return OccupancyClass.EMPTY;
        case r'MANY_SEATS_AVAILABLE': return OccupancyClass.MANY_SEATS_AVAILABLE;
        case r'FEW_SEATS_AVAILABLE': return OccupancyClass.FEW_SEATS_AVAILABLE;
        case r'STANDING_ROOM_ONLY': return OccupancyClass.STANDING_ROOM_ONLY;
        case r'CRUSHED_STANDING_ROOM_ONLY': return OccupancyClass.CRUSHED_STANDING_ROOM_ONLY;
        case r'FULL': return OccupancyClass.FULL;
        case r'NOT_ACCEPTING_PASSENGERS': return OccupancyClass.NOT_ACCEPTING_PASSENGERS;
        case r'UNKNOWN': return OccupancyClass.UNKNOWN;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// The singleton instance of this transformer.
  static OccupancyClassTypeTransformer? _instance;
}

