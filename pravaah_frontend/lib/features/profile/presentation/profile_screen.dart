import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/api/session.dart';
import '../../../../theme/app_theme.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.all(24.0),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  Text(
                    'Profile',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 24),
                  
                  // Premium Header Card
                  _buildHeaderCard(context, session),
                  const SizedBox(height: 24),
                  
                  // Quick Stats Row
                  _buildStatsRow(),
                  const SizedBox(height: 32),
                  
                  // Settings Groups
                  // Staff access sits directly under the header, not below
                  // six rows of settings: it was previously off-screen on a
                  // phone, so the only authenticated part of the product
                  // looked like it did not exist.
                  _buildSettingsGroup('Staff', [
                    if (session == null)
                      _buildSettingItem(
                          Icons.badge_outlined, 'Operator / Conductor sign in',
                          onTap: () => context.push('/staff'))
                    else
                      _buildSettingItem(
                          Icons.dashboard_outlined,
                          'Open ${session.roleLabel.toLowerCase()} console',
                          trailingText: session.username,
                          onTap: () => context.push('/staff')),
                  ]),
                  const SizedBox(height: 24),

                  _buildSettingsGroup('Account', [
                    _buildSettingItem(Icons.payment, 'Payment Methods'),
                    _buildSettingItem(Icons.location_on_outlined, 'Saved Addresses'),
                    _buildSettingItem(Icons.history, 'Trip History'),
                  ]),
                  const SizedBox(height: 24),
                  
                  _buildSettingsGroup('Preferences', [
                    _buildSettingItem(Icons.notifications_outlined, 'Notifications'),
                    _buildSettingItem(Icons.language, 'Language', trailingText: 'English'),
                    _buildSettingItem(Icons.accessibility_new, 'Accessibility'),
                  ]),
                  const SizedBox(height: 24),
                  
                  _buildSettingsGroup('Support', [
                    _buildSettingItem(Icons.help_outline, 'Help Center'),
                    _buildSettingItem(Icons.report_problem_outlined, 'Report an Issue'),
                  ]),
                  const SizedBox(height: 32),
                  
                  // Logout Button
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.redAccent,
                        side: const BorderSide(color: Colors.redAccent, width: 1.5),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      // Only staff have a session to end. A passenger is
                      // anonymous by design, so there is nothing to log out of.
                      onPressed: session == null
                          ? null
                          : () => ref.read(sessionProvider.notifier).signOut(),
                      child: Text(
                          session == null ? 'Not signed in' : 'Log Out',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                  ),
                  const SizedBox(height: 120),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderCard(BuildContext context, StaffSession? session) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const RadialGradient(
          center: Alignment.topLeft,
          radius: 2.0,
          colors: [AppTheme.primaryBlue, Color(0xFF003A86)],
        ),
        borderRadius: BorderRadius.circular(32),
        boxShadow: [
          BoxShadow(color: AppTheme.primaryBlue.withAlpha(80), blurRadius: 20, offset: const Offset(0, 10)),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white.withAlpha(100), width: 3),
            ),
            alignment: Alignment.center,
            child: Text(
              session == null ? 'MT' : session.username.characters.first.toUpperCase(),
              style: const TextStyle(
                  color: AppTheme.primaryBlue,
                  fontSize: 26,
                  fontWeight: FontWeight.w900),
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  session?.username ?? 'Mayank Tiwari',
                  style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 4),
                Text(
                  session == null ? '+91 98765 43210' : 'Signed in as staff',
                  style: TextStyle(color: Colors.white.withAlpha(200), fontSize: 14),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.greenAccent.withAlpha(40),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.greenAccent.withAlpha(80)),
                  ),
                  child: Text(
                    session?.roleLabel ?? 'Pro Commuter',
                    style: const TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.edit, color: Colors.white),
          )
        ],
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        Expanded(child: _buildStatCard('142', 'Trips', Icons.directions_bus, Colors.blue)),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard('₹450', 'Wallet', Icons.account_balance_wallet, Colors.orange)),
        const SizedBox(width: 12),
        Expanded(child: _buildStatCard('18kg', 'CO₂ Saved', Icons.eco, Colors.green)),
      ],
    );
  }

  Widget _buildStatCard(String value, String label, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.shade200),
        boxShadow: [
          BoxShadow(color: AppTheme.cardShadow.withAlpha(15), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 12),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: AppTheme.textPrimary)),
          const SizedBox(height: 2),
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  Widget _buildSettingsGroup(String title, List<Widget> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
          child: Text(
            title,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.textSecondary, letterSpacing: 0.5),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [
              BoxShadow(color: AppTheme.cardShadow.withAlpha(10), blurRadius: 10, offset: const Offset(0, 4)),
            ],
          ),
          child: Column(
            children: items,
          ),
        ),
      ],
    );
  }

  Widget _buildSettingItem(IconData icon, String title,
      {String? trailingText, VoidCallback? onTap}) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap ?? () {},
        borderRadius: BorderRadius.circular(24),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppTheme.background,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, size: 20, color: AppTheme.primaryBlue),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textPrimary),
                ),
              ),
              if (trailingText != null) ...[
                Text(
                  trailingText,
                  style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary, fontWeight: FontWeight.w500),
                ),
                const SizedBox(width: 8),
              ],
              const Icon(Icons.chevron_right, color: AppTheme.textSecondary, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
