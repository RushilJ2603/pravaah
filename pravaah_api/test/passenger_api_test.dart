//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.18

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

import 'package:pravaah_api/api.dart';
import 'package:test/test.dart';


/// tests for PassengerApi
void main() {
  // final instance = PassengerApi();

  group('tests for PassengerApi', () {
    // Get Vehicle
    //
    // Current state of one vehicle, with freshness (section 12.1).
    //
    //Future<VehicleResponse> getVehicleV1VehiclesVehicleIdGet(String vehicleId) async
    test('test getVehicleV1VehiclesVehicleIdGet', () async {
      // TODO
    });

    // List Vehicles
    //
    // Fleet inside a viewport (section 29.2).
    //
    //Future<FleetResponse> listVehiclesV1VehiclesGet(String bbox, { int limit }) async
    test('test listVehiclesV1VehiclesGet', () async {
      // TODO
    });

    // Plan
    //
    // Ranked journeys using *predicted* crowd, with a reason for each.  Routing itself is deterministic -- candidates come from the timetable, not from a model (section 5). The model only predicts the conditions each candidate will face, and the ranking is an explicit weighted cost so every option can say why it scored as it did.
    //
    //Future<PlanResponse> planV1PlanGet(num fromLat, num fromLon, num toLat, num toLon, { String profile, int windowMin }) async
    test('test planV1PlanGet', () async {
      // TODO
    });

    // Stop Departures
    //
    // Upcoming scheduled departures from a stop.  Crowd fields are `UNKNOWN` until Slice B adds forecasting. They are present and explicitly unknown rather than omitted, so a client never has to infer that a missing field means an empty vehicle (section 12.4 rule 3).
    //
    //Future<DeparturesResponse> stopDeparturesV1StopsStopIdDeparturesGet(String stopId, { int windowMin, int limit }) async
    test('test stopDeparturesV1StopsStopIdDeparturesGet', () async {
      // TODO
    });

    // Trip Forecast
    //
    // Predicted crowd at each upcoming stop of a trip (section 12.1).  This is the product's core claim: not how full the bus is now, but how full it will be when it reaches the stop the passenger is waiting at.
    //
    //Future<TripForecastResponse> tripForecastV1TripsTripIdForecastGet(String tripId) async
    test('test tripForecastV1TripsTripIdForecastGet', () async {
      // TODO
    });

  });
}
