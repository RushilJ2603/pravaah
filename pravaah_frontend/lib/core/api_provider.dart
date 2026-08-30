import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(basePath: 'https://strict-affiliation-ranked-gates.trycloudflare.com');
});

final passengerApiProvider = Provider<PassengerApi>((ref) {
  return PassengerApi(ref.watch(apiClientProvider));
});
