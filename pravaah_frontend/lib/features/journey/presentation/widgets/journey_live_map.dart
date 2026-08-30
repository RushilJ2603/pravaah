import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../theme/app_theme.dart';
import '../../data/mock_route_geometry.dart';
import 'package:pravaah_api/api.dart';
import '../../../dashboard/providers/vehicle_provider.dart';
import '../../../../core/api/places.dart';

class JourneyLiveMap extends ConsumerStatefulWidget {
  final JourneyOption option;
  final DelhiPlace? originPlace;
  final DelhiPlace? destPlace;
  
  const JourneyLiveMap({super.key, required this.option, this.originPlace, this.destPlace});

  @override
  ConsumerState<JourneyLiveMap> createState() => _JourneyLiveMapState();
}

class _JourneyLiveMapState extends ConsumerState<JourneyLiveMap> {
  final MapController _mapController = MapController();
  
  bool _isBusSelected = false;
  List<LatLng> _routeGeometry = [];
  bool _isLoadingRoute = false;

  @override
  void initState() {
    super.initState();
    _fetchRouteGeometry();
  }

  @override
  void didUpdateWidget(JourneyLiveMap oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.originPlace?.name != widget.originPlace?.name ||
        oldWidget.destPlace?.name != widget.destPlace?.name) {
      _fetchRouteGeometry();
    }
  }

  Future<void> _fetchRouteGeometry() async {
    if (widget.originPlace == null || widget.destPlace == null) return;
    
    setState(() {
      _isLoadingRoute = true;
    });

    try {
      final url = Uri.parse(
          'http://router.project-osrm.org/route/v1/driving/${widget.originPlace!.lon},${widget.originPlace!.lat};${widget.destPlace!.lon},${widget.destPlace!.lat}?overview=full&geometries=geojson');
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
            _isLoadingRoute = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingRoute = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final routeId = widget.option.legs.isNotEmpty ? widget.option.legs.first.routeId : 'Walk';
    
    // Fetch live vehicles for Delhi bounding box
    final vehiclesAsync = ref.watch(vehicleProvider("28.40,76.80,28.90,77.50"));
    
    VehicleView? activeVehicle;
    vehiclesAsync.whenData((fleet) {
      try {
        activeVehicle = fleet.vehicles.firstWhere((v) => v.routeId == routeId);
      } catch (_) {
        activeVehicle = null;
      }
    });

    LatLng busLoc;
    if (activeVehicle != null) {
      busLoc = LatLng(activeVehicle!.lat.toDouble(), activeVehicle!.lon.toDouble());
    } else if (_routeGeometry.isNotEmpty) {
      busLoc = _routeGeometry[_routeGeometry.length ~/ 2];
    } else {
      busLoc = mockRouteGeometry[mockRouteGeometry.length ~/ 2];
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: const MapOptions(
              initialCenter: LatLng(28.6250, 77.2600), // Midpoint
              initialZoom: 12.5,
              interactionOptions: InteractionOptions(
                flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
              ),
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.pravaah.app',
              ),
              PolylineLayer(
                polylines: [
                  Polyline(
                    points: _routeGeometry.isNotEmpty ? _routeGeometry : mockRouteGeometry,
                    color: AppTheme.primaryBlue.withAlpha(200),
                    strokeWidth: 4.0,
                  ),
                ],
              ),
              MarkerLayer(
                markers: [
                  // Source
                  if (widget.originPlace != null)
                  Marker(
                    point: LatLng(widget.originPlace!.lat, widget.originPlace!.lon),
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.blue, Icons.my_location),
                  ),
                  // Destination
                  if (widget.destPlace != null)
                  Marker(
                    point: LatLng(widget.destPlace!.lat, widget.destPlace!.lon),
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.redAccent, Icons.location_on),
                  ),
                  // Live Bus
                  if (activeVehicle != null || _routeGeometry.isNotEmpty || routeId == 'Walk')
                  Marker(
                    point: busLoc,
                    width: 50,
                    height: 50,
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _isBusSelected = !_isBusSelected;
                        });
                      },
                      child: _buildBusMarker(),
                    ),
                  ),
                ],
              ),
            ],
          ),
          
          // Interactive Data Card Overlay
          if (_isBusSelected)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: _buildBusDataCard(activeVehicle, routeId),
            ),
            
          // Recenter Button
          Positioned(
            top: 12,
            right: 12,
            child: FloatingActionButton.small(
              heroTag: 'recenter_map',
              backgroundColor: Colors.white,
              foregroundColor: AppTheme.primaryBlue,
              elevation: 4,
              onPressed: () {
                if (widget.originPlace != null) {
                  _mapController.move(LatLng(widget.originPlace!.lat, widget.originPlace!.lon), 12.5);
                } else {
                  _mapController.move(const LatLng(28.6250, 77.2600), 12.5);
                }
              },
              child: const Icon(Icons.center_focus_strong),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStopMarker(Color color, IconData icon) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 3),
        boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0, 2))],
      ),
      child: Icon(icon, color: color, size: 16),
    );
  }

  Widget _buildBusMarker() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: _isBusSelected ? Colors.orange : AppTheme.primaryBlue,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 3),
        boxShadow: [
          BoxShadow(
            color: (_isBusSelected ? Colors.orange : AppTheme.primaryBlue).withAlpha(100),
            blurRadius: 10,
            spreadRadius: 3,
          )
        ],
      ),
      child: const Icon(Icons.directions_bus, color: Colors.white, size: 24),
    );
  }

  Widget _buildBusDataCard(VehicleView? vehicle, String routeId) {
    return AnimatedOpacity(
      opacity: 1.0,
      duration: const Duration(milliseconds: 300),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(240), // Glassmorphism-lite
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
                Text(
                  vehicle != null ? 'Vehicle ${vehicle.vehicleId}' : 'Vehicle for $routeId',
                  style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: AppTheme.textPrimary),
                ),
                GestureDetector(
                  onTap: () => setState(() => _isBusSelected = false),
                  child: const Icon(Icons.close, size: 20, color: AppTheme.textSecondary),
                )
              ],
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red.shade200),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.groups_rounded, size: 14, color: Colors.red.shade700),
                  const SizedBox(width: 4),
                  Text(
                    vehicle != null ? 'Live Data (${vehicle.occupancyClass.toString().split('.').last})' : 'Crush Load (85% Capacity)',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _DataPoint(label: 'Speed', value: vehicle?.speedMps != null ? '${(vehicle!.speedMps! * 3.6).toStringAsFixed(1)} km/h' : '24 km/h'),
                _DataPoint(label: 'Next Stop', value: vehicle?.stopId ?? 'Unknown'),
                _DataPoint(label: 'Data Age', value: vehicle != null ? '${vehicle.ageS}s' : '12s'),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DataPoint extends StatelessWidget {
  final String label;
  final String value;

  const _DataPoint({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 14, color: AppTheme.textPrimary, fontWeight: FontWeight.w900)),
      ],
    );
  }
}
