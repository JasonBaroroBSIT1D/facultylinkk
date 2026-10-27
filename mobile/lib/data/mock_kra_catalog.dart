import 'dart:convert';

import 'package:flutter/services.dart';

/// Annex I KRA catalog bundled for offline UI (JC No. 01, s. 2026 structure).
abstract final class MockKraCatalog {
  static Future<Map<String, dynamic>> load() async {
    final raw = await rootBundle.loadString('assets/kra_catalog.json');
    final decoded = jsonDecode(raw);
    if (decoded is Map<String, dynamic>) return decoded;
    if (decoded is Map) return Map<String, dynamic>.from(decoded);
    return {'kras': []};
  }
}
