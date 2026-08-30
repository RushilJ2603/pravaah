import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/models.dart';
import '../../../core/api/session.dart';
import '../../dashboard/data/models.dart';
import '../../dashboard/providers/vehicle_provider.dart';

/// Every operator endpoint is gated behind `require_operator`, so each of these
/// reads the token first. Watching `tokenProvider` rather than reading it means
/// signing out invalidates all of them automatically.
String _requireToken(Ref ref) {
  final token = ref.watch(tokenProvider);
  if (token == null) {
    throw ApiException('UNAUTHORIZED', 'Not signed in');
  }
  return token;
}

/// Predicted crowding hotspots, ranked by severity then urgency.
///
/// Polled slower than the fleet: this is a forecast over a horizon, so it moves
/// on the order of minutes, not seconds.
final hotspotsProvider = FutureProvider.autoDispose
    .family<HotspotsResponse, int>((ref, horizonMin) async {
  pollEvery(ref, const Duration(seconds: 30));
  final json = await ref.read(apiClientProvider).getJson(
        '/v1/admin/hotspots',
        query: {'horizon_min': '$horizonMin', 'limit': '20'},
        bearerToken: _requireToken(ref),
      );
  return HotspotsResponse.fromJson(json);
});

/// Feed freshness and coverage. Stale by definition if it is not re-read.
final dataHealthProvider = FutureProvider.autoDispose<DataHealth>((ref) async {
  pollEvery(ref, const Duration(seconds: 10));
  final json = await ref.read(apiClientProvider).getJson(
        '/v1/admin/data-health',
        bearerToken: _requireToken(ref),
      );
  return DataHealth.fromJson(json);
});

/// The whole fleet. This is the one endpoint allowed to skip a viewport --
/// an operator sees the network, a passenger sees their surroundings.
final fleetProvider =
    FutureProvider.autoDispose<VehiclesResponse>((ref) async {
  pollEvery(ref, const Duration(seconds: 5));
  final json = await ref.read(apiClientProvider).getJson(
        '/v1/admin/vehicles',
        query: {'limit': '500'},
        bearerToken: _requireToken(ref),
      );
  return VehiclesResponse.fromJson(json);
});

/// Hour-by-hour predicted load for one route. Not polled: the horizon is
/// twelve hours, so re-reading it on a timer would buy nothing.
final routeForecastProvider =
    FutureProvider.family<List<RouteHourForecast>, String>((ref, routeId) async {
  final json = await ref.read(apiClientProvider).getJson(
        '/v1/admin/routes/$routeId/forecast',
        query: {'hours': '12'},
        bearerToken: _requireToken(ref),
      );
  return ((json['hours'] as List?) ?? const [])
      .map((h) => RouteHourForecast.fromJson(h as Map<String, dynamic>))
      .toList();
});
