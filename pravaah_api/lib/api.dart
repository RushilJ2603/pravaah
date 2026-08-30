//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

library openapi.api;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:collection/collection.dart';
import 'package:http/http.dart';
import 'package:intl/intl.dart';
import 'package:meta/meta.dart';

part 'api_client.dart';
part 'api_helper.dart';
part 'api_exception.dart';
part 'auth/authentication.dart';
part 'auth/api_key_auth.dart';
part 'auth/oauth.dart';
part 'auth/http_basic_auth.dart';
part 'auth/http_bearer_auth.dart';

part 'api/conductor_api.dart';
part 'api/operator_api.dart';
part 'api/ops_api.dart';
part 'api/passenger_api.dart';
part 'api/staff_auth_api.dart';

part 'model/crowd_band.dart';
part 'model/data_health_response.dart';
part 'model/departure_view.dart';
part 'model/departures_response.dart';
part 'model/fleet_response.dart';
part 'model/http_validation_error.dart';
part 'model/health_response.dart';
part 'model/hotspot_view.dart';
part 'model/hotspots_response.dart';
part 'model/journey_leg.dart';
part 'model/journey_option.dart';
part 'model/location_inner.dart';
part 'model/login_request.dart';
part 'model/login_response.dart';
part 'model/occupancy_class.dart';
part 'model/occupancy_report_request.dart';
part 'model/plan_response.dart';
part 'model/route_forecast_response.dart';
part 'model/route_hour_forecast.dart';
part 'model/shift_position_request.dart';
part 'model/shift_start_request.dart';
part 'model/shift_start_response.dart';
part 'model/source_type.dart';
part 'model/stop_forecast.dart';
part 'model/trip_forecast_response.dart';
part 'model/validation_error.dart';
part 'model/vehicle_response.dart';
part 'model/vehicle_stop_status.dart';
part 'model/vehicle_view.dart';


/// An [ApiClient] instance that uses the default values obtained from
/// the OpenAPI specification file.
var defaultApiClient = ApiClient();

const _delimiters = {'csv': ',', 'ssv': ' ', 'tsv': '\t', 'pipes': '|'};
const _dateEpochMarker = 'epoch';
const _deepEquality = DeepCollectionEquality();
final _dateFormatter = DateFormat('yyyy-MM-dd');
final _regList = RegExp(r'^List<(.*)>$');
final _regSet = RegExp(r'^Set<(.*)>$');
final _regMap = RegExp(r'^Map<String,(.*)>$');

bool _isEpochMarker(String? pattern) => pattern == _dateEpochMarker || pattern == '/$_dateEpochMarker/';
