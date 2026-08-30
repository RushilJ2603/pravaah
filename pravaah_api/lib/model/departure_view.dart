//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class DepartureView {
  /// Returns a new [DepartureView] instance.
  DepartureView({
    required this.tripId,
    this.routeId,
    this.directionId,
    required this.scheduledDeparture,
    this.headsign,
    this.crowdClass = OccupancyClass.UNKNOWN,
    this.crowdP50,
    this.isForecast = false,
  });

  String tripId;

  String? routeId;

  int? directionId;

  DateTime scheduledDeparture;

  String? headsign;

  OccupancyClass crowdClass;

  num? crowdP50;

  bool isForecast;

  @override
  bool operator ==(Object other) => identical(this, other) || other is DepartureView &&
    other.tripId == tripId &&
    other.routeId == routeId &&
    other.directionId == directionId &&
    other.scheduledDeparture == scheduledDeparture &&
    other.headsign == headsign &&
    other.crowdClass == crowdClass &&
    other.crowdP50 == crowdP50 &&
    other.isForecast == isForecast;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (tripId.hashCode) +
    (routeId == null ? 0 : routeId!.hashCode) +
    (directionId == null ? 0 : directionId!.hashCode) +
    (scheduledDeparture.hashCode) +
    (headsign == null ? 0 : headsign!.hashCode) +
    (crowdClass.hashCode) +
    (crowdP50 == null ? 0 : crowdP50!.hashCode) +
    (isForecast.hashCode);

  @override
  String toString() => 'DepartureView[tripId=$tripId, routeId=$routeId, directionId=$directionId, scheduledDeparture=$scheduledDeparture, headsign=$headsign, crowdClass=$crowdClass, crowdP50=$crowdP50, isForecast=$isForecast]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'trip_id'] = this.tripId;
    if (this.routeId != null) {
      json[r'route_id'] = this.routeId;
    } else {
      json[r'route_id'] = null;
    }
    if (this.directionId != null) {
      json[r'direction_id'] = this.directionId;
    } else {
      json[r'direction_id'] = null;
    }
      json[r'scheduled_departure'] = this.scheduledDeparture.toUtc().toIso8601String();
    if (this.headsign != null) {
      json[r'headsign'] = this.headsign;
    } else {
      json[r'headsign'] = null;
    }
      json[r'crowd_class'] = this.crowdClass;
    if (this.crowdP50 != null) {
      json[r'crowd_p50'] = this.crowdP50;
    } else {
      json[r'crowd_p50'] = null;
    }
      json[r'is_forecast'] = this.isForecast;
    return json;
  }

  /// Returns a new [DepartureView] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static DepartureView? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'trip_id'), 'Required key "DepartureView[trip_id]" is missing from JSON.');
        assert(json[r'trip_id'] != null, 'Required key "DepartureView[trip_id]" has a null value in JSON.');
        assert(json.containsKey(r'scheduled_departure'), 'Required key "DepartureView[scheduled_departure]" is missing from JSON.');
        assert(json[r'scheduled_departure'] != null, 'Required key "DepartureView[scheduled_departure]" has a null value in JSON.');
        return true;
      }());

      return DepartureView(
        tripId: mapValueOfType<String>(json, r'trip_id')!,
        routeId: mapValueOfType<String>(json, r'route_id'),
        directionId: mapValueOfType<int>(json, r'direction_id'),
        scheduledDeparture: mapDateTime(json, r'scheduled_departure', r'')!,
        headsign: mapValueOfType<String>(json, r'headsign'),
        crowdClass: OccupancyClass.fromJson(json[r'crowd_class']) ?? OccupancyClass.UNKNOWN,
        crowdP50: json[r'crowd_p50'] == null
            ? null
            : num.parse('${json[r'crowd_p50']}'),
        isForecast: mapValueOfType<bool>(json, r'is_forecast') ?? false,
      );
    }
    return null;
  }

  static List<DepartureView> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <DepartureView>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = DepartureView.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, DepartureView> mapFromJson(dynamic json) {
    final map = <String, DepartureView>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = DepartureView.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of DepartureView-objects as value to a dart map
  static Map<String, List<DepartureView>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<DepartureView>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = DepartureView.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'trip_id',
    'scheduled_departure',
  };
}

