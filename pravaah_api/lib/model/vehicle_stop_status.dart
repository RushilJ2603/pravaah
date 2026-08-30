//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

/// GTFS-Realtime VehicleStopStatus.
enum VehicleStopStatus {
  INCOMING_AT._(r'INCOMING_AT'),
  STOPPED_AT._(r'STOPPED_AT'),
  IN_TRANSIT_TO._(r'IN_TRANSIT_TO'),
  ;

  /// Instantiate a new enum with the provided value.
  const VehicleStopStatus._(this._value);

  /// The underlying value of this enum member.
  final String _value;

  @override
  String toString() => _value;

  /// Encodes this enum as a value suitable for JSON.
  String toJson() => _value;

  /// Returns the instance of [VehicleStopStatus] that was successfully decoded
  /// from the passed [value] on success, null otherwise.
  static VehicleStopStatus? fromJson(dynamic value) => VehicleStopStatusTypeTransformer().decode(value);

  /// Returns a [List] containing instances of [VehicleStopStatus]
  /// that were successfully decoded from the passed [JSON][json].
  static List<VehicleStopStatus> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <VehicleStopStatus>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = VehicleStopStatus.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [VehicleStopStatus] to String,
/// and [decode] dynamic data back to [VehicleStopStatus].
class VehicleStopStatusTypeTransformer {
  factory VehicleStopStatusTypeTransformer() => _instance ??= const VehicleStopStatusTypeTransformer._();

  const VehicleStopStatusTypeTransformer._();

  /// Encodes this enum as a value suitable for JSON.
  String encode(VehicleStopStatus data) => data._value;

  /// Returns the instance of [VehicleStopStatus] that was successfully decoded
  /// from the passed [data] value on success, null otherwise.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  VehicleStopStatus? decode(dynamic data, {bool allowNull = true}) {
    if (data is VehicleStopStatus) {
      return data;
    }
    if (data != null) {
      switch (data) {
        case r'INCOMING_AT': return VehicleStopStatus.INCOMING_AT;
        case r'STOPPED_AT': return VehicleStopStatus.STOPPED_AT;
        case r'IN_TRANSIT_TO': return VehicleStopStatus.IN_TRANSIT_TO;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// The singleton instance of this transformer.
  static VehicleStopStatusTypeTransformer? _instance;
}

