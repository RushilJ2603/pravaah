import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pravaah_api/api.dart';
import '../../../../theme/app_theme.dart';
import '../../../core/api_provider.dart';
import '../../../core/api/places.dart';
import 'widgets/journey_live_map.dart';
import 'package:intl/intl.dart';

enum JourneyState { initial, searching, results, active }

class JourneyScreen extends ConsumerStatefulWidget {
  const JourneyScreen({super.key});

  @override
  ConsumerState<JourneyScreen> createState() => _JourneyScreenState();
}

class _JourneyScreenState extends ConsumerState<JourneyScreen> {
  JourneyState _currentState = JourneyState.initial;
  String _selectedPreference = 'Fastest';

  final TextEditingController _originController = TextEditingController();
  final TextEditingController _destController = TextEditingController();

  DelhiPlace? _originPlace;
  DelhiPlace? _destPlace;
  PlanResponse? _planResponse;
  JourneyOption? _selectedOption;

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
        SnackBar(content: Text('Could not find "$unknown". Try another location.')),
      );
      return;
    }

    setState(() {
      _currentState = JourneyState.searching;
      _originPlace = origin;
      _destPlace = destination;
    });
    
    try {
      final api = ref.read(passengerApiProvider);
      // Convert UI preference to backend expected format (e.g. "Least Crowded" -> "least_crowded")
      String apiProfile = _selectedPreference.toLowerCase().replaceAll(' ', '_');
      
      // Use dynamic coordinates from places.dart
      final response = await api.planV1PlanGet(origin.lat, origin.lon, destination.lat, destination.lon, profile: apiProfile);
      
      if (mounted) {
        setState(() {
          _planResponse = response;
          _currentState = JourneyState.results;
        });
      }
    } catch (e) {
      if (mounted) {
         ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Search failed: $e')));
         setState(() => _currentState = JourneyState.initial);
      }
    }
  }

  void _startJourney(JourneyOption option) {
    setState(() {
      _selectedOption = option;
      _currentState = JourneyState.active;
    });
  }

  void _endJourney() {
    setState(() {
      _currentState = JourneyState.initial;
      _selectedOption = null;
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
                  if (_currentState == JourneyState.active && _selectedOption != null)
                    _buildActiveMode(_selectedOption!)
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
            _buildPreferenceChip('Fastest'),
            _buildPreferenceChip('Least Crowded'),
            _buildPreferenceChip('Balanced'),
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
        else if (_currentState == JourneyState.results && _planResponse != null) ...[
          Text('Suggested Routes', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          
          ...() {
            final sorted = List<JourneyOption>.from(_planResponse!.options);
            if (_selectedPreference == 'Fastest') {
              sorted.sort((a, b) => a.totalMinutes.compareTo(b.totalMinutes));
            } else if (_selectedPreference == 'Least Crowded') {
              sorted.sort((a, b) {
                final aRatio = a.legs.isNotEmpty ? (a.legs.first.crowd?.p50Ratio?.toDouble() ?? 1.0) : 1.0;
                final bRatio = b.legs.isNotEmpty ? (b.legs.first.crowd?.p50Ratio?.toDouble() ?? 1.0) : 1.0;
                return aRatio.compareTo(bRatio);
              });
            } else { // Balanced: blend of time and crowd
              sorted.sort((a, b) {
                final aRatio = a.legs.isNotEmpty ? (a.legs.first.crowd?.p50Ratio?.toDouble() ?? 1.0) : 1.0;
                final bRatio = b.legs.isNotEmpty ? (b.legs.first.crowd?.p50Ratio?.toDouble() ?? 1.0) : 1.0;
                final aScore = a.totalMinutes * 0.6 + aRatio * 100 * 0.4;
                final bScore = b.totalMinutes * 0.6 + bRatio * 100 * 0.4;
                return aScore.compareTo(bScore);
              });
            }
            return sorted.asMap().entries.map((entry) {
              return _buildRankedOption(entry.value, entry.key == 0);
            });
          }(),

          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () {
                setState(() => _currentState = JourneyState.initial);
              },
              child: const Text('Clear Search'),
            ),
          )
        ]
      ],
    );
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

  Widget _buildPreferenceChip(String label) {
    final isSelected = _selectedPreference == label;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (bool selected) {
        if (selected) {
          setState(() => _selectedPreference = label);
          // If a search was already performed, immediately re-fetch with new profile
          if (_originPlace != null && _destPlace != null) {
            _handleSearch();
          }
        }
      },
      selectedColor: AppTheme.primaryBlue.withAlpha(30),
      labelStyle: TextStyle(
        color: isSelected ? AppTheme.primaryBlue : AppTheme.textPrimary,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
      ),
    );
  }

  Widget _buildRankedOption(JourneyOption option, bool isPrimary) {
    final title = option.legs.isNotEmpty ? "Route ${option.legs.first.routeId}" : "Walk";
    final eta = "${option.totalMinutes} mins";
    
    String reasonText = isPrimary ? 'Recommended Route' : 'Alternative Route';
    if (option.reasons.isNotEmpty) {
      reasonText = (isPrimary ? 'Recommended: ' : 'Alternative: ') + option.reasons.join(', ');
    } else if (option.isRecommended) {
       reasonText = 'Recommended Route';
    }

    return GestureDetector(
      onTap: () => _startJourney(option),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: isPrimary ? Border.all(color: AppTheme.primaryBlue, width: 2) : null,
          boxShadow: const [
            BoxShadow(color: AppTheme.cardShadow, blurRadius: 4, offset: Offset(0, 2)),
          ],
        ),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: AppTheme.primaryBlue.withAlpha(20),
              child: const Icon(Icons.directions_bus, color: AppTheme.primaryBlue),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(eta, style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryBlue)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    reasonText,
                    style: TextStyle(
                      color: isPrimary ? Colors.green : AppTheme.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveMode(JourneyOption option) {
    final title = option.legs.isNotEmpty ? "Route ${option.legs.first.routeId}" : "Walk";
    final dest = option.legs.isNotEmpty ? option.legs.last.alightStopName : (_destController.text.isNotEmpty ? _destController.text : "Destination");
    
    // We can pull the departure and arrival times from the option
    final depFormat = DateFormat.Hm().format(option.departure.toLocal());
    final arrFormat = DateFormat.Hm().format(option.arrival.toLocal());

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
              Text(
                title,
                style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: -0.5),
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  Icon(Icons.arrow_forward_rounded, color: Colors.white.withAlpha(200), size: 14),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      dest,
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

        // RULE 6: SIMULATED DATA BANNER
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
        SizedBox(
          height: 250,
          width: double.infinity,
          child: JourneyLiveMap(
            option: option,
            originPlace: _originPlace,
            destPlace: _destPlace,
          ),
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
              _buildPremiumStop(option.legs.isNotEmpty ? option.legs.first.boardStopName : 'Start', depFormat, 'Departed', true, false, null),
              
              if (option.legs.isNotEmpty)
                _buildPremiumStop(option.legs.first.alightStopName, arrFormat, 'Live ETA', false, true, _buildCrowdIndicator(option.legs.first.crowd.p50Class.toString(), 'Estimated load')), 
              
              _buildPremiumStop(dest, arrFormat, 'Scheduled', false, false, null, isLast: true),
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
