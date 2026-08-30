# pravaah_api.api.StaffAuthApi

## Load the API package
```dart
import 'package:pravaah_api/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**loginV1AuthLoginPost**](StaffAuthApi.md#loginv1authloginpost) | **POST** /v1/auth/login | Login


# **loginV1AuthLoginPost**
> LoginResponse loginV1AuthLoginPost(loginRequest)

Login

Exchange an out-of-band staff credential for a short-lived token.

### Example
```dart
import 'package:pravaah_api/api.dart';

final api_instance = StaffAuthApi();
final loginRequest = LoginRequest(); // LoginRequest | 

try {
    final result = api_instance.loginV1AuthLoginPost(loginRequest);
    print(result);
} catch (e) {
    print('Exception when calling StaffAuthApi->loginV1AuthLoginPost: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **loginRequest** | [**LoginRequest**](LoginRequest.md)|  | 

### Return type

[**LoginResponse**](LoginResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

