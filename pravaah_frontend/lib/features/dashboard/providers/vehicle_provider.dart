import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../data/models.dart';

/// One client for the whole app, disposed with the container.
final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ApiClient();
  ref.onDispose(client.close);
  return client;
});

/// Live vehicles inside a viewport.
///
/// `bbox` is required by the API by design -- there is no fetch-everything
/// call, so a city-wide payload is not reachable by accident.
final vehicleProvider =
    FutureProvider.family<VehiclesResponse, String>((ref, bbox) async {
  final json = await ref.read(apiClientProvider).getJson(
    '/v1/vehicles',
    query: {'bbox': bbox, 'limit': '500'},
  );
  return VehiclesResponse.fromJson(json);
});
