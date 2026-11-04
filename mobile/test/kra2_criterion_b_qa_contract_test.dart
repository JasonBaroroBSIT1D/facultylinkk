import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Validates the latest backend live QA JSON (when present).
void main() {
  test('live QA report shows seven families exercised', () {
    final path = Platform.environment['KRA2_B_QA_REPORT'] ??
        '../../docs/KRA2_CRITERION_B_LIVE_QA_REPORT.json';
    final file = File(path);
    if (!file.existsSync()) {
      // Backend harness not run in this environment.
      return;
    }
    final report = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
    final families = report['families'] as Map<String, dynamic>;
    expect(families.length, 7);
    for (final key in [
      'patent',
      'patent_co',
      'commercialization',
      'utility_model',
      'industrial_design',
      'software',
      'variety',
    ]) {
      expect(families.containsKey(key), isTrue, reason: key);
      final row = families[key] as Map<String, dynamic>;
      expect(row['indicatorId'], isNotEmpty);
      final checks = row['checks'] as Map<String, dynamic>?;
      if (checks != null) {
        expect(checks['upload_stays_draft'], isTrue, reason: '$key draft');
      }
    }
  });
}
