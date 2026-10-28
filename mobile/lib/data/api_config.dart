import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';

/// Configurable Flask API base URL (no hardcoded LAN IP).
///
/// Override at build/run time with `--dart-define`:
///
/// | Scenario | Example |
/// |----------|---------|
/// | Flutter Web (default) | `http://127.0.0.1:5000` |
/// | Android emulator | `http://10.0.2.2:5000` (auto when not physical) |
/// | Android USB + `adb reverse` | `http://127.0.0.1:5000` (auto on physical device) |
/// | Android on same Wi‑Fi | `--dart-define=FL_API_BASE_URL=http://192.168.x.x:5000` |
/// | Production HTTPS | `--dart-define=FL_API_BASE_URL=https://api.example.com` |
///
/// Optional: `--dart-define=FL_ANDROID_API_HOST=emulator|device` to force host
/// when auto-detection is wrong.
abstract final class ApiConfig {
  static const _envBase = String.fromEnvironment('FL_API_BASE_URL');
  static const _androidHostMode =
      String.fromEnvironment('FL_ANDROID_API_HOST', defaultValue: 'auto');

  /// Max time to complete an HTTP request (connect + response).
  static const Duration requestTimeout = Duration(seconds: 20);

  static String? _resolvedBaseUrl;
  static bool _initialized = false;

  static bool get isInitialized => _initialized;

  /// Call once from [main] before any API traffic (recommended on mobile).
  static Future<void> initialize() async {
    if (_initialized) return;
    _resolvedBaseUrl = await _resolveBaseUrl();
    _initialized = true;
  }

  static String get baseUrl {
    if (_resolvedBaseUrl != null) return _resolvedBaseUrl!;
    return _syncDefaultBaseUrl();
  }

  /// Host label for user-facing errors (no credentials).
  static String get displayHost {
    final uri = Uri.tryParse(baseUrl);
    if (uri == null || uri.host.isEmpty) return baseUrl;
    final port = uri.hasPort ? ':${uri.port}' : '';
    return '${uri.scheme}://${uri.host}$port';
  }

  static Future<String> _resolveBaseUrl() async {
    final fromEnv = _envBase.trim();
    if (fromEnv.isNotEmpty) {
      return fromEnv.replaceAll(RegExp(r'/+$'), '');
    }
    if (kIsWeb) return 'http://127.0.0.1:5000';

    if (defaultTargetPlatform == TargetPlatform.android) {
      final mode = _androidHostMode.trim().toLowerCase();
      if (mode == 'emulator') return 'http://10.0.2.2:5000';
      if (mode == 'device' || mode == 'physical') {
        return 'http://127.0.0.1:5000';
      }
      try {
        final info = await DeviceInfoPlugin().androidInfo;
        if (info.isPhysicalDevice) {
          return 'http://127.0.0.1:5000';
        }
        return 'http://10.0.2.2:5000';
      } catch (_) {
        /* fall through to emulator default */
      }
      return 'http://10.0.2.2:5000';
    }

    return _syncDefaultBaseUrl();
  }

  static String _syncDefaultBaseUrl() {
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
