//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class OperatorApi {
  OperatorApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Admin Vehicles
  ///
  /// Whole-fleet live state. No bbox -- an operator sees the network.  This is the one place a full-fleet read is legitimate; the passenger API requires a viewport (section 12.4 rule 5).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] limit:
  Future<Response> adminVehiclesV1AdminVehiclesGetWithHttpInfo({ int? limit, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/admin/vehicles';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Admin Vehicles
  ///
  /// Whole-fleet live state. No bbox -- an operator sees the network.  This is the one place a full-fleet read is legitimate; the passenger API requires a viewport (section 12.4 rule 5).
  ///
  /// Parameters:
  ///
  /// * [int] limit:
  Future<FleetResponse?> adminVehiclesV1AdminVehiclesGet({ int? limit, Future<void>? abortTrigger, }) async {
    final response = await adminVehiclesV1AdminVehiclesGetWithHttpInfo(limit: limit, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'FleetResponse',) as FleetResponse;
    
    }
    return null;
  }

  /// Data Health
  ///
  /// Feed freshness and coverage (section 12.2).  Occupancy coverage is reported explicitly because a silent drop in it is the failure most likely to go unnoticed -- the map keeps moving while the crowd layer quietly becomes all-unknown.
  ///
  /// Note: This method returns the HTTP [Response].
  Future<Response> dataHealthV1AdminDataHealthGetWithHttpInfo({ Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/admin/data-health';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Data Health
  ///
  /// Feed freshness and coverage (section 12.2).  Occupancy coverage is reported explicitly because a silent drop in it is the failure most likely to go unnoticed -- the map keeps moving while the crowd layer quietly becomes all-unknown.
  Future<DataHealthResponse?> dataHealthV1AdminDataHealthGet({ Future<void>? abortTrigger, }) async {
    final response = await dataHealthV1AdminDataHealthGetWithHttpInfo(abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'DataHealthResponse',) as DataHealthResponse;
    
    }
    return null;
  }

  /// Hotspots
  ///
  /// Predicted crowding hotspots, ranked by severity and urgency.  This is the operator's core screen: problems that have not happened yet, with enough lead time to act on them (section 3.2).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] horizonMin:
  ///
  /// * [int] limit:
  Future<Response> hotspotsV1AdminHotspotsGetWithHttpInfo({ int? horizonMin, int? limit, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/admin/hotspots';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (horizonMin != null) {
      queryParams.addAll(_queryParams('', 'horizon_min', horizonMin));
    }
    if (limit != null) {
      queryParams.addAll(_queryParams('', 'limit', limit));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Hotspots
  ///
  /// Predicted crowding hotspots, ranked by severity and urgency.  This is the operator's core screen: problems that have not happened yet, with enough lead time to act on them (section 3.2).
  ///
  /// Parameters:
  ///
  /// * [int] horizonMin:
  ///
  /// * [int] limit:
  Future<HotspotsResponse?> hotspotsV1AdminHotspotsGet({ int? horizonMin, int? limit, Future<void>? abortTrigger, }) async {
    final response = await hotspotsV1AdminHotspotsGetWithHttpInfo(horizonMin: horizonMin, limit: limit, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'HotspotsResponse',) as HotspotsResponse;
    
    }
    return null;
  }

  /// Route Forecast
  ///
  /// Hour-by-hour predicted load for one route (section 12.2).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] routeId (required):
  ///
  /// * [int] hours:
  Future<Response> routeForecastV1AdminRoutesRouteIdForecastGetWithHttpInfo(String routeId, { int? hours, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/admin/routes/{route_id}/forecast'
      .replaceAll('{route_id}', routeId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (hours != null) {
      queryParams.addAll(_queryParams('', 'hours', hours));
    }

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Route Forecast
  ///
  /// Hour-by-hour predicted load for one route (section 12.2).
  ///
  /// Parameters:
  ///
  /// * [String] routeId (required):
  ///
  /// * [int] hours:
  Future<RouteForecastResponse?> routeForecastV1AdminRoutesRouteIdForecastGet(String routeId, { int? hours, Future<void>? abortTrigger, }) async {
    final response = await routeForecastV1AdminRoutesRouteIdForecastGetWithHttpInfo(routeId, hours: hours, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'RouteForecastResponse',) as RouteForecastResponse;
    
    }
    return null;
  }
}
