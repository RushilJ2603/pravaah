import 'package:flutter_test/flutter_test.dart';
import 'package:pravaah_frontend/core/api/places.dart';

void main() {
  group('place suggestions', () {
    test('typing "con" suggests Connaught Place', () {
      final names = searchPlaces('con').map((p) => p.name).toList();
      expect(names, contains('Connaught Place'));
    });

    test('matching is case-insensitive and matches mid-string', () {
      expect(searchPlaces('KASHMERE').map((p) => p.name), contains('Kashmere Gate ISBT'));
      // "vihar" appears in the middle of several names, not just at the start.
      final vihar = searchPlaces('vihar').map((p) => p.name).toList();
      expect(vihar, contains('Anand Vihar ISBT'));
      expect(vihar, contains('Mayur Vihar'));
    });

    test('an empty query suggests nothing, rather than everything', () {
      expect(searchPlaces('').isEmpty, isTrue);
      expect(searchPlaces('   ').isEmpty, isTrue);
    });

    test('nonsense matches nothing', () {
      expect(searchPlaces('zzzzz').isEmpty, isTrue);
    });

    test('findPlace resolves an exact name to real coordinates', () {
      final cp = findPlace('Connaught Place');
      expect(cp, isNotNull);
      // Central Delhi, not null island and not Boston.
      expect(cp!.lat, closeTo(28.63, 0.05));
      expect(cp.lon, closeTo(77.22, 0.05));
    });

    test('findPlace resolves a unique prefix but refuses an ambiguous one', () {
      expect(findPlace('kashmere')?.name, 'Kashmere Gate ISBT');
      // "d" prefixes Defence Colony, Dwarka x2, Dilshad Garden -> ambiguous.
      expect(findPlace('d'), isNull);
    });

    test('every place carries plausible Delhi coordinates', () {
      for (final p in kDelhiPlaces) {
        expect(p.lat, inInclusiveRange(28.3, 28.9), reason: p.name);
        expect(p.lon, inInclusiveRange(76.8, 77.4), reason: p.name);
      }
    });
  });
}
