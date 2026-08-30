import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/models.dart';
import '../../../core/api/session.dart';
import '../../dashboard/providers/vehicle_provider.dart';

/// Drives one conductor's shift.
///
/// The shift is the whole point: it binds this device to a vehicle and a trip.
/// The backend rejects any position report without an active shift, because a
/// GPS point that cannot be joined to a trip is useless to everything
/// downstream.
class ConductorController extends StateNotifier<AsyncValue<Shift?>> {
  ConductorController(this._ref) : super(const AsyncValue.data(null));

  final Ref _ref;

  ApiClient get _client => _ref.read(apiClientProvider);

  String get _token {
    final token = _ref.read(tokenProvider);
    if (token == null) throw ApiException('UNAUTHORIZED', 'Not signed in');
    return token;
  }

  Future<void> startShift({
    required String vehicleId,
    required String deviceId,
    String? routeId,
  }) async {
    state = const AsyncValue.loading();
    try {
      final json = await _client.postJson(
        '/v1/shifts/start',
        {
          'vehicle_id': vehicleId,
          'device_id': deviceId,
          if (routeId != null && routeId.isNotEmpty) 'route_id': routeId,
        },
        bearerToken: _token,
      );
      state = AsyncValue.data(Shift.fromJson(json, vehicleId, routeId));
    } catch (error, stack) {
      // VEHICLE_ALREADY_CLAIMED lands here: another crew member already has
      // this bus. That is a real operational case, not a bug.
      state = AsyncValue.error(error, stack);
    }
  }

  Future<void> endShift() async {
    final shift = state.valueOrNull;
    if (shift == null) return;
    await _client.postJson(
      '/v1/shifts/${shift.shiftId}/end',
      const {},
      bearerToken: _token,
    );
    state = const AsyncValue.data(null);
  }

  /// Report where the bus is. Timestamps must be recent: the backend refuses
  /// anything in the future or older than the city's staleness window.
  Future<void> reportPosition({
    required double lat,
    required double lon,
    double accuracyM = 10.0,
  }) async {
    final shift = state.valueOrNull;
    if (shift == null) throw ApiException('SHIFT_NOT_ACTIVE', 'No active shift');
    await _client.postJson(
      '/v1/shifts/${shift.shiftId}/position',
      {
        'lat': lat,
        'lon': lon,
        'accuracy_m': accuracyM,
        'timestamp': DateTime.now().toUtc().toIso8601String(),
      },
      bearerToken: _token,
    );
  }

  /// The crowd tap. Stored at the conductor trust tier because the caller is
  /// authenticated staff -- the tier comes from the credential, never the URL.
  Future<void> reportOccupancy(CrowdLevel level) async {
    final shift = state.valueOrNull;
    if (shift == null) throw ApiException('SHIFT_NOT_ACTIVE', 'No active shift');
    await _client.postJson(
      '/v1/occupancy/report',
      {
        'vehicle_id': shift.vehicleId,
        'occupancy_class': level.wire,
        'reported_at': DateTime.now().toUtc().toIso8601String(),
      },
      bearerToken: _token,
    );
  }
}

final conductorProvider =
    StateNotifierProvider<ConductorController, AsyncValue<Shift?>>(
  (ref) => ConductorController(ref),
);

/// The four levels a conductor can tap. Deliberately not the full eight-member
/// ladder: a person glancing down a bus can tell these apart, and offering
/// finer distinctions would invite false precision.
const List<CrowdLevel> kConductorLevels = [
  CrowdLevel.manySeats,
  CrowdLevel.fewSeats,
  CrowdLevel.standing,
  CrowdLevel.full,
];
