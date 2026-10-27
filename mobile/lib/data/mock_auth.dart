import 'app_auth_exception.dart';

/// Simulated faculty auth for frontend-only builds (no server).
abstract final class MockAuth {
  static const demoEmail = 'maria.santos@university.edu.ph';
  static const demoPassword = 'password123';
  static const demoResetCode = '123456';

  static const registerMessage =
      'Faculty accounts are issued by your institution. This request was recorded locally (simulated).';

  static void validateSignIn(String email, String password, String activePassword) {
    final normalized = email.trim().toLowerCase();
    if (normalized != demoEmail) {
      throw AppAuthException('Invalid email or password.', statusCode: 401);
    }
    if (password != activePassword) {
      throw AppAuthException('Invalid email or password.', statusCode: 401);
    }
  }

  static Map<String, dynamic> requestPasswordReset(String email) {
    // Same response shape whether or not the address is known (privacy-preserving UX).
    return {
      'ok': true,
      'message':
          'Simulated: if that email belongs to a FacultyLink account, a 6-digit code would be sent. '
          'For this demo, use code $demoResetCode with $demoEmail.',
      'expiresInSeconds': 300,
      'resendAfterSeconds': 60,
    };
  }

  static String verifyResetCode(String email, String otp) {
    if (otp.trim() != demoResetCode) {
      throw AppAuthException(
        'The code is invalid or has expired. Request a new code.',
        statusCode: 400,
      );
    }
    return 'simulated-reset-token';
  }

  static String resetPassword({
    required String resetToken,
    required String newPassword,
  }) {
    if (resetToken.isEmpty) {
      throw AppAuthException('Reset session expired. Start again.', statusCode: 400);
    }
    if (newPassword.length < 8) {
      throw AppAuthException('Use at least 8 characters.', statusCode: 400);
    }
    return 'Your password has been updated (simulated). Sign in with your new password.';
  }
}
