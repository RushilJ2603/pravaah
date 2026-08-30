import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/dashboard/providers/vehicle_provider.dart';
import 'api_client.dart';

/// Who is signed in, if anyone.
///
/// Passengers are anonymous by design -- there is no sign-up path and the
/// passenger endpoints take no credentials. Only staff authenticate, and the
/// backend decides what a token may do from the role baked into it, never from
/// anything this client claims.
class StaffSession {
  const StaffSession({required this.token, required this.role});

  final String token;
  final String role;

  bool get isOperator => role == 'OPERATOR';
  bool get isConductor => role == 'CONDUCTOR';
}

class SessionController extends StateNotifier<StaffSession?> {
  SessionController(this._client) : super(null);

  final ApiClient _client;

  /// Exchange credentials for a short-lived bearer token.
  ///
  /// Throws [ApiException] with code `UNAUTHORIZED` on bad credentials, which
  /// the sign-in form renders directly.
  Future<void> signIn(String username, String password) async {
    final json = await _client.postJson('/v1/auth/login', {
      'username': username,
      'password': password,
    });
    state = StaffSession(
      token: json['access_token'] as String,
      role: json['role'] as String,
    );
  }

  void signOut() => state = null;
}

final sessionProvider =
    StateNotifierProvider<SessionController, StaffSession?>((ref) {
  return SessionController(ref.read(apiClientProvider));
});

/// The bearer token, or null when nobody is signed in.
final tokenProvider = Provider<String?>((ref) => ref.watch(sessionProvider)?.token);
