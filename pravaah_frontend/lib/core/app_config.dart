/// Application configuration loaded from --dart-define at build/run time.
///
/// Usage:
///   flutter run --dart-define=BACKEND_URL=https://your-tunnel.trycloudflare.com
///   flutter build apk --dart-define=BACKEND_URL=https://your-tunnel.trycloudflare.com
///
/// Falls back to a placeholder so the app still compiles without the flag.
class AppConfig {
  AppConfig._();

  static const String backendUrl = String.fromEnvironment(
    'BACKEND_URL',
    defaultValue: 'https://motels-troubleshooting-detector-dee.trycloudflare.com',
  );
}
