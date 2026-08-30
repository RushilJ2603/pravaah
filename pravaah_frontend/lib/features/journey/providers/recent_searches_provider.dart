import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/api/places.dart';

class RecentSearchesNotifier extends Notifier<List<DelhiPlace>> {
  @override
  List<DelhiPlace> build() {
    // Provide some default Delhi locations for the demo when the app first launches.
    // Use safe index lookups to avoid StateError if place names ever change.
    return kDelhiPlaces
        .where((p) =>
            p.name == 'Connaught Place' ||
            p.name == 'Red Fort' ||
            p.name == 'Karol Bagh')
        .take(3)
        .toList();
  }

  void addSearch(DelhiPlace destination) {
    // Add the new destination to the top, remove duplicates, and keep the latest 3
    final newList = [
      destination,
      ...state.where((p) => p.name != destination.name)
    ];
    state = newList.take(3).toList();
  }
}

final recentSearchesProvider = NotifierProvider<RecentSearchesNotifier, List<DelhiPlace>>(() {
  return RecentSearchesNotifier();
});
