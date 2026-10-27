import 'package:flutter/foundation.dart';

/// Configurable Flask API base URL (no hardcoded LAN IP).
///
/// Override at build/run time:
/// `flutter run --dart-define=FL_API_BASE_URL=http://192.168.1.10:5000`
abstract final class ApiConfig {
  static const _envBase = String.fromEnvironment('FL_API_BASE_URL');

  static String get baseUrl {
    if (_envBase.trim().isNotEmpty) {
      return _envBase.trim().replaceAll(RegExp(r'/+$'), '');
    }
    if (kIsWeb) return 'http://127.0.0.1:5000';
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return 'http://10.0.2.2:5000';
      case TargetPlatform.iOS:
        return 'http://127.0.0.1:5000';
      default:
        return 'http://127.0.0.1:5000';
    }
  }
}
