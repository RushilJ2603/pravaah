//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class PassengerApi {
  PassengerApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Get Vehicle
  ///
  /// Current state of one vehicle, with freshness (section 12.1).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] vehicleId (required):
  Future<Response> getVehicleV1VehiclesVehicleIdGetWithHttpInfo(String vehicleId, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/vehicles/{vehicle_id}'
      .replaceAll('{vehicle_id}', vehicleId);

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

  /// Get Vehicle
  ///
  /// Current state of one vehicle, with freshness (section 12.1).
  ///
  /// Parameters:
  ///
  /// * [String] vehicleId (required):
  Future<VehicleResponse?> getVehicleV1VehiclesVehicleIdGet(String vehicleId, { Future<void>? abortTrigger, }) async {
    final response = await getVehicleV1VehiclesVehicleIdGetWithHttpInfo(vehicleId, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'VehicleResponse',) as VehicleResponse;
    
    }
    return null;
  }

  /// List Vehicles
  ///
  /// Fleet inside a viewport (section 29.2).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] bbox (required):
  ///   minLat,minLon,maxLat,maxLon
  ///
  /// * [int] limit:
  Future<Response> listVehiclesV1VehiclesGetWithHttpInfo(String bbox, { int? limit, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/vehicles';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'bbox', bbox));
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

  /// List Vehicles
  ///
  /// Fleet inside a viewport (section 29.2).
  ///
  /// Parameters:
  ///
  /// * [String] bbox (required):
  ///   minLat,minLon,maxLat,maxLon
  ///
  /// * [int] limit:
  Future<FleetResponse?> listVehiclesV1VehiclesGet(String bbox, { int? limit, Future<void>? abortTrigger, }) async {
    final response = await listVehiclesV1VehiclesGetWithHttpInfo(bbox, limit: limit, abortTrigger: abortTrigger,);
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

  /// Plan
  ///
  /// Ranked journeys using *predicted* crowd, with a reason for each.  Routing itself is deterministic -- candidates come from the timetable, not from a model (section 5). The model only predicts the conditions each candidate will face, and the ranking is an explicit weighted cost so every option can say why it scored as it did.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [num] fromLat (required):
  ///
  /// * [num] fromLon (required):
  ///
  /// * [num] toLat (required):
  ///
  /// * [num] toLon (required):
  ///
  /// * [String] profile:
  ///
  /// * [int] windowMin:
  Future<Response> planV1PlanGetWithHttpInfo(num fromLat, num fromLon, num toLat, num toLon, { String? profile, int? windowMin, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/plan';

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

      queryParams.addAll(_queryParams('', 'from_lat', fromLat));
      queryParams.addAll(_queryParams('', 'from_lon', fromLon));
      queryParams.addAll(_queryParams('', 'to_lat', toLat));
      queryParams.addAll(_queryParams('', 'to_lon', toLon));
    if (profile != null) {
      queryParams.addAll(_queryParams('', 'profile', profile));
    }
    if (windowMin != null) {
      queryParams.addAll(_queryParams('', 'window_min', windowMin));
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

  /// Plan
  ///
  /// Ranked journeys using *predicted* crowd, with a reason for each.  Routing itself is deterministic -- candidates come from the timetable, not from a model (section 5). The model only predicts the conditions each candidate will face, and the ranking is an explicit weighted cost so every option can say why it scored as it did.
  ///
  /// Parameters:
  ///
  /// * [num] fromLat (required):
  ///
  /// * [num] fromLon (required):
  ///
  /// * [num] toLat (required):
  ///
  /// * [num] toLon (required):
  ///
  /// * [String] profile:
  ///
  /// * [int] windowMin:
  Future<PlanResponse?> planV1PlanGet(num fromLat, num fromLon, num toLat, num toLon, { String? profile, int? windowMin, Future<void>? abortTrigger, }) async {
    final response = await planV1PlanGetWithHttpInfo(fromLat, fromLon, toLat, toLon, profile: profile, windowMin: windowMin, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'PlanResponse',) as PlanResponse;
    
    }
    return null;
  }

  /// Stop Departures
  ///
  /// Upcoming scheduled departures from a stop.  Crowd fields are `UNKNOWN` until Slice B adds forecasting. They are present and explicitly unknown rather than omitted, so a client never has to infer that a missing field means an empty vehicle (section 12.4 rule 3).
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] stopId (required):
  ///
  /// * [int] windowMin:
  ///
  /// * [int] limit:
  Future<Response> stopDeparturesV1StopsStopIdDeparturesGetWithHttpInfo(String stopId, { int? windowMin, int? limit, Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/stops/{stop_id}/departures'
      .replaceAll('{stop_id}', stopId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    if (windowMin != null) {
      queryParams.addAll(_queryParams('', 'window_min', windowMin));
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

  /// Stop Departures
  ///
  /// Upcoming scheduled departures from a stop.  Crowd fields are `UNKNOWN` until Slice B adds forecasting. They are present and explicitly unknown rather than omitted, so a client never has to infer that a missing field means an empty vehicle (section 12.4 rule 3).
  ///
  /// Parameters:
  ///
  /// * [String] stopId (required):
  ///
  /// * [int] windowMin:
  ///
  /// * [int] limit:
  Future<DeparturesResponse?> stopDeparturesV1StopsStopIdDeparturesGet(String stopId, { int? windowMin, int? limit, Future<void>? abortTrigger, }) async {
    final response = await stopDeparturesV1StopsStopIdDeparturesGetWithHttpInfo(stopId, windowMin: windowMin, limit: limit, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'DeparturesResponse',) as DeparturesResponse;
    
    }
    return null;
  }

  /// Trip Forecast
  ///
  /// Predicted crowd at each upcoming stop of a trip (section 12.1).  This is the product's core claim: not how full the bus is now, but how full it will be when it reaches the stop the passenger is waiting at.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] tripId (required):
  Future<Response> tripForecastV1TripsTripIdForecastGetWithHttpInfo(String tripId, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/trips/{trip_id}/forecast'
      .replaceAll('{trip_id}', tripId);

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

  /// Trip Forecast
  ///
  /// Predicted crowd at each upcoming stop of a trip (section 12.1).  This is the product's core claim: not how full the bus is now, but how full it will be when it reaches the stop the passenger is waiting at.
  ///
  /// Parameters:
  ///
  /// * [String] tripId (required):
  Future<TripForecastResponse?> tripForecastV1TripsTripIdForecastGet(String tripId, { Future<void>? abortTrigger, }) async {
    final response = await tripForecastV1TripsTripIdForecastGetWithHttpInfo(tripId, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'TripForecastResponse',) as TripForecastResponse;
    
    }
    return null;
  }
}
