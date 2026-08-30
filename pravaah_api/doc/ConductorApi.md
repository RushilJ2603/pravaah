# pravaah_api.api.ConductorApi

## Load the API package
```dart
import 'package:pravaah_api/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**endShiftV1ShiftsShiftIdEndPost**](ConductorApi.md#endshiftv1shiftsshiftidendpost) | **POST** /v1/shifts/{shift_id}/end | End Shift
[**reportOccupancyV1OccupancyReportPost**](ConductorApi.md#reportoccupancyv1occupancyreportpost) | **POST** /v1/occupancy/report | Report Occupancy
[**reportPositionV1ShiftsShiftIdPositionPost**](ConductorApi.md#reportpositionv1shiftsshiftidpositionpost) | **POST** /v1/shifts/{shift_id}/position | Report Position
[**startShiftV1ShiftsStartPost**](ConductorApi.md#startshiftv1shiftsstartpost) | **POST** /v1/shifts/start | Start Shift


# **endShiftV1ShiftsShiftIdEndPost**
> endShiftV1ShiftsShiftIdEndPost(shiftId)

End Shift

End only the caller's own active shift.

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = ConductorApi();
final shiftId = 56; // int | 

try {
    api_instance.endShiftV1ShiftsShiftIdEndPost(shiftId);
} catch (e) {
    print('Exception when calling ConductorApi->endShiftV1ShiftsShiftIdEndPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **shiftId** | **int**|  | 

### Return type

void (empty response body)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reportOccupancyV1OccupancyReportPost**
> Object reportOccupancyV1OccupancyReportPost(occupancyReportRequest)

Report Occupancy

Use the single crowd write path for anonymous and conductor reports.

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = ConductorApi();
final occupancyReportRequest = OccupancyReportRequest(); // OccupancyReportRequest | 

try {
    final result = api_instance.reportOccupancyV1OccupancyReportPost(occupancyReportRequest);
    print(result);
} catch (e) {
    print('Exception when calling ConductorApi->reportOccupancyV1OccupancyReportPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **occupancyReportRequest** | [**OccupancyReportRequest**](OccupancyReportRequest.md)|  | 

### Return type

**Object**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **reportPositionV1ShiftsShiftIdPositionPost**
> reportPositionV1ShiftsShiftIdPositionPost(shiftId, shiftPositionRequest)

Report Position

Append and publish a position only for the caller's active shift.

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = ConductorApi();
final shiftId = 56; // int | 
final shiftPositionRequest = ShiftPositionRequest(); // ShiftPositionRequest | 

try {
    api_instance.reportPositionV1ShiftsShiftIdPositionPost(shiftId, shiftPositionRequest);
} catch (e) {
    print('Exception when calling ConductorApi->reportPositionV1ShiftsShiftIdPositionPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **shiftId** | **int**|  | 
 **shiftPositionRequest** | [**ShiftPositionRequest**](ShiftPositionRequest.md)|  | 

### Return type

void (empty response body)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **startShiftV1ShiftsStartPost**
> ShiftStartResponse startShiftV1ShiftsStartPost(shiftStartRequest)

Start Shift

Claim one vehicle for the authenticated conductor and device.

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = ConductorApi();
final shiftStartRequest = ShiftStartRequest(); // ShiftStartRequest | 

try {
    final result = api_instance.startShiftV1ShiftsStartPost(shiftStartRequest);
    print(result);
} catch (e) {
    print('Exception when calling ConductorApi->startShiftV1ShiftsStartPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **shiftStartRequest** | [**ShiftStartRequest**](ShiftStartRequest.md)|  | 

### Return type

[**ShiftStartResponse**](ShiftStartResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

