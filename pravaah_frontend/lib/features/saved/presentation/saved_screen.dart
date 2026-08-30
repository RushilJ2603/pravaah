import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../theme/app_theme.dart';
import '../../journey/providers/recent_searches_provider.dart';

class SavedScreen extends StatelessWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AppTheme.background,
        appBar: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          title: Text(
            'Saved & Alerts',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryBlue,
                ),
          ),
          bottom: const TabBar(
            labelColor: AppTheme.primaryBlue,
            unselectedLabelColor: AppTheme.textSecondary,
            indicatorColor: AppTheme.primaryBlue,
            indicatorWeight: 3,
            tabs: [
              Tab(text: 'Saved'),
              Tab(text: 'Alerts'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            _SavedTab(),
            _AlertsTab(),
          ],
        ),
      ),
    );
  }
}

class _SavedTab extends ConsumerWidget {
  const _SavedTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recents = ref.watch(recentSearchesProvider);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Saved Places', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ...recents.map((place) => Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withAlpha(25),
              child: const Icon(Icons.favorite, color: Colors.redAccent),
            ),
            title: Text(place.name, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Delhi'),
            trailing: const Icon(Icons.chevron_right, color: AppTheme.textSecondary),
          ),
        )),
        
        if (recents.isEmpty)
          const Padding(
            padding: EdgeInsets.all(24.0),
            child: Center(child: Text('No saved places yet.', style: TextStyle(color: AppTheme.textSecondary))),
          ),
          
        const SizedBox(height: 32),
        Text('Saved Routes', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Card(
          elevation: 0,
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withAlpha(25),
              child: const Icon(Icons.directions_bus, color: AppTheme.primaryBlue),
            ),
            title: const Text('DL422', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Karol Bagh ↔ Naraina'),
            trailing: const Icon(Icons.notifications_active, color: Colors.orange),
          ),
        ),
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200),
          ),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withAlpha(25),
              child: const Icon(Icons.directions_bus, color: AppTheme.primaryBlue),
            ),
            title: const Text('DL454', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Punjabi Bagh ↔ Connaught Place'),
            trailing: const Icon(Icons.notifications_none, color: AppTheme.textSecondary),
          ),
        ),
        
        const SizedBox(height: 100), // Padding for bottom nav
      ],
    );
  }
}

class _AlertsTab extends StatelessWidget {
  const _AlertsTab();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildAlertCard(
          context,
          route: 'DL422',
          title: 'Heavy Traffic Delay',
          description: 'Buses are running approximately 15 minutes late due to congestion near Karol Bagh.',
          type: _AlertType.warning,
        ),
        _buildAlertCard(
          context,
          route: 'DL454',
          title: 'Stop Relocation',
          description: 'The Punjabi Bagh stop has been temporarily moved 50 meters down the road due to construction.',
          type: _AlertType.info,
        ),
        _buildAlertCard(
          context,
          route: 'General',
          title: 'Weekend Maintenance',
          description: 'Some routes may experience slight diversions this weekend for scheduled road maintenance in Central Delhi.',
          type: _AlertType.info,
        ),
        
        const SizedBox(height: 100), // Padding for bottom nav
      ],
    );
  }

  Widget _buildAlertCard(BuildContext context, {required String route, required String title, required String description, required _AlertType type}) {
    final color = type == _AlertType.warning ? Colors.orange : Colors.blue;
    final icon = type == _AlertType.warning ? Icons.warning_amber_rounded : Icons.info_outline_rounded;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withAlpha(75), width: 1.5),
        boxShadow: const [BoxShadow(color: AppTheme.cardShadow, blurRadius: 8, offset: Offset(0, 4))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: AppTheme.primaryBlue, borderRadius: BorderRadius.circular(6)),
                child: Text(route, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)),
              ),
              const SizedBox(width: 8),
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 4),
              Expanded(child: Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 16))),
            ],
          ),
          const SizedBox(height: 12),
          Text(description, style: const TextStyle(color: AppTheme.textSecondary, height: 1.4)),
          const SizedBox(height: 12),
          Text('Updated recently', style: TextStyle(color: Colors.grey.shade500, fontSize: 11)),
        ],
      ),
    );
  }
}

enum _AlertType { warning, info }
