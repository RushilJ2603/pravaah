# pravaah_api.model.DepartureView

## Load the model package
```dart
import 'package:pravaah_api/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tripId** | **String** |  | 
**routeId** | **String** |  | [optional] 
**directionId** | **int** |  | [optional] 
**scheduledDeparture** | [**DateTime**](DateTime.md) |  | 
**headsign** | **String** |  | [optional] 
**crowdClass** | [**OccupancyClass**](OccupancyClass.md) |  | [optional] [default to OccupancyClass.UNKNOWN]
**crowdP50** | **num** |  | [optional] 
**isForecast** | **bool** |  | [optional] [default to false]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


