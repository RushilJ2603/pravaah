import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';
import '../../../core/api_provider.dart';

final vehicleProvider = FutureProvider.family<FleetResponse, String>((ref, bbox) async {
  final api = ref.watch(passengerApiProvider);
  
  final response = await api.listVehiclesV1VehiclesGet(bbox, limit: 500);
  
  if (response != null) {
    return response;
  } else {
    throw Exception('Failed to load vehicles or received empty response');
  }
});
