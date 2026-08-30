import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

import '../../../core/api/session.dart';
import '../../../core/api_provider.dart';
import '../../dashboard/providers/vehicle_provider.dart';

/// Every operator endpoint is gated behind `require_operator`, so each of these
/// reads the token first. Watching `tokenProvider` rather than reading it means
/// signing out invalidates all of them automatically.
String _requireToken(Ref ref) {
  final token = ref.watch(tokenProvider);
  if (token == null) {
    throw ApiException(401, '{"code":"UNAUTHORIZED","message":"Not signed in"}');
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
  _requireToken(ref);
  final api = ref.watch(operatorApiProvider);
  final response =
      await api.hotspotsV1AdminHotspotsGet(horizonMin: horizonMin, limit: 20);
  if (response == null) {
    throw ApiException(0, 'Empty response from /v1/admin/hotspots');
  }
  return response;
});

/// Feed freshness and coverage. Stale by definition if it is not re-read.
final dataHealthProvider =
    FutureProvider.autoDispose<DataHealthResponse>((ref) async {
  pollEvery(ref, const Duration(seconds: 10));
  _requireToken(ref);
  final api = ref.watch(operatorApiProvider);
  final response = await api.dataHealthV1AdminDataHealthGet();
  if (response == null) {
    throw ApiException(0, 'Empty response from /v1/admin/data-health');
  }
  return response;
});

/// The whole fleet. This is the one endpoint allowed to skip a viewport --
/// an operator sees the network, a passenger sees their surroundings.
final fleetProvider = FutureProvider.autoDispose<FleetResponse>((ref) async {
  pollEvery(ref, const Duration(seconds: 5));
  _requireToken(ref);
  final api = ref.watch(operatorApiProvider);
  final response = await api.adminVehiclesV1AdminVehiclesGet(limit: 500);
  if (response == null) {
    throw ApiException(0, 'Empty response from /v1/admin/vehicles');
  }
  return response;
});

/// Hour-by-hour predicted load for one route. Not polled: the horizon is
/// twelve hours, so re-reading it on a timer would buy nothing.
final routeForecastProvider =
    FutureProvider.family<List<RouteHourForecast>, String>((ref, routeId) async {
  _requireToken(ref);
  final api = ref.watch(operatorApiProvider);
  final response = await api.routeForecastV1AdminRoutesRouteIdForecastGet(
    routeId,
    hours: 12,
  );
  return response?.hours ?? const [];
});
