# pravaah_api.api.PassengerApi

## Load the API package
```dart
import 'package:pravaah_api/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getVehicleV1VehiclesVehicleIdGet**](PassengerApi.md#getvehiclev1vehiclesvehicleidget) | **GET** /v1/vehicles/{vehicle_id} | Get Vehicle
[**listVehiclesV1VehiclesGet**](PassengerApi.md#listvehiclesv1vehiclesget) | **GET** /v1/vehicles | List Vehicles
[**planV1PlanGet**](PassengerApi.md#planv1planget) | **GET** /v1/plan | Plan
[**stopDeparturesV1StopsStopIdDeparturesGet**](PassengerApi.md#stopdeparturesv1stopsstopiddeparturesget) | **GET** /v1/stops/{stop_id}/departures | Stop Departures
[**tripForecastV1TripsTripIdForecastGet**](PassengerApi.md#tripforecastv1tripstripidforecastget) | **GET** /v1/trips/{trip_id}/forecast | Trip Forecast


# **getVehicleV1VehiclesVehicleIdGet**
> VehicleResponse getVehicleV1VehiclesVehicleIdGet(vehicleId)

Get Vehicle

Current state of one vehicle, with freshness (section 12.1).

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = PassengerApi();
final vehicleId = vehicleId_example; // String | 

try {
    final result = api_instance.getVehicleV1VehiclesVehicleIdGet(vehicleId);
    print(result);
} catch (e) {
    print('Exception when calling PassengerApi->getVehicleV1VehiclesVehicleIdGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **vehicleId** | **String**|  | 

### Return type

[**VehicleResponse**](VehicleResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listVehiclesV1VehiclesGet**
> FleetResponse listVehiclesV1VehiclesGet(bbox, limit)

List Vehicles

Fleet inside a viewport (section 29.2).

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = PassengerApi();
final bbox = bbox_example; // String | minLat,minLon,maxLat,maxLon
final limit = 56; // int | 

try {
    final result = api_instance.listVehiclesV1VehiclesGet(bbox, limit);
    print(result);
} catch (e) {
    print('Exception when calling PassengerApi->listVehiclesV1VehiclesGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bbox** | **String**| minLat,minLon,maxLat,maxLon | 
 **limit** | **int**|  | [optional] [default to 500]

### Return type

[**FleetResponse**](FleetResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **planV1PlanGet**
> PlanResponse planV1PlanGet(fromLat, fromLon, toLat, toLon, profile, windowMin)

Plan

Ranked journeys using *predicted* crowd, with a reason for each.  Routing itself is deterministic -- candidates come from the timetable, not from a model (section 5). The model only predicts the conditions each candidate will face, and the ranking is an explicit weighted cost so every option can say why it scored as it did.

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = PassengerApi();
final fromLat = 8.14; // num | 
final fromLon = 8.14; // num | 
final toLat = 8.14; // num | 
final toLon = 8.14; // num | 
final profile = profile_example; // String | 
final windowMin = 56; // int | 

try {
    final result = api_instance.planV1PlanGet(fromLat, fromLon, toLat, toLon, profile, windowMin);
    print(result);
} catch (e) {
    print('Exception when calling PassengerApi->planV1PlanGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **fromLat** | **num**|  | 
 **fromLon** | **num**|  | 
 **toLat** | **num**|  | 
 **toLon** | **num**|  | 
 **profile** | **String**|  | [optional] [default to 'balanced']
 **windowMin** | **int**|  | [optional] [default to 60]

### Return type

[**PlanResponse**](PlanResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **stopDeparturesV1StopsStopIdDeparturesGet**
> DeparturesResponse stopDeparturesV1StopsStopIdDeparturesGet(stopId, windowMin, limit)

Stop Departures

Upcoming scheduled departures from a stop.  Crowd fields are `UNKNOWN` until Slice B adds forecasting. They are present and explicitly unknown rather than omitted, so a client never has to infer that a missing field means an empty vehicle (section 12.4 rule 3).

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = PassengerApi();
final stopId = stopId_example; // String | 
final windowMin = 56; // int | 
final limit = 56; // int | 

try {
    final result = api_instance.stopDeparturesV1StopsStopIdDeparturesGet(stopId, windowMin, limit);
    print(result);
} catch (e) {
    print('Exception when calling PassengerApi->stopDeparturesV1StopsStopIdDeparturesGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **stopId** | **String**|  | 
 **windowMin** | **int**|  | [optional] [default to 60]
 **limit** | **int**|  | [optional] [default to 20]

### Return type

[**DeparturesResponse**](DeparturesResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **tripForecastV1TripsTripIdForecastGet**
> TripForecastResponse tripForecastV1TripsTripIdForecastGet(tripId)

Trip Forecast

Predicted crowd at each upcoming stop of a trip (section 12.1).  This is the product's core claim: not how full the bus is now, but how full it will be when it reaches the stop the passenger is waiting at.

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = PassengerApi();
final tripId = tripId_example; // String | 

try {
    final result = api_instance.tripForecastV1TripsTripIdForecastGet(tripId);
    print(result);
} catch (e) {
    print('Exception when calling PassengerApi->tripForecastV1TripsTripIdForecastGet: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tripId** | **String**|  | 

### Return type

[**TripForecastResponse**](TripForecastResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

