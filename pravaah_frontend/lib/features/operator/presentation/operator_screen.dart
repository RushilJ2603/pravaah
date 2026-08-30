import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/models.dart';
import '../../../core/api/session.dart';
import '../../../theme/app_theme.dart';
import '../providers/operator_provider.dart';

/// Operator console: predicted problems first, then fleet and feed health.
///
/// The ordering is the argument. A control room that learns about crowding when
/// it happens is the status quo; this screen leads with what has not happened
/// yet and how long there is to act.
class OperatorScreen extends ConsumerStatefulWidget {
  const OperatorScreen({super.key});

  @override
  ConsumerState<OperatorScreen> createState() => _OperatorScreenState();
}

class _OperatorScreenState extends ConsumerState<OperatorScreen> {
  int _horizon = 60;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fleet Command'),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(hotspotsProvider);
              ref.invalidate(dataHealthProvider);
              ref.invalidate(fleetProvider);
            },
          ),
          IconButton(
            tooltip: 'Sign out',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(sessionProvider.notifier).signOut(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(hotspotsProvider);
          ref.invalidate(dataHealthProvider);
          ref.invalidate(fleetProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildHealth(),
            const SizedBox(height: 20),
            Row(
              children: [
                Text('Predicted hotspots',
                    style: Theme.of(context).textTheme.titleLarge),
                const Spacer(),
                DropdownButton<int>(
                  value: _horizon,
                  underline: const SizedBox.shrink(),
                  items: const [
                    DropdownMenuItem(value: 30, child: Text('30 min')),
                    DropdownMenuItem(value: 60, child: Text('60 min')),
                    DropdownMenuItem(value: 120, child: Text('2 hours')),
                  ],
                  onChanged: (v) => setState(() => _horizon = v ?? 60),
                ),
              ],
            ),
            const SizedBox(height: 8),
            _buildHotspots(),
          ],
        ),
      ),
    );
  }

  Widget _buildHealth() {
    return ref.watch(dataHealthProvider).when(
          loading: () => const _Card(child: LinearProgressIndicator()),
          error: (e, _) => _Card(child: _error(e)),
          data: (health) {
            final fleet = ref.watch(fleetProvider);
            return _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        health.isHealthy
                            ? Icons.check_circle
                            : Icons.error_outline,
                        color: health.isHealthy
                            ? const Color(0xFF2E7D32)
                            : const Color(0xFFB71C1C),
                      ),
                      const SizedBox(width: 8),
                      Text('System health',
                          style: Theme.of(context).textTheme.titleMedium),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 20,
                    runSpacing: 12,
                    children: [
                      _stat('Vehicles tracked', '${health.vehiclesTracked}'),
                      _stat('Stale', '${health.vehiclesStale}'),
                      _stat('Crowd coverage',
                          '${(health.occupancyCoverage * 100).round()}%'),
                      _stat('Oldest position', '${health.oldestPositionAgeS}s'),
                      _stat('Feed version', '${health.feedVersionId ?? "-"}'),
                      _stat('Fleet loaded',
                          fleet.valueOrNull == null
                              ? '...'
                              : '${fleet.valueOrNull!.count}'),
                    ],
                  ),
                  if (health.forecastModel != null) ...[
                    const SizedBox(height: 12),
                    Text('Model: ${health.forecastModel}',
                        style: const TextStyle(
                            fontSize: 11, color: AppTheme.textSecondary)),
                  ],
                  if (health.sourceTypes.isNotEmpty)
                    Text(
                      'Sources: ${health.sourceTypes.entries.map((e) => "${e.key} ${e.value}").join(", ")}',
                      style: const TextStyle(
                          fontSize: 11, color: AppTheme.textSecondary),
                    ),
                ],
              ),
            );
          },
        );
  }

  Widget _stat(String label, String value) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(value,
              style:
                  const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          Text(label,
              style: const TextStyle(
                  fontSize: 11, color: AppTheme.textSecondary)),
        ],
      );

  Widget _buildHotspots() {
    return ref.watch(hotspotsProvider(_horizon)).when(
          loading: () => const Padding(
            padding: EdgeInsets.all(32),
            child: Center(child: CircularProgressIndicator()),
          ),
          error: (e, _) => _Card(child: _error(e)),
          data: (response) {
            if (response.hotspots.isEmpty) {
              return const _Card(
                child: Row(
                  children: [
                    Icon(Icons.check_circle_outline, color: Color(0xFF2E7D32)),
                    SizedBox(width: 12),
                    Expanded(
                        child: Text(
                            'No crowding predicted in this window. Nothing needs action.')),
                  ],
                ),
              );
            }
            return Column(
              children: [
                for (final h in response.hotspots) _hotspotCard(h),
              ],
            );
          },
        );
  }

  Widget _hotspotCard(Hotspot h) {
    final urgent = h.leadTimeMin <= 15;
    final colour =
        h.severity >= 4 ? const Color(0xFFB71C1C) : const Color(0xFFD84315);
    return _Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: colour.withAlpha(24),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text('Route ${h.routeShortName ?? h.routeId}',
                    style: TextStyle(
                        color: colour,
                        fontWeight: FontWeight.bold,
                        fontSize: 12)),
              ),
              const Spacer(),
              // Lead time is the operator's whole value, so it is the loudest
              // thing on the card.
              Text(
                h.leadTimeMin <= 0 ? 'now' : 'in ${h.leadTimeMin} min',
                style: TextStyle(
                  color: urgent ? colour : AppTheme.textSecondary,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(h.stopName,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          const SizedBox(height: 4),
          Text(h.crowd.summary,
              style: TextStyle(color: colour, fontSize: 13)),
          if (h.crowd.p50Onboard != null)
            Text(
              '${h.crowd.p10Onboard}-${h.crowd.p90Onboard} of ${h.crowd.capacity} onboard'
              ' · ${h.servicesInWindow} services in window',
              style: const TextStyle(
                  fontSize: 11, color: AppTheme.textSecondary),
            ),
        ],
      ),
    );
  }

  Widget _error(Object e) {
    final message =
        e is ApiException ? e.friendlyMessage : 'Could not load operator data.';
    return Row(
      children: [
        const Icon(Icons.cloud_off, color: AppTheme.textSecondary),
        const SizedBox(width: 12),
        Expanded(child: Text(message)),
      ],
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: const [
            BoxShadow(
                color: AppTheme.cardShadow, blurRadius: 4, offset: Offset(0, 2)),
          ],
        ),
        child: child,
      );
}
