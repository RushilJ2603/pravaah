import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../../providers/vehicle_provider.dart';
import '../../../../theme/app_theme.dart';
import '../../data/models.dart';
import '../../../../core/api/api_client.dart';
import '../../../../core/api/models.dart' as api;
import '../../../journey/providers/plan_provider.dart';

class MiniLiveMap extends ConsumerStatefulWidget {
  const MiniLiveMap({super.key});

  @override
  ConsumerState<MiniLiveMap> createState() => _MiniLiveMapState();
}

class _MiniLiveMapState extends ConsumerState<MiniLiveMap> {
  final MapController _mapController = MapController();
  final String _currentBbox = "28.40,76.80,28.90,77.50";

  /// Trip of the tapped bus. Drives both the highlighted path and the sheet.
  String? _selectedTripId;
  
  Position? _currentPosition;
  bool _isLoadingLocation = false;

  @override
  void initState() {
    super.initState();
    _determinePosition();
  }

  Future<void> _determinePosition() async {
    setState(() {
      _isLoadingLocation = true;
    });

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        throw Exception('Location services are disabled.');
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          throw Exception('Location permissions are denied');
        }
      }

      if (permission == LocationPermission.deniedForever) {
        throw Exception('Location permissions are permanently denied.');
      }

      Position position = await Geolocator.getCurrentPosition();
      setState(() {
        _currentPosition = position;
      });
      
      // Move map to the user's live location
      _mapController.move(LatLng(position.latitude, position.longitude), 14.0);
      
    } catch (e) {
      debugPrint("Location error: $e");
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingLocation = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final vehicleAsyncValue = ref.watch(vehicleProvider(_currentBbox));

    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: SizedBox(
        height: 380,
        child: Stack(
          children: [
            FlutterMap(
              mapController: _mapController,
              options: const MapOptions(
                initialCenter: LatLng(28.6139, 77.2090), // Default New Delhi
                initialZoom: 13.0,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.pravaah.app',
                ),
                vehicleAsyncValue.when(
                  data: (response) => MarkerLayer(
                    markers: response.vehicles.map((v) => _buildMarker(v)).toList(),
                  ),
                  loading: () => const MarkerLayer(markers: []),
                  error: (e, stack) => const MarkerLayer(markers: []),
                ),
                // Path of the tapped bus, under the markers.
                _buildSelectedPath(),
                // Blue Dot for User Location
                if (_currentPosition != null)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: LatLng(_currentPosition!.latitude, _currentPosition!.longitude),
                        width: 24,
                        height: 24,
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.blue,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.white, width: 3),
                            boxShadow: const [
                              BoxShadow(color: Colors.black38, blurRadius: 4, offset: Offset(0, 2)),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
              ],
            ),
            
            // Status overlay
            Positioned(
              top: 12,
              right: 12,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: const [
                    BoxShadow(color: AppTheme.cardShadow, blurRadius: 8),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    vehicleAsyncValue.when(
                      data: (r) => Text('${r.count} vehicles', style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.bold)),
                      loading: () => const SizedBox(width: 12, height: 12, child: CircularProgressIndicator(strokeWidth: 2)),
                      error: (e, _) => const Icon(Icons.error, color: Colors.red, size: 16),
                    ),
                  ],
                ),
              ),
            ),
            
            // My Location Button
            Positioned(
              bottom: 12,
              right: 12,
              child: FloatingActionButton.small(
                heroTag: 'my_location_btn',
                backgroundColor: Colors.white,
                foregroundColor: AppTheme.primaryBlue,
                elevation: 4,
                onPressed: _determinePosition,
                child: _isLoadingLocation 
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.my_location),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Marker _buildMarker(Vehicle v) {
    Color markerColor = Colors.grey; 
    if (v.occupancyClass != "UNKNOWN") {
       markerColor = AppTheme.primaryBlue;
    }

    return Marker(
      point: LatLng(v.lat, v.lon),
      width: 40,
      height: 40,
      child: GestureDetector(
        onTap: () => _showVehicleDetail(v),
        child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            decoration: BoxDecoration(
              color: markerColor,
              shape: BoxShape.circle,
              border: Border.all(
                color: Colors.white,
                width: 2,
                style: v.sourceType == "SIMULATED" ? BorderStyle.none : BorderStyle.solid,
              ),
              boxShadow: const [
                BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0,2)),
              ],
            ),
            child: const Icon(Icons.directions_bus, color: Colors.white, size: 20),
          ),
          if (v.isStale)
            Positioned(
              bottom: 0,
              right: 0,
              child: Container(
                padding: const EdgeInsets.all(2),
                decoration: const BoxDecoration(color: Colors.orange, shape: BoxShape.circle),
                child: const Icon(Icons.warning, size: 10, color: Colors.white),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Show where this bus came from, where it is going, and draw its path.
  void _showVehicleDetail(Vehicle v) {
    final tripId = v.tripId;
    setState(() => _selectedTripId = tripId);
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => _VehicleDetailSheet(vehicle: v),
    ).whenComplete(() {
      if (mounted) setState(() => _selectedTripId = null);
    });
  }

  /// The tapped trip's path, drawn from its real stop coordinates.
  Widget _buildSelectedPath() {
    final tripId = _selectedTripId;
    if (tripId == null) return const SizedBox.shrink();
    return ref.watch(tripDetailProvider(tripId)).when(
          loading: () => const SizedBox.shrink(),
          error: (_, _) => const SizedBox.shrink(),
          data: (trip) => PolylineLayer(
            polylines: [
              Polyline(
                points: trip.stops.map((s) => LatLng(s.lat, s.lon)).toList(),
                strokeWidth: 4,
                color: AppTheme.primaryBlue.withAlpha(180),
              ),
            ],
          ),
        );
  }
}

/// Origin, destination and the stop list for one vehicle.
class _VehicleDetailSheet extends ConsumerWidget {
  const _VehicleDetailSheet({required this.vehicle});

  final Vehicle vehicle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tripId = vehicle.tripId;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
      child: tripId == null
          // A vehicle between assignments genuinely has no trip. Say so rather
          // than showing an empty route.
          ? const Text('This bus is not currently assigned to a trip.')
          : ref.watch(tripDetailProvider(tripId)).when(
                loading: () => const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (e, _) => Text(e is ApiException
                    ? e.friendlyMessage
                    : 'Could not load this trip.'),
                data: (trip) => _content(context, trip),
              ),
    );
  }

  Widget _content(BuildContext context, api.TripDetail trip) {
    final crowd = api.CrowdLevel.fromWire(vehicle.occupancyClass);
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Route ${trip.routeId ?? ""}',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        if (trip.routeName != null)
          Text(trip.routeName!,
              style: const TextStyle(
                  fontSize: 13, color: AppTheme.textSecondary)),
        const SizedBox(height: 16),
        _endpoint(Icons.trip_origin, 'From', trip.origin.name),
        Padding(
          padding: const EdgeInsets.only(left: 11),
          child: Container(
              width: 2, height: 18, color: AppTheme.textSecondary.withAlpha(60)),
        ),
        _endpoint(Icons.place, 'To', trip.destination.name),
        const SizedBox(height: 16),
        Row(
          children: [
            const Icon(Icons.people_outline, size: 16),
            const SizedBox(width: 6),
            // Crowding always carries a text label, never colour alone.
            Text(crowd.label, style: const TextStyle(fontSize: 13)),
            const Spacer(),
            Text('${trip.stops.length} stops',
                style: const TextStyle(
                    fontSize: 12, color: AppTheme.textSecondary)),
          ],
        ),
        if (vehicle.isStale)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text('Live tracking delayed',
                style: TextStyle(fontSize: 12, color: Colors.orange)),
          ),
      ],
    );
  }

  Widget _endpoint(IconData icon, String label, String name) => Row(
        children: [
          Icon(icon, size: 22, color: AppTheme.primaryBlue),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: const TextStyle(
                        fontSize: 11, color: AppTheme.textSecondary)),
                Text(name,
                    style: const TextStyle(
                        fontSize: 15, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      );
}
