import 'package:flutter/foundation.dart';

/// Where the backend lives.
///
/// The base URL was previously hardcoded to `http://localhost:8000`, which is
/// correct for exactly one of the four ways this app gets run:
///
///   * web / desktop     -> localhost works
///   * Android emulator  -> the host machine is 10.0.2.2, not localhost
///   * physical device   -> needs the host's LAN address
///   * public demo       -> an HTTPS tunnel or deployed host
///
/// So it is a compile-time constant that can be overridden without touching
/// source:
///
///   flutter run --dart-define=PRAVAAH_API_BASE=`https://your-host.example.com`
class ApiConfig {
  const ApiConfig._();

  static const String _override =
      String.fromEnvironment('PRAVAAH_API_BASE', defaultValue: '');

  /// Where the API lives for viewers who are NOT on this machine.
  ///
  /// The demo is shown two ways at once: from localhost on the presenter's
  /// laptop, and over a public tunnel for anyone else. A compile-time base can
  /// only serve one of those, and baking the tunnel in breaks the laptop the
  /// moment the tunnel dies. So the page decides at runtime from its own
  /// origin, and this is only consulted when that origin is not local.
  static const String _remote =
      String.fromEnvironment('PRAVAAH_REMOTE_API_BASE', defaultValue: '');

  static bool _isLocalHost(String host) =>
      host == 'localhost' || host == '127.0.0.1' || host == '::1';

  /// Base URL, with a platform-appropriate default when nothing is defined.
  static String get baseUrl {
    if (_override.isNotEmpty) return _stripTrailingSlash(_override);
    if (kIsWeb) {
      // Served from the presenter's machine: the API is on the same machine.
      // Served from anywhere else: use the public API if one was configured,
      // otherwise fall back to the page's own origin.
      if (_isLocalHost(Uri.base.host)) return 'http://localhost:8000';
      if (_remote.isNotEmpty) return _stripTrailingSlash(_remote);
      return _stripTrailingSlash('${Uri.base.scheme}://${Uri.base.authority}');
    }
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      // 10.0.2.2 is the Android emulator's alias for the host machine's
      // loopback. On a physical device this must be overridden with the
      // host's LAN address or a public URL.
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  /// True when talking to a plain-HTTP host. Android blocks cleartext by
  /// default, so the UI can warn instead of failing with an opaque socket error.
  static bool get isCleartext => baseUrl.startsWith('http://');

  static Duration get timeout => const Duration(seconds: 20);

  static String _stripTrailingSlash(String value) =>
      value.endsWith('/') ? value.substring(0, value.length - 1) : value;
}
