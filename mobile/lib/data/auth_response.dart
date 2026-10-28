/// Parses Flask `/api/auth/*` JSON bodies (login, session, change-password).
abstract final class AuthResponse {
  static const passwordChangeRequiredCode = 'PASSWORD_CHANGE_REQUIRED';
  static const minPasswordLength = 8;

  static bool mustChangePassword(Map<String, dynamic> data) {
    if (_flag(data['mustChangePassword'])) return true;
    final session = data['session'];
    if (session is Map && _flag(session['mustChangePassword'])) return true;
    final user = data['user'];
    if (user is Map && _flag(user['mustChangePassword'])) return true;
    return false;
  }

  static String? userId(Map<String, dynamic> data) {
    final session = data['session'];
    if (session is Map) {
      final id = session['userId'];
      if (id is String && id.isNotEmpty) return id;
    }
    final user = data['user'];
    if (user is Map) {
      final id = user['id'];
      if (id is String && id.isNotEmpty) return id;
    }
    return null;
  }

  static String? email(Map<String, dynamic> data) {
    final user = data['user'];
    if (user is Map) {
      final value = user['email'];
      if (value is String && value.isNotEmpty) return value;
    }
    return null;
  }

  static bool _flag(dynamic value) => value == true || value == 1;
}
