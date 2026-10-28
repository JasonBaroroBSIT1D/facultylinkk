import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'api_config.dart';
import 'app_auth_exception.dart';

Future<http.Response> apiGet(
  http.Client client,
  Uri uri, {
  Map<String, String>? headers,
}) {
  return _guard(
    client.get(uri, headers: headers),
  );
}

Future<http.Response> apiPost(
  http.Client client,
  Uri uri, {
  Map<String, String>? headers,
  Object? body,
}) {
  return _guard(
    client.post(uri, headers: headers, body: body),
  );
}

Future<http.StreamedResponse> apiSend(
  http.Client client,
  http.BaseRequest request,
) {
  return _guard(client.send(request));
}

Future<T> _guard<T>(Future<T> future) async {
  try {
    return await future.timeout(ApiConfig.requestTimeout);
  } on TimeoutException {
    throw AppAuthException(
      'The FacultyLink server did not respond in time (${ApiConfig.displayHost}). '
      'Check that the API is running and that this device can reach it.',
      statusCode: 408,
    );
  } on http.ClientException catch (error) {
    throw AppAuthException(
      'Cannot reach the FacultyLink API at ${ApiConfig.displayHost}. '
      '${_connectionHint(error.message)}',
      statusCode: 503,
    );
  }
}

String _connectionHint(String message) {
  final parts = <String>[];
  if (message.trim().isNotEmpty) parts.add(message.trim());
  if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
    parts.add(
      'USB: adb reverse tcp:5000 tcp:5000 then use http://127.0.0.1:5000. '
      'Wi‑Fi: flutter run --dart-define=FL_API_BASE_URL=http://YOUR_PC_LAN_IP:5000',
    );
  } else if (kIsWeb) {
    parts.add(
      'Ensure Flask is running on port 5000 and restart it after CORS config changes.',
    );
  } else {
    parts.add('Verify the backend is running and the API URL matches this device.');
  }
  return parts.join(' ');
}
