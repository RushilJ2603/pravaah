# pravaah_api.model.VehicleView

## Load the model package
```dart
import 'package:pravaah_api/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**vehicleId** | **String** |  | 
**tripId** | **String** |  | [optional] 
**routeId** | **String** |  | [optional] 
**directionId** | **int** |  | [optional] 
**lat** | **num** |  | 
**lon** | **num** |  | 
**bearing** | **num** |  | [optional] 
**speedMps** | **num** |  | [optional] 
**stopId** | **String** |  | [optional] 
**currentStatus** | [**VehicleStopStatus**](VehicleStopStatus.md) |  | [optional] 
**occupancyClass** | [**OccupancyClass**](OccupancyClass.md) |  | [optional] [default to OccupancyClass.UNKNOWN]
**occupancyRatio** | **num** |  | [optional] 
**ts** | [**DateTime**](DateTime.md) |  | 
**ageS** | **int** |  | 
**isStale** | **bool** |  | 
**sourceType** | [**SourceType**](SourceType.md) |  | 
**qualityScore** | **num** |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


