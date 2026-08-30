import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../data/models.dart';

final vehicleProvider = FutureProvider.family<VehiclesResponse, String>((ref, bbox) async {
  // Use 10.0.2.2 for Android Emulator, localhost for Web/iOS Simulator.
  // We'll use localhost since the demo environment handles web well.
  final uri = Uri.parse('http://localhost:8000/v1/vehicles?bbox=$bbox&limit=500');
  final response = await http.get(uri);

  if (response.statusCode == 200) {
    return VehiclesResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  } else {
    // Attempt to parse the API error shape from docs/FRONTEND_HANDOFF.md
    try {
      final errMap = jsonDecode(response.body) as Map<String, dynamic>;
      throw Exception(errMap['error']?['message'] ?? 'API Error');
    } catch (_) {
      throw Exception('Failed to load vehicles: ${response.statusCode}');
    }
  }
});
