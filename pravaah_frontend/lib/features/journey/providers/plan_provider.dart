import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

import '../../../core/api/places.dart';
import '../../../core/api_provider.dart';

enum PlanProfile {
  fastest('fastest', 'Fastest'),
  leastCrowded('least_crowded', 'Least crowded'),
  mostReliable('most_reliable', 'Most reliable'),
  balanced('balanced', 'Balanced');

  const PlanProfile(this.wire, this.label);
  final String wire;
  final String label;
}

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
  final api = ref.watch(passengerApiProvider);
  final response = await api.planV1PlanGet(
    query.origin.lat,
    query.origin.lon,
    query.destination.lat,
    query.destination.lon,
    profile: query.profile.wire,
  );
  if (response == null) {
    throw ApiException(0, 'Empty response from /v1/plan');
  }
  return response;
});
