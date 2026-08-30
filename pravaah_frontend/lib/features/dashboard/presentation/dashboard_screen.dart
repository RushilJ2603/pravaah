import 'package:flutter/material.dart';
import '../../../../theme/app_theme.dart';
import 'widgets/mini_live_map.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Image.asset(
                          'assets/images/logo_full.png',
                          height: 32,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Where to go?',
                          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    
                    // Search Bar
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: const [
                          BoxShadow(
                            color: AppTheme.cardShadow,
                            blurRadius: 10,
                            offset: Offset(0, 4),
                          ),
                        ],
                      ),
                      child: const TextField(
                        decoration: InputDecoration(
                          hintText: 'Enter destination',
                          prefixIcon: Icon(Icons.search, color: AppTheme.textSecondary),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(vertical: 16),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    
                    const SizedBox(height: 8),
                    
                    // Mini Live Map Section
                    Text(
                      'Live Network Map',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    const MiniLiveMap(),
                    
                    const SizedBox(height: 32),
                    
                    // Recent Destinations
                    Text(
                      'Recent Destinations',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 16),
                    _buildRecentDestination(context, Icons.home, 'Home', 'NITK Campus, Surathkal'),
                    _buildRecentDestination(context, Icons.work, 'Work', 'Mangalore City Center'),
                    _buildRecentDestination(context, Icons.history, 'Udupi Bus Stand', 'Udupi'),
                    
                    const SizedBox(height: 120), // Bottom padding for floating nav bar
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentDestination(BuildContext context, IconData icon, String title, String subtitle) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(color: AppTheme.cardShadow, blurRadius: 4, offset: Offset(0, 2)),
        ],
      ),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: AppTheme.background,
          child: Icon(icon, color: AppTheme.primaryBlue),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.arrow_forward_ios, size: 16, color: AppTheme.textSecondary),
        onTap: () {},
      ),
    );
  }
}

