import 'package:flutter/material.dart';
import 'package:pravaah_api/api.dart';

/// Convenience getters the generated [JourneyOption]/[CrowdBand] models don't
/// carry themselves -- they come straight off the wire, so anything derived
/// lives here instead of a hand-maintained model class.
extension JourneyOptionDisplay on JourneyOption {
  String get routeLabel => legs.isNotEmpty ? 'Route ${legs.first.routeId}' : 'Walk';

  CrowdBand? get boardingCrowd => legs.isNotEmpty ? legs.first.crowd : null;
}

extension CrowdBandDisplay on CrowdBand {
  /// Section 33.3 rule 2: an unknown forecast still renders, it just says so.
  bool get isKnown => p50Class != OccupancyClass.UNKNOWN;

  String get summary => occupancyLabel(p50Class);
}

String occupancyLabel(OccupancyClass level) {
  switch (level) {
    case OccupancyClass.EMPTY:
    case OccupancyClass.MANY_SEATS_AVAILABLE:
      return 'Seats available';
    case OccupancyClass.FEW_SEATS_AVAILABLE:
      return 'Few seats left';
    case OccupancyClass.STANDING_ROOM_ONLY:
      return 'Standing room only';
    case OccupancyClass.CRUSHED_STANDING_ROOM_ONLY:
      return 'Crush load';
    case OccupancyClass.FULL:
      return 'Full';
    case OccupancyClass.NOT_ACCEPTING_PASSENGERS:
      return 'Not accepting passengers';
    case OccupancyClass.UNKNOWN:
      return 'Unknown';
  }
}

/// Crowding is never conveyed by colour alone (section 33.5) -- this backs a
/// coloured chip that always carries [occupancyLabel] as text alongside it.
Color occupancyColour(OccupancyClass level) {
  switch (level) {
    case OccupancyClass.EMPTY:
    case OccupancyClass.MANY_SEATS_AVAILABLE:
      return const Color(0xFF2E7D32);
    case OccupancyClass.FEW_SEATS_AVAILABLE:
      return const Color(0xFF9E7B00);
    case OccupancyClass.STANDING_ROOM_ONLY:
      return const Color(0xFFD84315);
    case OccupancyClass.CRUSHED_STANDING_ROOM_ONLY:
    case OccupancyClass.FULL:
    case OccupancyClass.NOT_ACCEPTING_PASSENGERS:
      return const Color(0xFFB71C1C);
    case OccupancyClass.UNKNOWN:
      // Unknown is neutral grey. It must never look like "empty".
      return const Color(0xFF6B7280);
  }
}
