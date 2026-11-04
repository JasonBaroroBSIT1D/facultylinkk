import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

/// Live API faculty KRA III journey (requires env vars; never hardcode secrets).
///
/// Run:
///   flutter test integration_test/kra3_faculty_api_flow_test.dart \
///     --dart-define=FLUTTER_TEST_API_BASE=http://127.0.0.1:5000 \
///     --dart-define=QA_FACULTY_EMAIL=... --dart-define=QA_FACULTY_PASSWORD=...
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  final apiBase = const String.fromEnvironment(
    'FLUTTER_TEST_API_BASE',
    defaultValue: 'http://127.0.0.1:5000',
  );
  final email = const String.fromEnvironment('QA_FACULTY_EMAIL');
  final password = const String.fromEnvironment('QA_FACULTY_PASSWORD');

  test('faculty login → KRA III criterion summaries respond', () async {
    if (email.isEmpty || password.isEmpty) {
      markTestSkipped('Set QA_FACULTY_EMAIL and QA_FACULTY_PASSWORD via --dart-define');
    }

    final client = HttpClient();
    try {
      final loginReq = await client.postUrl(Uri.parse('$apiBase/api/auth/login'));
      loginReq.headers.contentType = ContentType.json;
      loginReq.write(jsonEncode({
        'email': email,
        'password': password,
        'client': 'mobile',
      }));
      final loginRes = await loginReq.close();
      expect(loginRes.statusCode, 200);
      final loginBody = jsonDecode(await loginRes.transform(utf8.decoder).join());
      final token = loginBody['accessToken'] ?? loginBody['access_token'];
      expect(token, isNotNull);

      for (final criterion in ['kra3-a', 'kra3-b', 'kra3-c', 'kra3-d']) {
        final summaryReq = await client.getUrl(
          Uri.parse('$apiBase/api/faculty/me/$criterion/summary'),
        );
        summaryReq.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
        final summaryRes = await summaryReq.close();
        expect(summaryRes.statusCode, 200, reason: criterion);
        final summaryBody = jsonDecode(await summaryRes.transform(utf8.decoder).join());
        expect(summaryBody, isA<Map<String, dynamic>>());
      }

      final accReq = await client.getUrl(
        Uri.parse('$apiBase/api/faculty/me/kra3-a/accomplishments'),
      );
      accReq.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
      final accRes = await accReq.close();
      expect(accRes.statusCode, 200);
    } finally {
      client.close(force: true);
    }
  });
}
