import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/models.dart';
import '../../../core/api/places.dart';
import '../../dashboard/providers/vehicle_provider.dart';

/// What the user asked for. Value equality matters: Riverpod caches on it, so
/// re-selecting the same profile does not re-issue the request.
class PlanQuery {
  const PlanQuery({
    required this.origin,
    required this.destination,
    required this.profile,
  });

  final DelhiPlace origin;
  final DelhiPlace destination;
  final PlanProfile profile;

  @override
  bool operator ==(Object other) =>
      other is PlanQuery &&
      other.origin.name == origin.name &&
      other.destination.name == destination.name &&
      other.profile == profile;

  @override
  int get hashCode => Object.hash(origin.name, destination.name, profile);
}

/// Ranked journeys from `GET /v1/plan`.
///
/// The ranking, the reason codes and the crowd forecast all come from the
/// server. The client sorts nothing and explains nothing on its own -- an
/// option's `reasons` are rendered verbatim (SOLUTION.md section 33.3 rule 3).
final planProvider =
    FutureProvider.family<PlanResponse, PlanQuery>((ref, query) async {
  final json = await ref.read(apiClientProvider).getJson(
    '/v1/plan',
    query: {
      'from_lat': query.origin.lat.toString(),
      'from_lon': query.origin.lon.toString(),
      'to_lat': query.destination.lat.toString(),
      'to_lon': query.destination.lon.toString(),
      'profile': query.profile.wire,
    },
  );
  return PlanResponse.fromJson(json);
});

/// Crowd forecast for every upcoming stop of a trip.
final tripForecastProvider =
    FutureProvider.family<TripForecast, String>((ref, tripId) async {
  final json =
      await ref.read(apiClientProvider).getJson('/v1/trips/$tripId/forecast');
  return TripForecast.fromJson(json);
});

/// Origin, destination and path for one trip, for the vehicle detail sheet.
final tripDetailProvider =
    FutureProvider.family<TripDetail, String>((ref, tripId) async {
  final json = await ref.read(apiClientProvider).getJson('/v1/trips/$tripId');
  return TripDetail.fromJson(json);
});
