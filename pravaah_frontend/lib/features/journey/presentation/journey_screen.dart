import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/models.dart';
import '../../../core/api/places.dart';
import '../../../theme/app_theme.dart';
import '../providers/plan_provider.dart';
import 'widgets/journey_live_map.dart';

enum JourneyState { initial, searching, results, active }

class JourneyScreen extends ConsumerStatefulWidget {
  const JourneyScreen({super.key});

  @override
  ConsumerState<JourneyScreen> createState() => _JourneyScreenState();
}

class _JourneyScreenState extends ConsumerState<JourneyScreen> {
  JourneyState _currentState = JourneyState.initial;
  PlanProfile _selectedProfile = PlanProfile.balanced;

  /// Set once the user searches; the provider owns loading and error state
  /// from there, so this screen never hand-rolls a spinner again.
  PlanQuery? _query;

  final TextEditingController _originController = TextEditingController();
  final TextEditingController _destController = TextEditingController();

  Future<void> _handleSearch() async {
    if (_originController.text.isEmpty || _destController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter an origin and destination.')),
      );
      return;
    }

    final origin = findPlace(_originController.text);
    final destination = findPlace(_destController.text);
    if (origin == null || destination == null) {
      final unknown = origin == null ? _originController.text : _destController.text;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not find "$unknown". Pick a suggestion.')),
      );
      return;
    }
    if (origin.name == destination.name) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Origin and destination are the same.')),
      );
      return;
    }

    setState(() {
      _query = PlanQuery(
        origin: origin,
        destination: destination,
        profile: _selectedProfile,
      );
      _currentState = JourneyState.results;
    });
  }

  void _startJourney() {
    setState(() => _currentState = JourneyState.active);
  }

  void _endJourney() {
    setState(() {
      _currentState = JourneyState.initial;
      _originController.clear();
      _destController.clear();
    });
  }

  @override
  void dispose() {
    _originController.dispose();
    _destController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        bottom: false,
        child: CustomScrollView(
          slivers: [
            SliverPadding(
              padding: const EdgeInsets.all(24.0),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  if (_currentState == JourneyState.active)
                    _buildActiveMode()
                  else
                    _buildPlanningMode(),
                  const SizedBox(height: 120),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanningMode() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Plan Journey',
          style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
          ),
        ),
        const SizedBox(height: 24),
        
        // Inputs
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [
              BoxShadow(color: AppTheme.cardShadow, blurRadius: 10, offset: Offset(0, 4)),
            ],
          ),
          child: Column(
            children: [
              _buildLocationInput(Icons.my_location, 'Your Location (e.g. Connaught Place)', AppTheme.primaryBlue, _originController),
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Icon(Icons.more_vert, color: AppTheme.textSecondary),
                ),
              ),
              _buildLocationInput(Icons.location_on, 'Destination (e.g. Anand Vihar ISBT)', Colors.redAccent, _destController),
            ],
          ),
        ),
        const SizedBox(height: 24),
        
        // Preferences
        Text('Preferences', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          children: [
            _buildPreferenceChip(PlanProfile.fastest),
            _buildPreferenceChip(PlanProfile.leastCrowded),
            _buildPreferenceChip(PlanProfile.mostReliable),
            _buildPreferenceChip(PlanProfile.balanced),
          ],
        ),
        const SizedBox(height: 32),
        
        // Action Button or Results
        if (_currentState == JourneyState.initial)
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _handleSearch,
              child: const Text('Search Routes'),
            ),
          )
        else if (_currentState == JourneyState.searching)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(32.0),
              child: CircularProgressIndicator(color: AppTheme.primaryBlue),
            ),
          )
        else if (_currentState == JourneyState.results) ...[
          _buildResults(),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () {
                setState(() {
                  _currentState = JourneyState.initial;
                  _query = null;
                });
              },
              child: const Text('Clear Search'),
            ),
          )
        ]
      ],
    );
  }

  /// Ranked options straight from `/v1/plan`.
  ///
  /// Loading, empty and error are all rendered explicitly. A transport app that
  /// shows a blank list when the network fails is worse than one that says so.
  Widget _buildResults() {
    final query = _query;
    if (query == null) return const SizedBox.shrink();

    return ref.watch(planProvider(query)).when(
          loading: () => const Center(
            child: Padding(
              padding: EdgeInsets.all(32.0),
              child: CircularProgressIndicator(color: AppTheme.primaryBlue),
            ),
          ),
          error: (error, _) => _buildError(error),
          data: (plan) {
            if (plan.options.isEmpty) {
              return _buildNotice(
                Icons.search_off,
                'No direct service found between these stops in the next hour.',
              );
            }
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text('Suggested Routes',
                        style: Theme.of(context).textTheme.titleLarge),
                    const Spacer(),
                    Text('${plan.options.length} options',
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 12)),
                  ],
                ),
                const SizedBox(height: 16),
                for (final option in plan.options) _buildOptionCard(option),
              ],
            );
          },
        );
  }

  Widget _buildError(Object error) {
    final message = error is ApiException
        ? error.friendlyMessage
        : 'Could not plan this journey.';
    return _buildNotice(Icons.cloud_off, message, retry: true);
  }

  Widget _buildNotice(IconData icon, String message, {bool retry = false}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.textSecondary.withAlpha(40)),
      ),
      child: Column(
        children: [
          Icon(icon, color: AppTheme.textSecondary, size: 32),
          const SizedBox(height: 12),
          Text(message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textSecondary)),
          if (retry) ...[
            const SizedBox(height: 12),
            TextButton(
              onPressed: () {
                final q = _query;
                if (q != null) ref.invalidate(planProvider(q));
              },
              child: const Text('Try again'),
            ),
          ],
        ],
      ),
    );
  }

  /// One ranked option. Every reason string comes from the API verbatim.
  Widget _buildOptionCard(JourneyOption option) {
    final crowd = option.boardingCrowd;
    return GestureDetector(
      onTap: _startJourney,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: option.isRecommended
              ? Border.all(color: AppTheme.primaryBlue, width: 2)
              : null,
          boxShadow: const [
            BoxShadow(
                color: AppTheme.cardShadow, blurRadius: 4, offset: Offset(0, 2)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppTheme.primaryBlue.withAlpha(20),
                  child: const Icon(Icons.directions_bus,
                      color: AppTheme.primaryBlue),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(option.routeLabel,
                          style: const TextStyle(
                              fontWeight: FontWeight.bold, fontSize: 16)),
                      if (option.legs.isNotEmpty)
                        Text(
                          '${option.legs.first.boardStopName} to '
                          '${option.legs.first.alightStopName}',
                          style: const TextStyle(
                              color: AppTheme.textSecondary, fontSize: 12),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('${option.totalMinutes} min',
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 16)),
                    if (option.isRecommended)
                      const Text('Recommended',
                          style: TextStyle(
                              color: AppTheme.primaryBlue,
                              fontSize: 11,
                              fontWeight: FontWeight.bold)),
                  ],
                ),
              ],
            ),
            if (crowd != null) ...[
              const SizedBox(height: 12),
              _buildCrowdBand(crowd),
            ],
            const SizedBox(height: 12),
            // Rule 3: every ranked option shows its reason, and the text is the
            // server's -- the client never invents an explanation.
            for (final reason in option.reasons)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.only(top: 2),
                      child: Icon(Icons.check_circle_outline,
                          size: 14, color: AppTheme.textSecondary),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(reason,
                          style: const TextStyle(
                              fontSize: 12, color: AppTheme.textSecondary)),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// A forecast is a band, never a point (section 33.3 rule 2), and crowding is
  /// never conveyed by colour alone (section 33.5) -- so the label is text.
  Widget _buildCrowdBand(CrowdBand crowd) {
    final colour = _crowdColour(crowd.p50);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: colour.withAlpha(18),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: colour.withAlpha(70)),
      ),
      child: Row(
        children: [
          Icon(crowd.isKnown ? Icons.people_outline : Icons.help_outline,
              size: 16, color: colour),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(crowd.summary,
                    style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: colour)),
                if (crowd.isKnown && crowd.p50Onboard != null)
                  Text(
                    'when you board · ${crowd.p10Onboard}-${crowd.p90Onboard} '
                    'of ${crowd.capacity} onboard'
                    '${crowd.isFallback ? ' · estimated from history' : ''}',
                    style: const TextStyle(
                        fontSize: 10, color: AppTheme.textSecondary),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _crowdColour(CrowdLevel level) {
    switch (level) {
      case CrowdLevel.empty:
      case CrowdLevel.manySeats:
        return const Color(0xFF2E7D32);
      case CrowdLevel.fewSeats:
        return const Color(0xFF9E7B00);
      case CrowdLevel.standing:
        return const Color(0xFFD84315);
      case CrowdLevel.crushed:
      case CrowdLevel.full:
      case CrowdLevel.notAccepting:
        return const Color(0xFFB71C1C);
      case CrowdLevel.unknown:
        // Unknown is neutral grey. It must never look like "empty".
        return const Color(0xFF6B7280);
    }
  }

  Widget _buildLocationInput(IconData icon, String hint, Color iconColor, TextEditingController controller) {
    return Row(
      children: [
        Icon(icon, color: iconColor),
        const SizedBox(width: 16),
        Expanded(
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: hint,
              border: InputBorder.none,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPreferenceChip(PlanProfile profile) {
    final isSelected = _selectedProfile == profile;
    return ChoiceChip(
      label: Text(profile.label),
      selected: isSelected,
      onSelected: (bool selected) {
        if (!selected) return;
        setState(() {
          _selectedProfile = profile;
          // Re-rank immediately if results are already on screen: the whole
          // point is that the same candidates reorder for a different priority.
          final q = _query;
          if (q != null) {
            _query = PlanQuery(
              origin: q.origin,
              destination: q.destination,
              profile: profile,
            );
          }
        });
      },
      selectedColor: AppTheme.primaryBlue.withAlpha(30),
      labelStyle: TextStyle(
        color: isSelected ? AppTheme.primaryBlue : AppTheme.textPrimary,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
      ),
    );
  }

  Widget _buildActiveMode() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Premium Header Card (Compact)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          decoration: BoxDecoration(
            gradient: const RadialGradient(
              center: Alignment.topLeft,
              radius: 2.5,
              colors: [AppTheme.primaryBlue, Color(0xFF003A86)],
            ),
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(color: AppTheme.primaryBlue.withAlpha(80), blurRadius: 15, offset: const Offset(0, 8)),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withAlpha(40),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.white.withAlpha(80)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.satellite_alt_rounded, color: Colors.white, size: 12),
                        SizedBox(width: 4),
                        Text(
                          'Live Tracking',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: _endJourney,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'End Trip',
                        style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold, fontSize: 12),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              const Text(
                'Route 543',
                style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: -0.5),
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  Icon(Icons.arrow_forward_rounded, color: Colors.white.withAlpha(200), size: 14),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      _destController.text.isNotEmpty ? _destController.text : "Anand Vihar ISBT",
                      style: TextStyle(color: Colors.white.withAlpha(220), fontSize: 15, fontWeight: FontWeight.w500),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // RULE 6: SIMULATED DATA BANNER (Must be unmissable but premium)
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
          decoration: BoxDecoration(
            color: Colors.orange.shade50,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.orange.shade200, width: 1.5),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.orange.shade100, shape: BoxShape.circle),
                child: Icon(Icons.science_rounded, color: Colors.orange.shade800, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SIMULATED DATA (DEMO)',
                      style: TextStyle(
                        color: Colors.orange.shade900,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 0.5,
                        fontSize: 14,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Synthetic network traffic, not real Delhi data.',
                      style: TextStyle(color: Colors.orange.shade700, fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Embed the Map View
        const SizedBox(
          height: 250,
          width: double.infinity,
          child: JourneyLiveMap(),
        ),
        const SizedBox(height: 28),

        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Text('Journey Progress', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
        ),
        const SizedBox(height: 16),
        
        // Premium Live Progress Card
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(32),
            border: Border.all(color: Colors.grey.shade200, width: 1),
            boxShadow: [
              BoxShadow(color: AppTheme.cardShadow.withAlpha(15), blurRadius: 20, offset: const Offset(0, 10)),
            ],
          ),
          child: Column(
            children: [
              _buildPremiumStop('Connaught Place', '12:00', 'Departed', true, false, null),
              // Rule 2 explicitly shown: p10-p90 uncertainty band for forecasts
              _buildPremiumStop('India Gate', '12:05', 'Live ETA', false, true, _buildCrowdIndicator('CRUSHED_STANDING_ROOM_ONLY', '80-100% full (p10-p90)')), 
              // Rule 1 explicitly shown: Unknown is never empty.
              _buildPremiumStop('Nizamuddin', '12:15', 'Scheduled', false, false, _buildCrowdIndicator('UNKNOWN', 'No forecast data')),
              _buildPremiumStop(_destController.text.isNotEmpty ? _destController.text : 'Anand Vihar ISBT', '12:42', 'Scheduled', false, false, null, isLast: true),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCrowdIndicator(String occupancyClass, String forecastData) {
    Color chipColor;
    Color textColor;
    IconData icon;
    String friendlyName;

    switch (occupancyClass) {
      case 'CRUSHED_STANDING_ROOM_ONLY':
      case 'FULL':
        chipColor = Colors.red.shade50;
        textColor = Colors.red.shade700;
        icon = Icons.groups_rounded;
        friendlyName = 'Crush Load';
        break;
      case 'STANDING_ROOM_ONLY':
        chipColor = Colors.orange.shade50;
        textColor = Colors.orange.shade800;
        icon = Icons.group_rounded;
        friendlyName = 'Standing Only';
        break;
      case 'UNKNOWN':
        chipColor = Colors.grey.shade100;
        textColor = Colors.grey.shade600;
        icon = Icons.help_outline_rounded;
        friendlyName = 'Unknown';
        break;
      default: // Seats available
        chipColor = Colors.green.shade50;
        textColor = Colors.green.shade700;
        icon = Icons.event_seat_rounded;
        friendlyName = 'Seats Available';
    }

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: textColor.withAlpha(50)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: textColor),
          const SizedBox(width: 6),
          Flexible(
            child: Text(
              '$friendlyName • $forecastData',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: textColor),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPremiumStop(String name, String time, String status, bool isPast, bool isCurrent, Widget? crowdIndicator, {bool isLast = false}) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Time Column
          SizedBox(
            width: 50,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  time,
                  style: TextStyle(
                    fontWeight: isCurrent ? FontWeight.w900 : FontWeight.bold,
                    color: isPast ? AppTheme.textSecondary : (isCurrent ? AppTheme.primaryBlue : AppTheme.textPrimary),
                    fontSize: 15,
                  ),
                ),
                Text(
                  status,
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: isCurrent ? AppTheme.primaryBlue : AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          
          // Timeline Node
          Column(
            children: [
              Container(
                width: 20,
                height: 20,
                decoration: BoxDecoration(
                  color: isPast ? AppTheme.primaryBlue : (isCurrent ? Colors.white : Colors.grey.shade200),
                  shape: BoxShape.circle,
                  border: isCurrent ? Border.all(color: AppTheme.primaryBlue, width: 6) : null,
                  boxShadow: isCurrent ? [
                    BoxShadow(color: AppTheme.primaryBlue.withAlpha(100), blurRadius: 10, spreadRadius: 2)
                  ] : null,
                ),
                child: isPast ? const Icon(Icons.check, size: 12, color: Colors.white) : null,
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 3,
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    decoration: BoxDecoration(
                      color: isPast ? AppTheme.primaryBlue : Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(width: 16),
          
          // Content Column
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: TextStyle(
                      fontWeight: isCurrent ? FontWeight.w900 : FontWeight.bold,
                      color: isPast ? AppTheme.textSecondary : AppTheme.textPrimary,
                      fontSize: 17,
                    ),
                  ),
                  if (crowdIndicator != null) crowdIndicator,
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
