import 'auth_response.dart';

/// Thrown when sign-in, password change, or password recovery fails.
class AppAuthException implements Exception {
  AppAuthException(this.message, {this.statusCode, this.code});

  final String message;
  final int? statusCode;
  final String? code;

  bool get isPasswordChangeRequired =>
      code == AuthResponse.passwordChangeRequiredCode;

  @override
  String toString() => message;
}
