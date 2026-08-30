import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../data/models.dart';

/// One client for the whole app, disposed with the container.
final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ApiClient();
  ref.onDispose(client.close);
  return client;
});

/// Re-run the calling provider every [interval] for as long as it is watched.
///
/// The live endpoints return snapshots, not streams. Without this a screen
/// renders whatever the first fetch happened to see and never moves again,
/// even though the fleet reports new positions every few seconds.
void pollEvery(Ref ref, Duration interval) {
  final timer = Timer(interval, ref.invalidateSelf);
  ref.onDispose(timer.cancel);
}

/// Live vehicles inside a viewport.
///
/// `bbox` is required by the API by design -- there is no fetch-everything
/// call, so a city-wide payload is not reachable by accident.
final vehicleProvider = FutureProvider.autoDispose
    .family<VehiclesResponse, String>((ref, bbox) async {
  pollEvery(ref, const Duration(seconds: 5));
  final json = await ref.read(apiClientProvider).getJson(
    '/v1/vehicles',
    query: {'bbox': bbox, 'limit': '500'},
  );
  return VehiclesResponse.fromJson(json);
});
