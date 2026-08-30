//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

/// Where an observation came from.  Ordered loosely by trust for occupancy fusion (see SOLUTION.md section 6.5): APC and REAL_OPERATOR outrank CROWDSOURCED, and SIMULATED never enters production training unless explicitly allowed.
enum SourceType {
  REAL_OPERATOR._(r'REAL_OPERATOR'),
  PUBLIC_FEED._(r'PUBLIC_FEED'),
  APC._(r'APC'),
  AFC._(r'AFC'),
  CROWDSOURCED._(r'CROWDSOURCED'),
  DERIVED._(r'DERIVED'),
  SIMULATED._(r'SIMULATED'),
  ;

  /// Instantiate a new enum with the provided value.
  const SourceType._(this._value);

  /// The underlying value of this enum member.
  final String _value;

  @override
  String toString() => _value;

  /// Encodes this enum as a value suitable for JSON.
  String toJson() => _value;

  /// Returns the instance of [SourceType] that was successfully decoded
  /// from the passed [value] on success, null otherwise.
  static SourceType? fromJson(dynamic value) => SourceTypeTypeTransformer().decode(value);

  /// Returns a [List] containing instances of [SourceType]
  /// that were successfully decoded from the passed [JSON][json].
  static List<SourceType> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <SourceType>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = SourceType.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }
}

/// Transformation class that can [encode] an instance of [SourceType] to String,
/// and [decode] dynamic data back to [SourceType].
class SourceTypeTypeTransformer {
  factory SourceTypeTypeTransformer() => _instance ??= const SourceTypeTypeTransformer._();

  const SourceTypeTypeTransformer._();

  /// Encodes this enum as a value suitable for JSON.
  String encode(SourceType data) => data._value;

  /// Returns the instance of [SourceType] that was successfully decoded
  /// from the passed [data] value on success, null otherwise.
  ///
  /// If [allowNull] is true and the [dynamic value][data] cannot be decoded successfully,
  /// then null is returned. However, if [allowNull] is false and the [dynamic value][data]
  /// cannot be decoded successfully, then an [UnimplementedError] is thrown.
  ///
  /// The [allowNull] is very handy when an API changes and a new enum value is added or removed,
  /// and users are still using an old app with the old code.
  SourceType? decode(dynamic data, {bool allowNull = true}) {
    if (data is SourceType) {
      return data;
    }
    if (data != null) {
      switch (data) {
        case r'REAL_OPERATOR': return SourceType.REAL_OPERATOR;
        case r'PUBLIC_FEED': return SourceType.PUBLIC_FEED;
        case r'APC': return SourceType.APC;
        case r'AFC': return SourceType.AFC;
        case r'CROWDSOURCED': return SourceType.CROWDSOURCED;
        case r'DERIVED': return SourceType.DERIVED;
        case r'SIMULATED': return SourceType.SIMULATED;
        default:
          if (!allowNull) {
            throw ArgumentError('Unknown enum value to decode: $data');
          }
      }
    }
    return null;
  }

  /// The singleton instance of this transformer.
  static SourceTypeTypeTransformer? _instance;
}

