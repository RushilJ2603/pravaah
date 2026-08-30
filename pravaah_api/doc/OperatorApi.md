# pravaah_api.api.OperatorApi

## Load the API package
```dart
import 'package:pravaah_api/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**adminVehiclesV1AdminVehiclesGet**](OperatorApi.md#adminvehiclesv1adminvehiclesget) | **GET** /v1/admin/vehicles | Admin Vehicles
[**dataHealthV1AdminDataHealthGet**](OperatorApi.md#datahealthv1admindatahealthget) | **GET** /v1/admin/data-health | Data Health
[**hotspotsV1AdminHotspotsGet**](OperatorApi.md#hotspotsv1adminhotspotsget) | **GET** /v1/admin/hotspots | Hotspots
[**routeForecastV1AdminRoutesRouteIdForecastGet**](OperatorApi.md#routeforecastv1adminroutesrouteidforecastget) | **GET** /v1/admin/routes/{route_id}/forecast | Route Forecast


# **adminVehiclesV1AdminVehiclesGet**
> FleetResponse adminVehiclesV1AdminVehiclesGet(limit)

Admin Vehicles

Whole-fleet live state. No bbox -- an operator sees the network.  This is the one place a full-fleet read is legitimate; the passenger API requires a viewport (section 12.4 rule 5).

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = OperatorApi();
final limit = 56; // int | 

try {
    final result = api_instance.adminVehiclesV1AdminVehiclesGet(limit);
    print(result);
} catch (e) {
    print('Exception when calling OperatorApi->adminVehiclesV1AdminVehiclesGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**|  | [optional] [default to 2000]

### Return type

[**FleetResponse**](FleetResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **dataHealthV1AdminDataHealthGet**
> DataHealthResponse dataHealthV1AdminDataHealthGet()

Data Health

Feed freshness and coverage (section 12.2).  Occupancy coverage is reported explicitly because a silent drop in it is the failure most likely to go unnoticed -- the map keeps moving while the crowd layer quietly becomes all-unknown.

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = OperatorApi();

try {
    final result = api_instance.dataHealthV1AdminDataHealthGet();
    print(result);
} catch (e) {
    print('Exception when calling OperatorApi->dataHealthV1AdminDataHealthGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**DataHealthResponse**](DataHealthResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **hotspotsV1AdminHotspotsGet**
> HotspotsResponse hotspotsV1AdminHotspotsGet(horizonMin, limit)

Hotspots

Predicted crowding hotspots, ranked by severity and urgency.  This is the operator's core screen: problems that have not happened yet, with enough lead time to act on them (section 3.2).

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = OperatorApi();
final horizonMin = 56; // int | 
final limit = 56; // int | 

try {
    final result = api_instance.hotspotsV1AdminHotspotsGet(horizonMin, limit);
    print(result);
} catch (e) {
    print('Exception when calling OperatorApi->hotspotsV1AdminHotspotsGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **horizonMin** | **int**|  | [optional] [default to 60]
 **limit** | **int**|  | [optional] [default to 20]

### Return type

[**HotspotsResponse**](HotspotsResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **routeForecastV1AdminRoutesRouteIdForecastGet**
> RouteForecastResponse routeForecastV1AdminRoutesRouteIdForecastGet(routeId, hours)

Route Forecast

Hour-by-hour predicted load for one route (section 12.2).

### Example
```dart
import 'package:pravaah_api/api.dart';
// TODO Configure HTTP Bearer authorization: HTTPBearer
// Case 1. Use String Token
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken('YOUR_ACCESS_TOKEN');
// Case 2. Use Function which generate token.
// String yourTokenGeneratorFunction() { ... }
//defaultApiClient.getAuthentication<HttpBearerAuth>('HTTPBearer').setAccessToken(yourTokenGeneratorFunction);

final api_instance = OperatorApi();
final routeId = routeId_example; // String | 
final hours = 56; // int | 

try {
    final result = api_instance.routeForecastV1AdminRoutesRouteIdForecastGet(routeId, hours);
    print(result);
} catch (e) {
    print('Exception when calling OperatorApi->routeForecastV1AdminRoutesRouteIdForecastGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **routeId** | **String**|  | 
 **hours** | **int**|  | [optional] [default to 12]

### Return type

[**RouteForecastResponse**](RouteForecastResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

