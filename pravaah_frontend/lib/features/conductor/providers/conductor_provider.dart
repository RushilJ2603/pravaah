import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';

import '../../../core/api/session.dart';
import '../../../core/api_provider.dart';

/// The four levels a conductor can tap, mapped onto the generated occupancy
/// ladder. Deliberately not the full eight-member ladder: a person glancing
/// down a bus can tell these apart, and offering finer distinctions would
/// invite false precision.
enum CrowdLevel {
  manySeats(OccupancyClass.MANY_SEATS_AVAILABLE, 'Many seats'),
  fewSeats(OccupancyClass.FEW_SEATS_AVAILABLE, 'Few seats'),
  standing(OccupancyClass.STANDING_ROOM_ONLY, 'Standing room'),
  full(OccupancyClass.CRUSHED_STANDING_ROOM_ONLY, 'Crush load');

  const CrowdLevel(this.wire, this.label);
  final OccupancyClass wire;
  final String label;
}

const List<CrowdLevel> kConductorLevels = [
  CrowdLevel.manySeats,
  CrowdLevel.fewSeats,
  CrowdLevel.standing,
  CrowdLevel.full,
];

/// `POST /v1/shifts/start` returns only `shiftId`/`startedAt`; the vehicle and
/// route the conductor bound are only known client-side, from the request.
class Shift {
  const Shift({required this.shiftId, required this.vehicleId, this.routeId});

  final int shiftId;
  final String vehicleId;
  final String? routeId;
}

/// Drives one conductor's shift.
///
/// The shift is the whole point: it binds this device to a vehicle and a trip.
/// The backend rejects any position report without an active shift, because a
/// GPS point that cannot be joined to a trip is useless to everything
/// downstream.
class ConductorController extends StateNotifier<AsyncValue<Shift?>> {
  ConductorController(this._ref) : super(const AsyncValue.data(null));

  final Ref _ref;

  ConductorApi get _api => _ref.read(conductorApiProvider);

  void _requireSignedIn() {
    if (_ref.read(tokenProvider) == null) {
      throw ApiException(401, '{"code":"UNAUTHORIZED","message":"Not signed in"}');
    }
  }

  Future<void> startShift({
    required String vehicleId,
    required String deviceId,
    String? routeId,
  }) async {
    state = const AsyncValue.loading();
    try {
      _requireSignedIn();
      final response = await _api.startShiftV1ShiftsStartPost(
        ShiftStartRequest(
          vehicleId: vehicleId,
          deviceId: deviceId,
          routeId: routeId != null && routeId.isNotEmpty ? routeId : null,
        ),
      );
      if (response == null) {
        throw ApiException(0, 'Empty response from /v1/shifts/start');
      }
      state = AsyncValue.data(
        Shift(shiftId: response.shiftId, vehicleId: vehicleId, routeId: routeId),
      );
    } catch (error, stack) {
      // VEHICLE_ALREADY_CLAIMED lands here: another crew member already has
      // this bus. That is a real operational case, not a bug.
      state = AsyncValue.error(error, stack);
    }
  }

  Future<void> endShift() async {
    final shift = state.valueOrNull;
    if (shift == null) return;
    _requireSignedIn();
    await _api.endShiftV1ShiftsShiftIdEndPost(shift.shiftId);
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
    if (shift == null) {
      throw ApiException(409, '{"code":"SHIFT_NOT_ACTIVE","message":"No active shift"}');
    }
    _requireSignedIn();
    await _api.reportPositionV1ShiftsShiftIdPositionPost(
      shift.shiftId,
      ShiftPositionRequest(
        lat: lat,
        lon: lon,
        accuracyM: accuracyM,
        timestamp: DateTime.now().toUtc(),
      ),
    );
  }

  /// The crowd tap. Stored at the conductor trust tier because the caller is
  /// authenticated staff -- the tier comes from the credential, never the URL.
  Future<void> reportOccupancy(CrowdLevel level) async {
    final shift = state.valueOrNull;
    if (shift == null) {
      throw ApiException(409, '{"code":"SHIFT_NOT_ACTIVE","message":"No active shift"}');
    }
    _requireSignedIn();
    await _api.reportOccupancyV1OccupancyReportPost(
      OccupancyReportRequest(
        vehicleId: shift.vehicleId,
        occupancyClass: level.wire,
        reportedAt: DateTime.now().toUtc(),
      ),
    );
  }
}

final conductorProvider =
    StateNotifierProvider<ConductorController, AsyncValue<Shift?>>(
  (ref) => ConductorController(ref),
);
