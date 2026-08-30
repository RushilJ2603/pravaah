import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

/// Filled in by staff sign-in (`session.dart`); empty means no bearer token
/// is sent. One instance for the app's lifetime so every API client shares it.
final bearerAuthProvider = Provider<HttpBearerAuth>((ref) => HttpBearerAuth());

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(
    basePath: 'https://strict-affiliation-ranked-gates.trycloudflare.com',
    authentication: ref.watch(bearerAuthProvider),
  );
});

final passengerApiProvider = Provider<PassengerApi>((ref) {
  return PassengerApi(ref.watch(apiClientProvider));
});

final staffAuthApiProvider = Provider<StaffAuthApi>((ref) {
  return StaffAuthApi(ref.watch(apiClientProvider));
});

final conductorApiProvider = Provider<ConductorApi>((ref) {
  return ConductorApi(ref.watch(apiClientProvider));
});

final operatorApiProvider = Provider<OperatorApi>((ref) {
  return OperatorApi(ref.watch(apiClientProvider));
});
