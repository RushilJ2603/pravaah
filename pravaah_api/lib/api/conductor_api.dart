//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class ConductorApi {
  ConductorApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// End Shift
  ///
  /// End only the caller's own active shift.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] shiftId (required):
  Future<Response> endShiftV1ShiftsShiftIdEndPostWithHttpInfo(int shiftId, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/shifts/{shift_id}/end'
      .replaceAll('{shift_id}', shiftId.toString());

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// End Shift
  ///
  /// End only the caller's own active shift.
  ///
  /// Parameters:
  ///
  /// * [int] shiftId (required):
  Future<void> endShiftV1ShiftsShiftIdEndPost(int shiftId, { Future<void>? abortTrigger, }) async {
    final response = await endShiftV1ShiftsShiftIdEndPostWithHttpInfo(shiftId, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Report Occupancy
  ///
  /// Use the single crowd write path for anonymous and conductor reports.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [OccupancyReportRequest] occupancyReportRequest (required):
  Future<Response> reportOccupancyV1OccupancyReportPostWithHttpInfo(OccupancyReportRequest occupancyReportRequest, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/occupancy/report';

    // ignore: prefer_final_locals
    Object? postBody = occupancyReportRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Report Occupancy
  ///
  /// Use the single crowd write path for anonymous and conductor reports.
  ///
  /// Parameters:
  ///
  /// * [OccupancyReportRequest] occupancyReportRequest (required):
  Future<Object?> reportOccupancyV1OccupancyReportPost(OccupancyReportRequest occupancyReportRequest, { Future<void>? abortTrigger, }) async {
    final response = await reportOccupancyV1OccupancyReportPostWithHttpInfo(occupancyReportRequest, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Object',) as Object;
    
    }
    return null;
  }

  /// Report Position
  ///
  /// Append and publish a position only for the caller's active shift.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [int] shiftId (required):
  ///
  /// * [ShiftPositionRequest] shiftPositionRequest (required):
  Future<Response> reportPositionV1ShiftsShiftIdPositionPostWithHttpInfo(int shiftId, ShiftPositionRequest shiftPositionRequest, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/shifts/{shift_id}/position'
      .replaceAll('{shift_id}', shiftId.toString());

    // ignore: prefer_final_locals
    Object? postBody = shiftPositionRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Report Position
  ///
  /// Append and publish a position only for the caller's active shift.
  ///
  /// Parameters:
  ///
  /// * [int] shiftId (required):
  ///
  /// * [ShiftPositionRequest] shiftPositionRequest (required):
  Future<void> reportPositionV1ShiftsShiftIdPositionPost(int shiftId, ShiftPositionRequest shiftPositionRequest, { Future<void>? abortTrigger, }) async {
    final response = await reportPositionV1ShiftsShiftIdPositionPostWithHttpInfo(shiftId, shiftPositionRequest, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Start Shift
  ///
  /// Claim one vehicle for the authenticated conductor and device.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [ShiftStartRequest] shiftStartRequest (required):
  Future<Response> startShiftV1ShiftsStartPostWithHttpInfo(ShiftStartRequest shiftStartRequest, { Future<void>? abortTrigger, }) async {
    // ignore: prefer_const_declarations
    final path = r'/v1/shifts/start';

    // ignore: prefer_final_locals
    Object? postBody = shiftStartRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
      abortTrigger: abortTrigger,
    );
  }

  /// Start Shift
  ///
  /// Claim one vehicle for the authenticated conductor and device.
  ///
  /// Parameters:
  ///
  /// * [ShiftStartRequest] shiftStartRequest (required):
  Future<ShiftStartResponse?> startShiftV1ShiftsStartPost(ShiftStartRequest shiftStartRequest, { Future<void>? abortTrigger, }) async {
    final response = await startShiftV1ShiftsStartPostWithHttpInfo(shiftStartRequest, abortTrigger: abortTrigger,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'ShiftStartResponse',) as ShiftStartResponse;
    
    }
    return null;
  }
}
