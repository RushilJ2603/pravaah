import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';
import '../../../core/api_provider.dart';

/// Re-run the calling provider every [interval] for as long as it is watched.
///
/// The live endpoints return snapshots, not streams. Without this a screen
/// renders whatever the first fetch happened to see and never moves again,
/// even though the fleet reports new positions every few seconds.
void pollEvery(Ref ref, Duration interval) {
  final timer = Timer(interval, ref.invalidateSelf);
  ref.onDispose(timer.cancel);
}

final vehicleProvider = FutureProvider.autoDispose
    .family<FleetResponse, String>((ref, bbox) async {
  pollEvery(ref, const Duration(seconds: 5));
  final api = ref.watch(passengerApiProvider);

  final response = await api.listVehiclesV1VehiclesGet(bbox, limit: 500);

  if (response != null) {
    return response;
  } else {
    throw Exception('Failed to load vehicles or received empty response');
  }
});
