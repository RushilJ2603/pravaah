# pravaah_api.api.OpsApi

## Load the API package
```dart
import 'package:pravaah_api/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**healthV1HealthGet**](OpsApi.md#healthv1healthget) | **GET** /v1/health | Health


# **healthV1HealthGet**
> HealthResponse healthV1HealthGet()

Health

Dependency reachability, for the deployment runbook (section 14.4).  Reports `degraded` rather than failing when a dependency is down: section 16.1 requires the system to degrade visibly, and an endpoint that returns 500 cannot say which dependency is at fault.

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = OpsApi();

try {
    final result = api_instance.healthV1HealthGet();
    print(result);
} catch (e) {
    print('Exception when calling OpsApi->healthV1HealthGet: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**HealthResponse**](HealthResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

