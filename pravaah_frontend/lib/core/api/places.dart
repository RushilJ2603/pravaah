/// Named Delhi landmarks with real coordinates.
///
/// `/v1/plan` takes coordinates, but a passenger types a place name. Until the
/// backend exposes a stop-search endpoint, this list bridges the two. Every
/// entry is a real Delhi location at its real position, and each is a landmark
/// stop on the generated network — so a journey between any two of them
/// resolves to actual services.
class DelhiPlace {
  const DelhiPlace(this.name, this.lat, this.lon);
  final String name;
  final double lat;
  final double lon;

  @override
  String toString() => name;
}

const List<DelhiPlace> kDelhiPlaces = [
  DelhiPlace('Connaught Place', 28.6315, 77.2167),
  DelhiPlace('New Delhi Railway Station', 28.6425, 77.2199),
  DelhiPlace('Paharganj', 28.6465, 77.2120),
  DelhiPlace('Chandni Chowk', 28.6506, 77.2303),
  DelhiPlace('Red Fort', 28.6562, 77.2410),
  DelhiPlace('Kashmere Gate ISBT', 28.6675, 77.2285),
  DelhiPlace('Civil Lines', 28.6820, 77.2230),
  DelhiPlace('India Gate', 28.6129, 77.2295),
  DelhiPlace('Mandi House', 28.6258, 77.2340),
  DelhiPlace('ITO', 28.6289, 77.2410),
  DelhiPlace('AIIMS', 28.5672, 77.2100),
  DelhiPlace('Green Park', 28.5590, 77.2070),
  DelhiPlace('Hauz Khas', 28.5494, 77.2001),
  DelhiPlace('Malviya Nagar', 28.5355, 77.2110),
  DelhiPlace('Saket', 28.5245, 77.2066),
  DelhiPlace('Chirag Delhi', 28.5400, 77.2240),
  DelhiPlace('Nehru Place', 28.5494, 77.2500),
  DelhiPlace('Kalkaji', 28.5490, 77.2590),
  DelhiPlace('Govindpuri', 28.5390, 77.2630),
  DelhiPlace('Lajpat Nagar', 28.5700, 77.2430),
  DelhiPlace('Defence Colony', 28.5730, 77.2300),
  DelhiPlace('Moolchand', 28.5680, 77.2350),
  DelhiPlace('Ashram', 28.5720, 77.2590),
  DelhiPlace('Sarai Kale Khan ISBT', 28.5900, 77.2580),
  DelhiPlace('Nizamuddin', 28.5890, 77.2510),
  DelhiPlace('Badarpur', 28.4930, 77.3020),
  DelhiPlace('Tughlakabad', 28.5070, 77.2600),
  DelhiPlace('Vasant Kunj', 28.5200, 77.1590),
  DelhiPlace('Munirka', 28.5540, 77.1740),
  DelhiPlace('RK Puram', 28.5640, 77.1800),
  DelhiPlace('Karol Bagh', 28.6510, 77.1900),
  DelhiPlace('Rajouri Garden', 28.6490, 77.1200),
  DelhiPlace('Tilak Nagar', 28.6390, 77.0950),
  DelhiPlace('Janakpuri', 28.6210, 77.0810),
  DelhiPlace('Uttam Nagar', 28.6210, 77.0590),
  DelhiPlace('Dwarka Sector 21', 28.5520, 77.0580),
  DelhiPlace('Dwarka Mor', 28.6190, 77.0330),
  DelhiPlace('Najafgarh', 28.6090, 76.9800),
  DelhiPlace('Punjabi Bagh', 28.6740, 77.1310),
  DelhiPlace('Vikas Puri', 28.6370, 77.0680),
  DelhiPlace('Naraina', 28.6300, 77.1400),
  DelhiPlace('Azadpur', 28.7070, 77.1750),
  DelhiPlace('Model Town', 28.7020, 77.1930),
  DelhiPlace('Pitampura', 28.6980, 77.1320),
  DelhiPlace('Rohini Sector 18', 28.7380, 77.1200),
  DelhiPlace('Jahangirpuri', 28.7290, 77.1620),
  DelhiPlace('GTB Nagar', 28.6990, 77.2070),
  DelhiPlace('Mukherjee Nagar', 28.7050, 77.2110),
  DelhiPlace('Wazirabad', 28.7180, 77.2300),
  DelhiPlace('Narela', 28.8530, 77.0920),
  DelhiPlace('Alipur', 28.7970, 77.1350),
  DelhiPlace('Anand Vihar ISBT', 28.6470, 77.3160),
  DelhiPlace('Preet Vihar', 28.6410, 77.2950),
  DelhiPlace('Laxmi Nagar', 28.6300, 77.2770),
  DelhiPlace('Mayur Vihar', 28.6090, 77.2950),
  DelhiPlace('Shahdara', 28.6730, 77.2890),
  DelhiPlace('Seelampur', 28.6700, 77.2670),
  DelhiPlace('Welcome', 28.6720, 77.2780),
  DelhiPlace('Dilshad Garden', 28.6810, 77.3210),
  DelhiPlace('Vivek Vihar', 28.6720, 77.3150),
  DelhiPlace('Yamuna Vihar', 28.6960, 77.2720),
];

/// Case-insensitive substring match, for the origin/destination autocomplete.
Iterable<DelhiPlace> searchPlaces(String query) {
  final q = query.trim().toLowerCase();
  if (q.isEmpty) return const [];
  return kDelhiPlaces.where((p) => p.name.toLowerCase().contains(q));
}

DelhiPlace? findPlace(String name) {
  final n = name.trim().toLowerCase();
  for (final p in kDelhiPlaces) {
    if (p.name.toLowerCase() == n) return p;
  }
  // Fall back to a unique prefix match so "kashmere" resolves.
  final matches = kDelhiPlaces.where((p) => p.name.toLowerCase().startsWith(n));
  return matches.length == 1 ? matches.first : null;
}
