import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../../theme/app_theme.dart';
import '../../data/mock_route_geometry.dart';

class JourneyLiveMap extends StatefulWidget {
  const JourneyLiveMap({super.key});

  @override
  State<JourneyLiveMap> createState() => _JourneyLiveMapState();
}

class _JourneyLiveMapState extends State<JourneyLiveMap> {
  final MapController _mapController = MapController();
  
  // Mock Data from real road geometry
  final LatLng _source = mockRouteGeometry.first; // Connaught Place Area
  final LatLng _dest = mockRouteGeometry.last; // Anand Vihar Area
  final LatLng _busLocation = mockRouteGeometry[mockRouteGeometry.length ~/ 2]; // Midpoint on the actual road
  
  bool _isBusSelected = false;

  @override
  Widget build(BuildContext context) {
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
                    points: mockRouteGeometry,
                    color: AppTheme.primaryBlue.withAlpha(200),
                    strokeWidth: 4.0,
                  ),
                ],
              ),
              MarkerLayer(
                markers: [
                  // Source
                  Marker(
                    point: _source,
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.blue, Icons.my_location),
                  ),
                  // Destination
                  Marker(
                    point: _dest,
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.redAccent, Icons.location_on),
                  ),
                  // Live Bus
                  Marker(
                    point: _busLocation,
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
              child: _buildBusDataCard(),
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
                _mapController.move(const LatLng(28.6250, 77.2600), 12.5);
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

  Widget _buildBusDataCard() {
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
                const Text(
                  'Vehicle DL0181',
                  style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16, color: AppTheme.textPrimary),
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
                    'Crush Load (85% Capacity)',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.red.shade700),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            const Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _DataPoint(label: 'Speed', value: '24 km/h'),
                _DataPoint(label: 'Next Stop', value: 'India Gate'),
                _DataPoint(label: 'Data Age', value: '12s'),
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
