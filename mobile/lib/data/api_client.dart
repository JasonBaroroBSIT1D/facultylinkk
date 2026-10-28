import 'dart:convert';

import 'package:http/http.dart' as http;

import 'api_config.dart';
import 'api_http.dart';
import 'app_auth_exception.dart';
import 'token_storage.dart';

class ApiClient {
  ApiClient({http.Client? httpClient, TokenStorage? tokenStorage})
      : _http = httpClient ?? http.Client(),
        _tokens = tokenStorage ?? TokenStorage();

  final http.Client _http;
  final TokenStorage _tokens;

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final data = await _postJson(
      '/api/auth/login',
      {
        'email': email.trim(),
        'password': password,
        'client': 'mobile',
      },
      authenticated: false,
    );
    final access = data['accessToken'] as String?;
    final refresh = data['refreshToken'] as String?;
    if (access == null || refresh == null) {
      throw AppAuthException('Invalid server response.', statusCode: 502);
    }
    await _tokens.saveTokens(accessToken: access, refreshToken: refresh);
    return data;
  }

  Future<Map<String, dynamic>> session() async {
    return _getJson('/api/auth/session', allowRefresh: true);
  }

  /// Current faculty member's assigned reviewer (`faculty_profiles.reviewer_user_id`).
  Future<Map<String, dynamic>> fetchFacultyMe() async {
    return _getJson('/api/faculty/me', authenticated: true, allowRefresh: true);
  }

  Future<Map<String, dynamic>> fetchFacultyDashboard() async {
    return _getJson('/api/faculty/me/dashboard', authenticated: true, allowRefresh: true);
  }

  Future<Map<String, dynamic>> fetchMyAssignedReviewer() async {
    return _getJson(
      '/api/faculty/me/reviewer',
      authenticated: true,
      allowRefresh: true,
    );
  }

  Future<List<Map<String, dynamic>>> fetchMyDocuments() async {
    final data = await _getJson(
      '/api/faculty/me/documents',
      authenticated: true,
      allowRefresh: true,
    );
    final rows = data['documents'];
    if (rows is! List) return [];
    return rows.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<Map<String, dynamic>> uploadFacultyDocument({
    required String title,
    required String kraId,
    required String criterionId,
    required String indicatorId,
    required String fileName,
    required List<int> fileBytes,
    String? replacesDocumentId,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/faculty/me/documents');
    Future<http.Response> send(String? bearer) async {
      final request = http.MultipartRequest('POST', uri);
      if (bearer != null && bearer.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $bearer';
      }
      request.fields['title'] = title;
      request.fields['kraId'] = kraId;
      request.fields['criterionId'] = criterionId;
      request.fields['indicatorId'] = indicatorId;
      if (replacesDocumentId != null && replacesDocumentId.isNotEmpty) {
        request.fields['replacesDocumentId'] = replacesDocumentId;
      }
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
        ),
      );
      final streamed = await apiSend(_http, request);
      return http.Response.fromStream(streamed);
    }

    var token = await _tokens.readAccessToken();
    var response = await send(token);
    if (response.statusCode == 401) {
      final refreshed = await _refreshAccessToken();
      if (refreshed != null) response = await send(refreshed);
    }
    _throwIfError(response);
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final doc = data['document'];
    if (doc is Map<String, dynamic>) return doc;
    return data;
  }

  Future<Map<String, dynamic>> submitFacultyDocument(String documentId) async {
    return _postJson(
      '/api/faculty/me/documents/$documentId/submit',
      {},
      authenticated: true,
    );
  }

  Future<List<int>> downloadFacultyDocumentBytes(String documentId) async {
    final path =
        '/api/faculty/me/documents/$documentId/file?disposition=inline';
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    Future<http.Response> send(String? bearer) async {
      return apiGet(
        _http,
        uri,
        headers: {
          if (bearer != null && bearer.isNotEmpty) 'Authorization': 'Bearer $bearer',
        },
      );
    }
    var token = await _tokens.readAccessToken();
    var response = await send(token);
    if (response.statusCode == 401) {
      final refreshed = await _refreshAccessToken();
      if (refreshed != null) response = await send(refreshed);
    }
    _throwIfError(response);
    return response.bodyBytes;
  }

  Future<void> logout() async {
    try {
      await _postJson('/api/auth/logout', {}, authenticated: true, allowRefresh: false);
    } finally {
      await _tokens.clear();
    }
  }

  Future<Map<String, dynamic>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    final data = await _postJson(
      '/api/auth/change-password',
      {
        'currentPassword': currentPassword,
        'newPassword': newPassword,
      },
      authenticated: true,
    );
    final access = data['accessToken'] as String?;
    final refresh = data['refreshToken'] as String?;
    if (access != null && refresh != null) {
      await _tokens.saveTokens(accessToken: access, refreshToken: refresh);
    }
    return data;
  }

  Future<Map<String, dynamic>> requestPasswordReset(String email) async {
    return _postJson(
      '/api/auth/forgot-password',
      {'email': email.trim()},
      authenticated: false,
    );
  }

  Future<String> verifyPasswordResetCode({
    required String email,
    required String code,
  }) async {
    final data = await _postJson(
      '/api/auth/forgot-password/verify',
      {'email': email.trim(), 'code': code.trim()},
      authenticated: false,
    );
    final token = data['resetToken'] as String?;
    if (token == null || token.isEmpty) {
      throw AppAuthException(
        'The code is invalid or has expired. Request a new code.',
        statusCode: 400,
      );
    }
    return token;
  }

  Future<String> resetPassword({
    required String email,
    required String resetToken,
    required String newPassword,
  }) async {
    final data = await _postJson(
      '/api/auth/forgot-password/reset',
      {
        'email': email.trim(),
        'resetToken': resetToken,
        'newPassword': newPassword,
      },
      authenticated: false,
    );
    return (data['message'] as String?) ??
        'Your password has been updated. Sign in with your new password.';
  }

  Future<bool> tryRestoreSession() async {
    final access = await _tokens.readAccessToken();
    if (access == null || access.isEmpty) return false;
    try {
      await session();
      return true;
    } on AppAuthException {
      await _tokens.clear();
      return false;
    } catch (_) {
      await _tokens.clear();
      return false;
    }
  }

  Future<Map<String, dynamic>> _getJson(
    String path, {
    bool authenticated = false,
    bool allowRefresh = true,
  }) async {
    final response = await _send(
      'GET',
      path,
      authenticated: authenticated,
      allowRefresh: allowRefresh,
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> _postJson(
    String path,
    Map<String, dynamic> body, {
    bool authenticated = false,
    bool allowRefresh = true,
  }) async {
    final response = await _send(
      'POST',
      path,
      body: body,
      authenticated: authenticated,
      allowRefresh: allowRefresh,
    );
    return _decode(response);
  }

  Future<http.Response> _send(
    String method,
    String path, {
    Map<String, dynamic>? body,
    bool authenticated = false,
    bool allowRefresh = true,
  }) async {
    Future<http.Response> once(String? bearer) async {
      final uri = Uri.parse('${ApiConfig.baseUrl}$path');
      final headers = {
        'Accept': 'application/json',
        if (body != null) 'Content-Type': 'application/json',
        if (bearer != null && bearer.isNotEmpty) 'Authorization': 'Bearer $bearer',
      };
      if (method == 'GET') {
        return apiGet(_http, uri, headers: headers);
      }
      return apiPost(
        _http,
        uri,
        headers: headers,
        body: jsonEncode(body ?? {}),
      );
    }

    var token = authenticated ? await _tokens.readAccessToken() : null;
    var response = await once(token);
    if (response.statusCode == 401 && authenticated && allowRefresh) {
      final refreshed = await _refreshAccessToken();
      if (refreshed != null) {
        response = await once(refreshed);
      }
    }
    _throwIfError(response);
    return response;
  }

  Future<String?> _refreshAccessToken() async {
    final refresh = await _tokens.readRefreshToken();
    if (refresh == null || refresh.isEmpty) return null;
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/auth/refresh');
    final response = await apiPost(
      _http,
      uri,
      headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $refresh',
      },
    );
    if (response.statusCode >= 400) return null;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final access = data['accessToken'] as String?;
    if (access == null) return null;
    await _tokens.saveTokens(accessToken: access, refreshToken: refresh);
    return access;
  }

  Map<String, dynamic> _decode(http.Response response) {
    if (response.body.isEmpty) return {};
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  void _throwIfError(http.Response response) {
    if (response.statusCode < 400) return;
    String message = 'Request failed.';
    String? code;
    try {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      message = (body['message'] as String?) ?? message;
      code = body['code'] as String?;
    } catch (_) {
      /* keep default */
    }
    throw AppAuthException(message, statusCode: response.statusCode, code: code);
  }
}
