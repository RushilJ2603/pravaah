//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;

class HotspotView {
  /// Returns a new [HotspotView] instance.
  HotspotView({
    required this.stopId,
    required this.stopName,
    required this.routeId,
    required this.routeShortName,
    required this.predictedAt,
    required this.leadTimeMin,
    required this.servicesInWindow,
    required this.severity,
    required this.crowd,
    required this.reason,
  });

  String stopId;

  String stopName;

  String routeId;

  String? routeShortName;

  DateTime predictedAt;

  int leadTimeMin;

  int servicesInWindow;

  int severity;

  CrowdBand crowd;

  String reason;

  @override
  bool operator ==(Object other) => identical(this, other) || other is HotspotView &&
    other.stopId == stopId &&
    other.stopName == stopName &&
    other.routeId == routeId &&
    other.routeShortName == routeShortName &&
    other.predictedAt == predictedAt &&
    other.leadTimeMin == leadTimeMin &&
    other.servicesInWindow == servicesInWindow &&
    other.severity == severity &&
    other.crowd == crowd &&
    other.reason == reason;

  @override
  int get hashCode =>
    // ignore: unnecessary_parenthesis
    (stopId.hashCode) +
    (stopName.hashCode) +
    (routeId.hashCode) +
    (routeShortName == null ? 0 : routeShortName!.hashCode) +
    (predictedAt.hashCode) +
    (leadTimeMin.hashCode) +
    (servicesInWindow.hashCode) +
    (severity.hashCode) +
    (crowd.hashCode) +
    (reason.hashCode);

  @override
  String toString() => 'HotspotView[stopId=$stopId, stopName=$stopName, routeId=$routeId, routeShortName=$routeShortName, predictedAt=$predictedAt, leadTimeMin=$leadTimeMin, servicesInWindow=$servicesInWindow, severity=$severity, crowd=$crowd, reason=$reason]';

  Map<String, dynamic> toJson() {
    final json = <String, dynamic>{};
      json[r'stop_id'] = this.stopId;
      json[r'stop_name'] = this.stopName;
      json[r'route_id'] = this.routeId;
    if (this.routeShortName != null) {
      json[r'route_short_name'] = this.routeShortName;
    } else {
      json[r'route_short_name'] = null;
    }
      json[r'predicted_at'] = this.predictedAt.toUtc().toIso8601String();
      json[r'lead_time_min'] = this.leadTimeMin;
      json[r'services_in_window'] = this.servicesInWindow;
      json[r'severity'] = this.severity;
      json[r'crowd'] = this.crowd;
      json[r'reason'] = this.reason;
    return json;
  }

  /// Returns a new [HotspotView] instance and imports its values from
  /// [value] if it's a [Map], null otherwise.
  // ignore: prefer_constructors_over_static_methods
  static HotspotView? fromJson(dynamic value) {
    if (value is Map) {
      final json = value.cast<String, dynamic>();

      // Ensure that the map contains the required keys.
      // Note 1: the values aren't checked for validity beyond being non-null.
      // Note 2: this code is stripped in release mode!
      assert(() {
        assert(json.containsKey(r'stop_id'), 'Required key "HotspotView[stop_id]" is missing from JSON.');
        assert(json[r'stop_id'] != null, 'Required key "HotspotView[stop_id]" has a null value in JSON.');
        assert(json.containsKey(r'stop_name'), 'Required key "HotspotView[stop_name]" is missing from JSON.');
        assert(json[r'stop_name'] != null, 'Required key "HotspotView[stop_name]" has a null value in JSON.');
        assert(json.containsKey(r'route_id'), 'Required key "HotspotView[route_id]" is missing from JSON.');
        assert(json[r'route_id'] != null, 'Required key "HotspotView[route_id]" has a null value in JSON.');
        assert(json.containsKey(r'route_short_name'), 'Required key "HotspotView[route_short_name]" is missing from JSON.');
        assert(json.containsKey(r'predicted_at'), 'Required key "HotspotView[predicted_at]" is missing from JSON.');
        assert(json[r'predicted_at'] != null, 'Required key "HotspotView[predicted_at]" has a null value in JSON.');
        assert(json.containsKey(r'lead_time_min'), 'Required key "HotspotView[lead_time_min]" is missing from JSON.');
        assert(json[r'lead_time_min'] != null, 'Required key "HotspotView[lead_time_min]" has a null value in JSON.');
        assert(json.containsKey(r'services_in_window'), 'Required key "HotspotView[services_in_window]" is missing from JSON.');
        assert(json[r'services_in_window'] != null, 'Required key "HotspotView[services_in_window]" has a null value in JSON.');
        assert(json.containsKey(r'severity'), 'Required key "HotspotView[severity]" is missing from JSON.');
        assert(json[r'severity'] != null, 'Required key "HotspotView[severity]" has a null value in JSON.');
        assert(json.containsKey(r'crowd'), 'Required key "HotspotView[crowd]" is missing from JSON.');
        assert(json[r'crowd'] != null, 'Required key "HotspotView[crowd]" has a null value in JSON.');
        assert(json.containsKey(r'reason'), 'Required key "HotspotView[reason]" is missing from JSON.');
        assert(json[r'reason'] != null, 'Required key "HotspotView[reason]" has a null value in JSON.');
        return true;
      }());

      return HotspotView(
        stopId: mapValueOfType<String>(json, r'stop_id')!,
        stopName: mapValueOfType<String>(json, r'stop_name')!,
        routeId: mapValueOfType<String>(json, r'route_id')!,
        routeShortName: mapValueOfType<String>(json, r'route_short_name'),
        predictedAt: mapDateTime(json, r'predicted_at', r'')!,
        leadTimeMin: mapValueOfType<int>(json, r'lead_time_min')!,
        servicesInWindow: mapValueOfType<int>(json, r'services_in_window')!,
        severity: mapValueOfType<int>(json, r'severity')!,
        crowd: CrowdBand.fromJson(json[r'crowd'])!,
        reason: mapValueOfType<String>(json, r'reason')!,
      );
    }
    return null;
  }

  static List<HotspotView> listFromJson(dynamic json, {bool growable = false,}) {
    final result = <HotspotView>[];
    if (json is List && json.isNotEmpty) {
      for (final row in json) {
        final value = HotspotView.fromJson(row);
        if (value != null) {
          result.add(value);
        }
      }
    }
    return result.toList(growable: growable);
  }

  static Map<String, HotspotView> mapFromJson(dynamic json) {
    final map = <String, HotspotView>{};
    if (json is Map && json.isNotEmpty) {
      json = json.cast<String, dynamic>(); // ignore: parameter_assignments
      for (final entry in json.entries) {
        final value = HotspotView.fromJson(entry.value);
        if (value != null) {
          map[entry.key] = value;
        }
      }
    }
    return map;
  }

  // maps a json object with a list of HotspotView-objects as value to a dart map
  static Map<String, List<HotspotView>> mapListFromJson(dynamic json, {bool growable = false,}) {
    final map = <String, List<HotspotView>>{};
    if (json is Map && json.isNotEmpty) {
      // ignore: parameter_assignments
      json = json.cast<String, dynamic>();
      for (final entry in json.entries) {
        map[entry.key] = HotspotView.listFromJson(entry.value, growable: growable,);
      }
    }
    return map;
  }

  /// The list of required keys that must be present in a JSON.
  static const requiredKeys = <String>{
    'stop_id',
    'stop_name',
    'route_id',
    'route_short_name',
    'predicted_at',
    'lead_time_min',
    'services_in_window',
    'severity',
    'crowd',
    'reason',
  };
}

