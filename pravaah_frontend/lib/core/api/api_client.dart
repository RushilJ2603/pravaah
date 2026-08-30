import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;

import 'package:http/http.dart' as http;

import 'api_config.dart';

/// A failure the UI can actually explain to a passenger.
///
/// The backend returns exactly one error shape for every failure:
///
///   {"error": {"code": "FEED_UNAVAILABLE", "message": "...", "request_id": "..."}}
///
/// so the code travels with the exception and screens can branch on it instead
/// of pattern-matching English strings.
class ApiException implements Exception {
  ApiException(this.code, this.message, {this.status});

  final String code;
  final String message;
  final int? status;

  /// True when the failure is the network or the server being unreachable,
  /// rather than the request being wrong. These are the ones worth a retry.
  bool get isTransient =>
      code == 'NETWORK' ||
      code == 'TIMEOUT' ||
      code == 'FEED_UNAVAILABLE' ||
      (status != null && status! >= 500);

  /// Wording safe to put in front of a passenger.
  String get friendlyMessage {
    switch (code) {
      case 'NETWORK':
        return 'Cannot reach the PRAVAAH server. Check that the backend is '
            'running and that this device can see it.';
      case 'TIMEOUT':
        return 'The server took too long to respond.';
      case 'FEED_UNAVAILABLE':
        return 'Live data is temporarily unavailable.';
      case 'NO_ROUTE_FOUND':
        return 'No service found for that journey in the next hour.';
      case 'OUT_OF_SERVICE_AREA':
        return 'That location is outside the covered area.';
      case 'INVALID_COORDINATES':
        return 'That location could not be understood.';
      case 'UNAUTHORIZED':
        return 'Please sign in again.';
      case 'FORBIDDEN':
        return 'This account cannot do that.';
      case 'RATE_LIMITED':
        return 'Too many requests. Try again shortly.';
      default:
        return message.isNotEmpty ? message : 'Something went wrong.';
    }
  }

  @override
  String toString() => 'ApiException($code${status != null ? ' $status' : ''}): $message';
}

/// Thin wrapper over `http` that centralises the base URL, timeouts and the
/// backend's single error contract.
class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<Map<String, dynamic>> getJson(
    String path, {
    Map<String, String>? query,
    String? bearerToken,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path')
        .replace(queryParameters: query);
    try {
      final response = await _client
          .get(uri, headers: _headers(bearerToken))
          .timeout(ApiConfig.timeout);
      return _decode(response);
    } on TimeoutException {
      throw ApiException('TIMEOUT', 'Request timed out after '
          '${ApiConfig.timeout.inSeconds}s');
    } on SocketException catch (e) {
      throw ApiException('NETWORK', e.message);
    } on http.ClientException catch (e) {
      // Flutter web surfaces CORS and connection refusals as ClientException.
      throw ApiException('NETWORK', e.message);
    }
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body, {
    String? bearerToken,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    try {
      final response = await _client
          .post(uri, headers: _headers(bearerToken), body: jsonEncode(body))
          .timeout(ApiConfig.timeout);
      return _decode(response);
    } on TimeoutException {
      throw ApiException('TIMEOUT', 'Request timed out');
    } on SocketException catch (e) {
      throw ApiException('NETWORK', e.message);
    } on http.ClientException catch (e) {
      throw ApiException('NETWORK', e.message);
    }
  }

  Map<String, String> _headers(String? bearerToken) => {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        if (bearerToken != null) 'Authorization': 'Bearer $bearerToken',
      };

  Map<String, dynamic> _decode(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return const {};
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    // Every backend failure uses the same envelope; fall back gracefully if a
    // proxy or tunnel returns something else entirely (an HTML error page).
    try {
      final decoded = jsonDecode(response.body) as Map<String, dynamic>;
      final error = decoded['error'] as Map<String, dynamic>?;
      throw ApiException(
        (error?['code'] as String?) ?? 'INTERNAL',
        (error?['message'] as String?) ?? 'Request failed',
        status: response.statusCode,
      );
    } on ApiException {
      rethrow;
    } catch (_) {
      throw ApiException('INTERNAL', 'Unexpected response from server',
          status: response.statusCode);
    }
  }

  void close() => _client.close();
}
