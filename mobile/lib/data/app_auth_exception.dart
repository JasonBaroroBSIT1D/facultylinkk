/// Thrown when simulated sign-in or password recovery fails.
class AppAuthException implements Exception {
  AppAuthException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}
