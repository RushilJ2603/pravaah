import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

import '../api_provider.dart';

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
  SessionController(this._ref) : super(null);

  final Ref _ref;

  /// Exchange credentials for a short-lived bearer token.
  ///
  /// Throws [ApiException] with code `UNAUTHORIZED` on bad credentials, which
  /// the sign-in form renders directly.
  Future<void> signIn(String username, String password) async {
    final api = _ref.read(staffAuthApiProvider);
    final response = await api.loginV1AuthLoginPost(
      LoginRequest(username: username, password: password),
    );
    if (response == null) {
      throw ApiException(0, 'Empty response from /v1/auth/login');
    }
    _ref.read(bearerAuthProvider).accessToken = response.accessToken;
    state = StaffSession(token: response.accessToken, role: response.role);
  }

  void signOut() {
    // The setter rejects null; empty clears the header instead.
    _ref.read(bearerAuthProvider).accessToken = '';
    state = null;
  }
}

final sessionProvider =
    StateNotifierProvider<SessionController, StaffSession?>((ref) {
  return SessionController(ref);
});

/// The bearer token, or null when nobody is signed in.
final tokenProvider = Provider<String?>((ref) => ref.watch(sessionProvider)?.token);
