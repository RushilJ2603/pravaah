import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/models.dart';
import '../../../core/api/places.dart';
import '../../../core/api/session.dart';
import '../../../theme/app_theme.dart';
import '../providers/conductor_provider.dart';

/// The conductor console.
///
/// Designed for someone who is also doing their actual job: large targets,
/// high contrast, one screen, no navigation. Crowd levels carry text labels
/// rather than colour alone, both because that is the project rule and because
/// this gets used in sunlight.
class ConductorScreen extends ConsumerStatefulWidget {
  const ConductorScreen({super.key});

  @override
  ConsumerState<ConductorScreen> createState() => _ConductorScreenState();
}

class _ConductorScreenState extends ConsumerState<ConductorScreen> {
  final _vehicle = TextEditingController(text: 'DL0001');
  final _route = TextEditingController();
  CrowdLevel? _lastReported;
  String? _notice;

  @override
  void dispose() {
    _vehicle.dispose();
    _route.dispose();
    super.dispose();
  }

  Future<void> _guard(Future<void> Function() action, String success) async {
    try {
      await action();
      if (mounted) setState(() => _notice = success);
    } on ApiException catch (e) {
      if (mounted) setState(() => _notice = e.friendlyMessage);
    } catch (_) {
      if (mounted) setState(() => _notice = 'Something went wrong.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final shiftState = ref.watch(conductorProvider);
    final shift = shiftState.valueOrNull;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Conductor'),
        actions: [
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(sessionProvider.notifier).signOut(),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: shift == null
              ? _buildStartShift(shiftState)
              : _buildOnShift(shift),
        ),
      ),
    );
  }

  Widget _buildStartShift(AsyncValue<Shift?> state) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('Start of shift',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text(
          'Bind this phone to the bus you are working. Nothing is reported '
          'until you do -- a position with no shift cannot be matched to a trip.',
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
        ),
        const SizedBox(height: 24),
        TextField(
          controller: _vehicle,
          decoration: const InputDecoration(
            labelText: 'Vehicle number',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.directions_bus),
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _route,
          decoration: const InputDecoration(
            labelText: 'Route (optional)',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.alt_route),
          ),
        ),
        const SizedBox(height: 24),
        SizedBox(
          height: 60,
          child: ElevatedButton.icon(
            onPressed: state.isLoading
                ? null
                : () => ref.read(conductorProvider.notifier).startShift(
                      vehicleId: _vehicle.text.trim(),
                      deviceId: 'conductor-device',
                      routeId: _route.text.trim(),
                    ),
            icon: const Icon(Icons.play_arrow),
            label: const Text('Start shift', style: TextStyle(fontSize: 18)),
          ),
        ),
        if (state.hasError) ...[
          const SizedBox(height: 16),
          Text(
            state.error is ApiException
                ? (state.error as ApiException).code == 'VEHICLE_ALREADY_CLAIMED'
                    ? 'Another crew member already has this bus on shift.'
                    : (state.error as ApiException).friendlyMessage
                : 'Could not start the shift.',
            style: const TextStyle(color: Color(0xFFB71C1C)),
          ),
        ],
      ],
    );
  }

  Widget _buildOnShift(Shift shift) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFF2E7D32).withAlpha(20),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              const Icon(Icons.check_circle, color: Color(0xFF2E7D32)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('On shift · ${shift.vehicleId}',
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text('Shift ${shift.shiftId}',
                        style: const TextStyle(
                            fontSize: 11, color: AppTheme.textSecondary)),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        const Text('How full is the bus?',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Expanded(
          child: GridView.count(
            crossAxisCount: 2,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.4,
            children: [
              for (final level in kConductorLevels) _crowdButton(level),
            ],
          ),
        ),
        if (_notice != null) ...[
          const SizedBox(height: 8),
          Text(_notice!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary)),
        ],
        const SizedBox(height: 12),
        SizedBox(
          height: 52,
          child: OutlinedButton.icon(
            onPressed: () => _guard(
              () => ref.read(conductorProvider.notifier).reportPosition(
                    // Connaught Place. A real deployment reads the device GPS;
                    // this keeps the flow exercisable without location
                    // permissions on a demo machine.
                    lat: kDelhiPlaces.first.lat,
                    lon: kDelhiPlaces.first.lon,
                  ),
              'Position sent',
            ),
            icon: const Icon(Icons.my_location),
            label: const Text('Send position'),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 52,
          child: TextButton.icon(
            onPressed: () =>
                _guard(() => ref.read(conductorProvider.notifier).endShift(),
                    'Shift ended'),
            icon: const Icon(Icons.stop_circle_outlined),
            label: const Text('End shift'),
          ),
        ),
      ],
    );
  }

  Widget _crowdButton(CrowdLevel level) {
    final selected = _lastReported == level;
    final colour = switch (level) {
      CrowdLevel.manySeats => const Color(0xFF2E7D32),
      CrowdLevel.fewSeats => const Color(0xFF9E7B00),
      CrowdLevel.standing => const Color(0xFFD84315),
      _ => const Color(0xFFB71C1C),
    };
    return Material(
      color: selected ? colour : colour.withAlpha(24),
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () {
          setState(() => _lastReported = level);
          _guard(
            () => ref.read(conductorProvider.notifier).reportOccupancy(level),
            'Reported: ${level.label}',
          );
        },
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              level.label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
                color: selected ? Colors.white : colour,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
