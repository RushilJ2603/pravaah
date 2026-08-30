import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../../providers/vehicle_provider.dart';
import '../../../../theme/app_theme.dart';
import 'package:pravaah_api/api.dart';
import '../../../../core/api/places.dart';

class MiniLiveMap extends ConsumerStatefulWidget {
  const MiniLiveMap({super.key});

  @override
  ConsumerState<MiniLiveMap> createState() => _MiniLiveMapState();
}

class _MiniLiveMapState extends ConsumerState<MiniLiveMap> {
  final MapController _mapController = MapController();
  final String _currentBbox = "28.40,76.80,28.90,77.50";
  
  Position? _currentPosition;
  bool _isLoadingLocation = false;
  VehicleView? _selectedVehicle;
  
  DelhiPlace? _selectedOrigin;
  DelhiPlace? _selectedDest;
  List<LatLng> _routeGeometry = [];
  String? _boardStopName;
  String? _alightStopName;

  @override
  void initState() {
    super.initState();
    _determinePosition();
  }

  Future<void> _determinePosition() async {
    // Overriding real GPS for the simulation to keep the viewport in Delhi.
    _mapController.move(const LatLng(28.6139, 77.2090), 13.0);
    
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Showing Delhi simulation area.')),
      );
    }
  }

  Future<void> _fetchRouteGeometry(DelhiPlace origin, DelhiPlace dest, VehicleView v) async {
    setState(() {
      _routeGeometry = [];
    });

    try {
      final url = Uri.parse(
          'http://router.project-osrm.org/route/v1/driving/${origin.lon},${origin.lat};${v.lon},${v.lat};${dest.lon},${dest.lat}?overview=full&geometries=geojson');
      final response = await http.get(url);
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final coordinates = data['routes'][0]['geometry']['coordinates'] as List;
        
        final List<LatLng> points = coordinates.map((coord) {
          return LatLng(coord[1].toDouble(), coord[0].toDouble());
        }).toList();
        
        if (mounted) {
          setState(() {
            _routeGeometry = points;
          });
        }
      }
    } catch (_) {}
  }

  DelhiPlace _getClosestPlace(LatLng point) {
    DelhiPlace? closest;
    double minDistance = double.infinity;
    const distance = Distance();
    for (final p in kDelhiPlaces) {
      final d = distance.as(LengthUnit.Meter, point, LatLng(p.lat, p.lon));
      if (d < minDistance) {
        minDistance = d;
        closest = p;
      }
    }
    return closest!;
  }

  /// Find a DelhiPlace by fuzzy stop name match.
  DelhiPlace? _findPlaceByStopName(String stopName) {
    final lower = stopName.toLowerCase();
    // Try keyword matching: "Karol Bagh - Naraina (4)" → find "Karol Bagh"
    DelhiPlace? best;
    int bestMatchLen = 0;
    for (final p in kDelhiPlaces) {
      final pLower = p.name.toLowerCase();
      if (lower.contains(pLower) && pLower.length > bestMatchLen) {
        best = p;
        bestMatchLen = pLower.length;
      }
    }
    return best;
  }

  void _onVehicleSelected(VehicleView v) {
    setState(() {
      _selectedVehicle = v;
      _selectedOrigin = null;
      _selectedDest = null;
      _boardStopName = null;
      _alightStopName = null;
      _routeGeometry = [];
    });
    _fetchRealRoute(v);
  }

  Future<void> _fetchRealRoute(VehicleView v) async {
    // Step 1: use /v1/plan from the bus position to a nearby known stop
    // to discover real board/alight stop names for this route.
    final nearbyDest = _getClosestPlace(LatLng(
      v.lat.toDouble() + 0.05, v.lon.toDouble() + 0.05));

    try {
      // Call the API from bus position to nearby destination
      final planUrl = Uri.parse(
        'https://strict-affiliation-ranked-gates.trycloudflare.com/v1/plan'
        '?from_lat=${v.lat}&from_lon=${v.lon}&to_lat=${nearbyDest.lat}&to_lon=${nearbyDest.lon}');
      final planResp = await http.get(planUrl);
      
      if (planResp.statusCode == 200) {
        final planData = json.decode(planResp.body);
        final options = planData['options'] as List?;
        
        String? boardName;
        String? alightName;
        
        // Find a leg that runs on this route
        if (options != null) {
          outer:
          for (final opt in options) {
            final legs = opt['legs'] as List?;
            if (legs == null) continue;
            for (final leg in legs) {
              if (leg['route_id'] == v.routeId) {
                boardName = leg['board_stop_name'] as String?;
                alightName = leg['alight_stop_name'] as String?;
                break outer;
              }
            }
          }
        }
        
        boardName ??= 'Bus at ${v.lat.toStringAsFixed(3)}, ${v.lon.toStringAsFixed(3)}';
        alightName ??= nearbyDest.name;
        
        final originPlace = _findPlaceByStopName(boardName);
        final destPlace = _findPlaceByStopName(alightName) ?? nearbyDest;
        
        if (mounted) {
          setState(() {
            _boardStopName = boardName;
            _alightStopName = alightName;
            _selectedOrigin = originPlace ?? _getClosestPlace(LatLng(v.lat.toDouble(), v.lon.toDouble()));
            _selectedDest = destPlace;
          });
        }
        
        // Step 2: fetch OSRM route through the bus position
        await _fetchRouteGeometry(_selectedOrigin!, destPlace, v);
      }
    } catch (e) {
      // Graceful fallback: just use nearest places
      final origin = _getClosestPlace(LatLng(v.lat.toDouble(), v.lon.toDouble()));
      final dest = nearbyDest;
      if (mounted) {
        setState(() {
          _boardStopName = origin.name;
          _alightStopName = dest.name;
          _selectedOrigin = origin;
          _selectedDest = dest;
        });
      }
      await _fetchRouteGeometry(origin, dest, v);
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
                if (_routeGeometry.isNotEmpty)
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: _routeGeometry,
                        color: Colors.deepOrange,
                        strokeWidth: 5.0,
                      ),
                    ],
                  ),
                if (_selectedOrigin != null && _selectedDest != null)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: LatLng(_selectedOrigin!.lat, _selectedOrigin!.lon),
                        width: 30,
                        height: 30,
                        child: _buildStopMarker(Colors.blue, Icons.my_location),
                      ),
                      Marker(
                        point: LatLng(_selectedDest!.lat, _selectedDest!.lon),
                        width: 30,
                        height: 30,
                        child: _buildStopMarker(Colors.redAccent, Icons.location_on),
                      ),
                    ],
                  ),
                vehicleAsyncValue.when(
                  data: (response) => MarkerLayer(
                    markers: response.vehicles.map((v) => _buildMarker(v)).toList(),
                  ),
                  loading: () => const MarkerLayer(markers: []),
                  error: (e, stack) => const MarkerLayer(markers: []),
                ),
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
            
            // Selected Vehicle Overlay
            if (_selectedVehicle != null)
              Positioned(
                bottom: 12,
                left: 12,
                right: 60, // Leave room for FAB
                child: _buildVehicleCard(_selectedVehicle!),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildVehicleCard(VehicleView vehicle) {
    return AnimatedOpacity(
      opacity: 1.0,
      duration: const Duration(milliseconds: 300),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(240),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white, width: 1.5),
          boxShadow: const [
            BoxShadow(color: AppTheme.cardShadow, blurRadius: 15, offset: Offset(0, 8)),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    'Route ${vehicle.routeId ?? "Unknown"}',
                    style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: AppTheme.textPrimary),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                GestureDetector(
                  onTap: () {
                    setState(() {
                      _selectedVehicle = null;
                      _selectedOrigin = null;
                      _selectedDest = null;
                      _routeGeometry = [];
                    });
                  },
                  child: const Icon(Icons.close, size: 20, color: AppTheme.textSecondary),
                )
              ],
            ),
            if (_boardStopName != null && _alightStopName != null) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  const Icon(Icons.my_location, size: 12, color: AppTheme.primaryBlue),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      '$_boardStopName → $_alightStopName',
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textSecondary),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ] else if (_routeGeometry.isEmpty) ...[
              const SizedBox(height: 6),
              const Row(
                children: [
                  SizedBox(width: 10, height: 10, child: CircularProgressIndicator(strokeWidth: 2)),
                  SizedBox(width: 8),
                  Text('Loading route info...', style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
                ],
              ),
            ],
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.groups_rounded, size: 14, color: Colors.blue.shade700),
                  const SizedBox(width: 4),
                  Text(
                    'Load: ${vehicle.occupancyClass.toString().split('.').last}',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.blue.shade700),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(child: _buildDataPoint(label: 'Speed', value: vehicle.speedMps != null ? '${(vehicle.speedMps! * 3.6).toStringAsFixed(1)} km/h' : '0 km/h')),
                Expanded(child: _buildDataPoint(label: 'Next Stop', value: vehicle.stopId ?? 'Unknown')),
                Expanded(child: _buildDataPoint(label: 'Age', value: '${vehicle.ageS}s')),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDataPoint({required String label, required String value}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 14, color: AppTheme.textPrimary, fontWeight: FontWeight.w900), overflow: TextOverflow.ellipsis, maxLines: 1),
      ],
    );
  }

  Widget _buildStopMarker(Color color, IconData icon) {
    return Container(
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2),
        boxShadow: const [
          BoxShadow(color: AppTheme.cardShadow, blurRadius: 4),
        ],
      ),
      child: Icon(icon, color: Colors.white, size: 16),
    );
  }

  Marker _buildMarker(VehicleView v) {
    Color markerColor = Colors.grey; 
    if (v.occupancyClass != OccupancyClass.UNKNOWN) {
       markerColor = AppTheme.primaryBlue;
    }
    
    final isSelected = _selectedVehicle?.vehicleId == v.vehicleId;
    if (isSelected) {
       markerColor = Colors.deepOrange;
    }

    return Marker(
      point: LatLng(v.lat.toDouble(), v.lon.toDouble()),
      width: isSelected ? 48 : 40,
      height: isSelected ? 48 : 40,
      child: GestureDetector(
        onTap: () => _onVehicleSelected(v),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              decoration: BoxDecoration(
                color: markerColor,
                shape: BoxShape.circle,
                border: Border.all(
                  color: Colors.white,
                  width: isSelected ? 3 : 2,
                  style: v.sourceType == SourceType.SIMULATED ? BorderStyle.none : BorderStyle.solid,
                ),
                boxShadow: [
                  if (isSelected) const BoxShadow(color: Colors.deepOrange, blurRadius: 8)
                  else const BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0,2)),
                ],
              ),
              child: Icon(Icons.directions_bus, color: Colors.white, size: isSelected ? 24 : 20),
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
}
