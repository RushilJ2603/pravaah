//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class JourneyOption {
  /// Returns a new [JourneyOption] instance.
  JourneyOption({
    required this.optionId,
    required this.totalMinutes,
    required this.transfers,
    required this.departure,
    required this.arrival,
    this.legs = const [],
    required this.score,
    this.reasons = const [],
    this.isRecommended = false,
  });

  String optionId;

  int totalMinutes;

  int transfers;

  DateTime departure;

  DateTime arrival;

  List<JourneyLeg> legs;

  num score;

  List<String> reasons;

  bool isRecommended;

  @override
  bool operator ==(Object other) => identical(this, other) || other is JourneyOption &&
    other.optionId == optionId &&
    other.totalMinutes == totalMinutes &&
    other.transfers == transfers &&
    other.departure == departure &&
    other.arrival == arrival &&
    _deepEquality.equals(other.legs, legs) &&
    other.score == score &&
    _deepEquality.equals(other.reasons, reasons) &&
    other.isRecommended == isRecommended;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (optionId.hashCode) +
    (totalMinutes.hashCode) +
    (transfers.hashCode) +
    (departure.hashCode) +
    (arrival.hashCode) +
    (legs.hashCode) +
    (score.hashCode) +
    (reasons.hashCode) +
    (isRecommended.hashCode);

  @override
  String toString() => 'JourneyOption[optionId=$optionId, totalMinutes=$totalMinutes, transfers=$transfers, departure=$departure, arrival=$arrival, legs=$legs, score=$score, reasons=$reasons, isRecommended=$isRecommended]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'option_id'] = this.optionId;
      json[r'total_minutes'] = this.totalMinutes;
      json[r'transfers'] = this.transfers;
      json[r'departure'] = this.departure.toUtc().toIso8601String();
      json[r'arrival'] = this.arrival.toUtc().toIso8601String();
      json[r'legs'] = this.legs;
      json[r'score'] = this.score;
      json[r'reasons'] = this.reasons;
      json[r'is_recommended'] = this.isRecommended;
    return json;
  }

  /// Returns a new [JourneyOption] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static JourneyOption? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'option_id'), 'Required key "JourneyOption[option_id]" is missing from JSON.');
        assert(json[r'option_id'] != null, 'Required key "JourneyOption[option_id]" has a null value in JSON.');
        assert(json.containsKey(r'total_minutes'), 'Required key "JourneyOption[total_minutes]" is missing from JSON.');
        assert(json[r'total_minutes'] != null, 'Required key "JourneyOption[total_minutes]" has a null value in JSON.');
        assert(json.containsKey(r'transfers'), 'Required key "JourneyOption[transfers]" is missing from JSON.');
        assert(json[r'transfers'] != null, 'Required key "JourneyOption[transfers]" has a null value in JSON.');
        assert(json.containsKey(r'departure'), 'Required key "JourneyOption[departure]" is missing from JSON.');
        assert(json[r'departure'] != null, 'Required key "JourneyOption[departure]" has a null value in JSON.');
        assert(json.containsKey(r'arrival'), 'Required key "JourneyOption[arrival]" is missing from JSON.');
        assert(json[r'arrival'] != null, 'Required key "JourneyOption[arrival]" has a null value in JSON.');
        assert(json.containsKey(r'legs'), 'Required key "JourneyOption[legs]" is missing from JSON.');
        assert(json[r'legs'] != null, 'Required key "JourneyOption[legs]" has a null value in JSON.');
        assert(json.containsKey(r'score'), 'Required key "JourneyOption[score]" is missing from JSON.');
        assert(json[r'score'] != null, 'Required key "JourneyOption[score]" has a null value in JSON.');
        assert(json.containsKey(r'reasons'), 'Required key "JourneyOption[reasons]" is missing from JSON.');
        assert(json[r'reasons'] != null, 'Required key "JourneyOption[reasons]" has a null value in JSON.');
        return true;
      }());

      return JourneyOption(
        optionId: mapValueOfType<String>(json, r'option_id')!,
        totalMinutes: mapValueOfType<int>(json, r'total_minutes')!,
        transfers: mapValueOfType<int>(json, r'transfers')!,
        departure: mapDateTime(json, r'departure', r'')!,
        arrival: mapDateTime(json, r'arrival', r'')!,
        legs: JourneyLeg.listFromJson(json[r'legs']),
        score: num.parse('${json[r'score']}'),
        reasons: json[r'reasons'] is Iterable
            ? (json[r'reasons'] as Iterable).cast<String>().toList(growable: false)
            : const [],
        isRecommended: mapValueOfType<bool>(json, r'is_recommended') ?? false,
      );
    }
    return null;
  }

  static List<JourneyOption> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <JourneyOption>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = JourneyOption.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, JourneyOption> mapFromJson(dynamic json) {
    final map = <String, JourneyOption>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = JourneyOption.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of JourneyOption-objects as value to a dart map
  static Map<String, List<JourneyOption>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<JourneyOption>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = JourneyOption.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'option_id',
    'total_minutes',
    'transfers',
    'departure',
    'arrival',
    'legs',
    'score',
    'reasons',
  };
}

