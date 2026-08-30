import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../../../core/api/models.dart';
import '../../../../core/api/places.dart';
import '../../../../theme/app_theme.dart';

/// The journey the server actually returned, drawn on a map.
///
/// Leg endpoints are resolved through [findPlace]: `/v1/plan` gives stop names
/// and ids but no coordinates, and the landmark table is the only mapping the
/// client has today. A leg boarding at a generated intermediate stop resolves
/// to null and is skipped, so the line stays continuous rather than jumping to
/// (0, 0). Because a leg carries no `trip_id`, the path is straight segments
/// between stops — not the road geometry the dashboard map can draw.
class JourneyLiveMap extends StatefulWidget {
  const JourneyLiveMap({
    super.key,
    required this.origin,
    required this.destination,
    required this.option,
  });

  final DelhiPlace origin;
  final DelhiPlace destination;
  final JourneyOption option;

  @override
  State<JourneyLiveMap> createState() => _JourneyLiveMapState();
}

class _JourneyLiveMapState extends State<JourneyLiveMap> {
  final MapController _mapController = MapController();

  /// Index into `option.legs` of the leg whose card is open, if any.
  int? _selectedLeg;

  LatLng get _source => LatLng(widget.origin.lat, widget.origin.lon);
  LatLng get _dest => LatLng(widget.destination.lat, widget.destination.lon);

  static LatLng? _resolve(String stopName) {
    final place = findPlace(stopName);
    return place == null ? null : LatLng(place.lat, place.lon);
  }

  /// origin → every resolvable leg endpoint in order → destination.
  List<LatLng> get _routePoints {
    final points = <LatLng>[_source];
    for (final leg in widget.option.legs) {
      final board = _resolve(leg.boardStopName);
      final alight = _resolve(leg.alightStopName);
      if (board != null) points.add(board);
      if (alight != null) points.add(alight);
    }
    points.add(_dest);
    return points;
  }

  /// The stop each leg is boarded at, for the tappable bus markers. Legs whose
  /// board stop cannot be resolved simply get no marker.
  Map<int, LatLng> get _boardingPoints {
    final result = <int, LatLng>{};
    for (var i = 0; i < widget.option.legs.length; i++) {
      final point = _resolve(widget.option.legs[i].boardStopName);
      if (point != null) result[i] = point;
    }
    return result;
  }

  void _fitRoute() {
    _mapController.fitCamera(
      CameraFit.bounds(
        bounds: LatLngBounds.fromPoints(_routePoints),
        padding: const EdgeInsets.all(40),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final points = _routePoints;
    final boardings = _boardingPoints;
    final selected = _selectedLeg;

    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCameraFit: CameraFit.bounds(
                bounds: LatLngBounds.fromPoints(points),
                padding: const EdgeInsets.all(40),
              ),
              interactionOptions: const InteractionOptions(
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
                    points: points,
                    color: AppTheme.primaryBlue.withAlpha(200),
                    strokeWidth: 4.0,
                  ),
                ],
              ),
              MarkerLayer(
                markers: [
                  Marker(
                    point: _source,
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.blue, Icons.my_location),
                  ),
                  Marker(
                    point: _dest,
                    width: 30,
                    height: 30,
                    child: _buildStopMarker(Colors.redAccent, Icons.location_on),
                  ),
                  for (final entry in boardings.entries)
                    Marker(
                      point: entry.value,
                      width: 50,
                      height: 50,
                      child: GestureDetector(
                        onTap: () => setState(
                          () => _selectedLeg =
                              _selectedLeg == entry.key ? null : entry.key,
                        ),
                        child: _buildBusMarker(_selectedLeg == entry.key),
                      ),
                    ),
                ],
              ),
            ],
          ),
          if (selected != null && selected < widget.option.legs.length)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: _buildLegCard(widget.option.legs[selected]),
            ),
          Positioned(
            top: 12,
            right: 12,
            child: FloatingActionButton.small(
              heroTag: 'recenter_map',
              backgroundColor: Colors.white,
              foregroundColor: AppTheme.primaryBlue,
              elevation: 4,
              onPressed: _fitRoute,
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
        boxShadow: const [
          BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0, 2))
        ],
      ),
      child: Icon(icon, color: color, size: 16),
    );
  }

  Widget _buildBusMarker(bool isSelected) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: isSelected ? Colors.orange : AppTheme.primaryBlue,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 3),
        boxShadow: [
          BoxShadow(
            color: (isSelected ? Colors.orange : AppTheme.primaryBlue)
                .withAlpha(100),
            blurRadius: 10,
            spreadRadius: 3,
          )
        ],
      ),
      child: const Icon(Icons.directions_bus, color: Colors.white, size: 24),
    );
  }

  static String _hhmm(DateTime t) {
    final local = t.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }

  /// One leg of the plan. Every value here comes from `/v1/plan`; the crowd
  /// figure is the p50 of the band the server predicted for this leg.
  Widget _buildLegCard(JourneyLeg leg) {
    final crowd = leg.crowd.p50;
    final onboard = leg.crowd.p50Onboard;
    final capacity = leg.crowd.capacity;
    final crowdColor = crowd.rank >= 4
        ? Colors.red
        : crowd.rank >= 3
            ? Colors.orange
            : Colors.green;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(240),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white, width: 1.5),
        boxShadow: const [
          BoxShadow(
              color: AppTheme.cardShadow,
              blurRadius: 15,
              offset: Offset(0, 8)),
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
                  'Route ${leg.routeId}',
                  style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                      color: AppTheme.textPrimary),
                ),
              ),
              GestureDetector(
                onTap: () => setState(() => _selectedLeg = null),
                child: const Icon(Icons.close,
                    size: 20, color: AppTheme.textSecondary),
              )
            ],
          ),
          if (leg.routeName != null)
            Text(
              leg.routeName!,
              style: const TextStyle(
                  fontSize: 12, color: AppTheme.textSecondary),
            ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: crowdColor.withAlpha(30),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: crowdColor.withAlpha(90)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.groups_rounded, size: 14, color: crowdColor),
                const SizedBox(width: 4),
                Text(
                  onboard != null && capacity != null
                      ? '${crowd.label} ($onboard of $capacity onboard)'
                      : crowd.label,
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: crowdColor),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _DataPoint(label: 'Board', value: leg.boardStopName),
              _DataPoint(label: 'Departs', value: _hhmm(leg.departure)),
              _DataPoint(label: 'Stops', value: '${leg.stops}'),
            ],
          ),
        ],
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
        Text(label,
            style: const TextStyle(
                fontSize: 11,
                color: AppTheme.textSecondary,
                fontWeight: FontWeight.w600)),
        const SizedBox(height: 2),
        Text(value,
            style: const TextStyle(
                fontSize: 14,
                color: AppTheme.textPrimary,
                fontWeight: FontWeight.w900)),
      ],
    );
  }
}
