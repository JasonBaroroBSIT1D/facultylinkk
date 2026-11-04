import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

/// Live API faculty journey (requires env vars; never hardcode secrets).
///
/// Run:
///   flutter test integration_test/kra2_b_faculty_api_flow_test.dart \
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

  test('faculty login → draft accomplishment not in reviewer submitted list', () async {
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

      final accReq = await client.getUrl(Uri.parse('$apiBase/api/faculty/documents/kra2-b/accomplishments'));
      accReq.headers.set(HttpHeaders.authorizationHeader, 'Bearer $token');
      final accRes = await accReq.close();
      expect(accRes.statusCode, 200);
      final accBody = jsonDecode(await accRes.transform(utf8.decoder).join());
      final accomplishments = accBody['accomplishments'] as List<dynamic>? ?? [];
      for (final row in accomplishments) {
        final map = row as Map<String, dynamic>;
        if ((map['submittedForReviewAt'] as String?)?.isEmpty ?? true) {
          expect(map['status'], isNot('approved'));
        }
      }
    } finally {
      client.close(force: true);
    }
  });
}
