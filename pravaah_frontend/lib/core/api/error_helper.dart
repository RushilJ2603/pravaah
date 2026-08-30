import 'dart:convert';

import 'package:pravaah_api/api.dart';

/// The backend's machine-readable error code, when the body is JSON shaped
/// like `{"code": "...", "message": "..."}`. Null if the body isn't JSON or
/// carries no code (e.g. a raw network failure never reached the backend).
extension ApiExceptionCode on ApiException {
  String? get errorCode {
    final body = message;
    if (body == null) return null;
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map && decoded['code'] is String) {
        return decoded['code'] as String;
      }
    } catch (_) {
      // Not JSON -- a raw network/transport failure, most likely.
    }
    return null;
  }

  /// Wording safe to put in front of a passenger or staff user.
  String get friendlyMessage {
    switch (errorCode) {
      case 'UNAUTHORIZED':
        return 'Please sign in again.';
      case 'FORBIDDEN':
        return 'This account cannot do that.';
      case 'VEHICLE_ALREADY_CLAIMED':
        return 'Another crew member already has this bus on shift.';
      case 'SHIFT_NOT_ACTIVE':
        return 'Start a shift before doing that.';
      case 'NO_ROUTE_FOUND':
        return 'No service found for that journey in the next hour.';
      case 'OUT_OF_SERVICE_AREA':
        return 'That location is outside the covered area.';
      case 'INVALID_COORDINATES':
        return 'That location could not be understood.';
      case 'RATE_LIMITED':
        return 'Too many requests. Try again shortly.';
      case 'FEED_UNAVAILABLE':
        return 'Live data is temporarily unavailable.';
    }
    if (code == 0) {
      return 'Cannot reach the PRAVAAH server. Check that the backend is '
          'running and that this device can see it.';
    }
    if (code == 401) return 'Please sign in again.';
    if (code == 403) return 'This account cannot do that.';
    if (code >= 500) return 'The server is having trouble. Try again shortly.';
    return message ?? 'Could not complete this request.';
  }
}
