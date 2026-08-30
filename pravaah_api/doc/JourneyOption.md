# pravaah_api.model.JourneyOption

## Load the model package
```dart
import 'package:pravaah_api/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**optionId** | **String** |  | 
**totalMinutes** | **int** |  | 
**transfers** | **int** |  | 
**departure** | [**DateTime**](DateTime.md) |  | 
**arrival** | [**DateTime**](DateTime.md) |  | 
**legs** | [**List<JourneyLeg>**](JourneyLeg.md) |  | [default to const []]
**score** | **num** |  | 
**reasons** | **List<String>** |  | [default to const []]
**isRecommended** | **bool** |  | [optional] [default to false]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


