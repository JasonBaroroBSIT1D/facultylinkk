import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../data/app_state.dart';
import '../../navigation/app_routes.dart';
import '../../data/app_auth_exception.dart';
import '../../widgets/auth_ui.dart';
import '../../widgets/dialogs.dart';

enum _RecoveryStep { email, code, newPassword }

/// Email OTP password recovery: email -> 6-digit code -> new password -> login.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key, this.initialEmail});

  final String? initialEmail;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _emailKey = GlobalKey<FormState>();
  final _codeKey = GlobalKey<FormState>();
  final _passwordKey = GlobalKey<FormState>();
  late final TextEditingController _email =
      TextEditingController(text: widget.initialEmail ?? '');
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();

  _RecoveryStep _step = _RecoveryStep.email;
  bool _loading = false;
  bool _obscure = true;
  bool _obscureConfirm = true;
  String _requestedEmail = '';
  String? _resetToken;

  Timer? _ticker;
  int _resendRemaining = 0;
  int _expiresRemaining = 0;

  @override
  void dispose() {
    _ticker?.cancel();
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  void _startTimers(int resendSeconds, int expiresSeconds) {
    _resendRemaining = resendSeconds;
    _expiresRemaining = expiresSeconds;
    _ticker?.cancel();
    _ticker = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      setState(() {
        if (_resendRemaining > 0) _resendRemaining--;
        if (_expiresRemaining > 0) _expiresRemaining--;
      });
      if (_resendRemaining == 0 && _expiresRemaining == 0) timer.cancel();
    });
  }

  void _toEmailStep() {
    _ticker?.cancel();
    setState(() {
      _step = _RecoveryStep.email;
      _resetToken = null;
      _resendRemaining = 0;
      _expiresRemaining = 0;
      _code.clear();
      _password.clear();
      _confirm.clear();
    });
  }

  void _back() {
    if (_loading) return;
    if (_step == _RecoveryStep.email) {
      Navigator.pop(context);
    } else {
      _toEmailStep();
    }
  }

  String _message(Object error) =>
      error is AppAuthException ? error.message : 'Something went wrong. Please try again.';

  Future<void> _sendCode({bool resend = false}) async {
    if (!resend && !_emailKey.currentState!.validate()) return;
    final email = resend ? _requestedEmail : _email.text.trim();
    setState(() => _loading = true);
    try {
      final data = await AppState.instance.requestPasswordResetCode(email);
      if (!mounted) return;
      _requestedEmail = email;
      _code.clear();
      _startTimers(
        (data['resendAfterSeconds'] as num?)?.toInt() ?? 60,
        (data['expiresInSeconds'] as num?)?.toInt() ?? 300,
      );
      setState(() => _step = _RecoveryStep.code);
      showAppSnackBar(
        context,
        (data['message'] as String?) ?? 'A 6-digit code has been sent.',
      );
    } catch (error) {
      if (!mounted) return;
      showAppSnackBar(context, _message(error), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _verifyCode() async {
    if (!_codeKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final token = await AppState.instance.verifyPasswordResetCode(
        _requestedEmail,
        _code.text.trim(),
      );
      if (!mounted) return;
      _ticker?.cancel();
      setState(() {
        _resetToken = token;
        _step = _RecoveryStep.newPassword;
      });
    } catch (error) {
      if (!mounted) return;
      _code.clear();
      showAppSnackBar(context, _message(error), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _resetPassword() async {
    if (!_passwordKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final message = await AppState.instance.resetPassword(
        email: _requestedEmail,
        resetToken: _resetToken ?? '',
        newPassword: _password.text,
      );
      if (!mounted) return;
      setState(() => _loading = false);
      await showSuccessDialog(
        context: context,
        title: 'Password updated',
        message: message,
        actionLabel: 'Go to sign in',
      );
      if (!mounted) return;
      Navigator.pushNamedAndRemoveUntil(
        context,
        AppRoutes.login,
        (_) => false,
        arguments: _requestedEmail,
      );
    } catch (error) {
      if (!mounted) return;
      showAppSnackBar(context, _message(error), error: true);
      if (error is AppAuthException && error.statusCode == 400 && _password.text.length >= 8) {
        // The reset session itself is no longer valid: start over.
        _toEmailStep();
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _eye(bool obscured, VoidCallback toggle) => IconButton(
        tooltip: obscured ? 'Show password' : 'Hide password',
        onPressed: toggle,
        icon: Icon(
          obscured ? Icons.visibility_outlined : Icons.visibility_off_outlined,
          color: AuthPalette.iconIdle,
        ),
      );

  String _clock(int seconds) {
    final minutes = (seconds ~/ 60).toString().padLeft(2, '0');
    final rest = (seconds % 60).toString().padLeft(2, '0');
    return '$minutes:$rest';
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: _step == _RecoveryStep.email && !_loading,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _back();
      },
      child: AuthBackdrop(
        onBack: _back,
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 220),
          child: KeyedSubtree(
            key: ValueKey(_step),
            child: switch (_step) {
              _RecoveryStep.email => _emailStep(),
              _RecoveryStep.code => _codeStep(),
              _RecoveryStep.newPassword => _passwordStep(),
            },
          ),
        ),
      ),
    );
  }

  Widget _emailStep() {
    return AuthCard(
      badgeIcon: Icons.mark_email_unread_rounded,
      children: [
        const AuthHeading(
          title: 'Forgot password',
          subtitle: 'Enter your registered email and we will\nsend you a 6-digit code.',
        ),
        Form(
          key: _emailKey,
          child: AuthField(
            hint: 'Email',
            controller: _email,
            prefixIcon: Icons.mail_outline_rounded,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _loading ? null : _sendCode(),
            validator: (value) {
              if (value == null || value.trim().isEmpty) return 'Enter your email';
              if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim())) {
                return 'Enter a valid email address';
              }
              return null;
            },
          ),
        ),
        const SizedBox(height: 24),
        AuthButton(label: 'Send code', loading: _loading, onPressed: _sendCode),
        const SizedBox(height: 10),
        AuthLink(label: 'Back to sign in', onPressed: _back),
      ],
    );
  }

  Widget _codeStep() {
    final resendIn = _resendRemaining;
    final expiresIn = _expiresRemaining;
    return AuthCard(
      badgeIcon: Icons.password_rounded,
      children: [
        AuthHeading(
          title: 'Enter code',
          subtitle: 'If $_requestedEmail is registered,\na 6-digit code was sent to it.',
        ),
        Form(
          key: _codeKey,
          child: AuthField(
            hint: '------',
            controller: _code,
            codeStyle: true,
            keyboardType: TextInputType.number,
            textInputAction: TextInputAction.done,
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(6),
            ],
            onSubmitted: (_) => _loading ? null : _verifyCode(),
            validator: (value) {
              if (value == null || value.length != 6) return 'Enter the 6-digit code';
              return null;
            },
          ),
        ),
        const SizedBox(height: 10),
        Text(
          expiresIn > 0
              ? 'Code expires in ${_clock(expiresIn)}'
              : 'This code has expired. Request a new one.',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: expiresIn > 0 ? AuthPalette.muted : const Color(0xFFD92D20),
          ),
        ),
        const SizedBox(height: 18),
        AuthButton(label: 'Verify', loading: _loading, onPressed: _verifyCode),
        const SizedBox(height: 10),
        AuthLink(
          label: resendIn > 0 ? 'Resend code in ${resendIn}s' : 'Resend code',
          color: resendIn > 0 ? AuthPalette.muted : AuthPalette.primary,
          onPressed: () {
            if (resendIn > 0 || _loading) return;
            _sendCode(resend: true);
          },
        ),
        AuthLink(label: 'Use a different email', onPressed: _back, fontSize: 13),
      ],
    );
  }

  Widget _passwordStep() {
    return AuthCard(
      badgeIcon: Icons.lock_reset_rounded,
      children: [
        const AuthHeading(
          title: 'New password',
          subtitle: 'Code verified. Choose a new password\nfor your account.',
        ),
        Form(
          key: _passwordKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AuthField(
                hint: 'New password',
                controller: _password,
                prefixIcon: Icons.lock_outline_rounded,
                obscureText: _obscure,
                textInputAction: TextInputAction.next,
                suffix: _eye(_obscure, () => setState(() => _obscure = !_obscure)),
                validator: (value) {
                  if (value == null || value.length < 8) {
                    return 'Use at least 8 characters';
                  }
                  if (value.length > 128) return 'Use at most 128 characters';
                  return null;
                },
              ),
              const SizedBox(height: 2),
              AuthField(
                hint: 'Confirm new password',
                controller: _confirm,
                prefixIcon: Icons.lock_reset_rounded,
                obscureText: _obscureConfirm,
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _loading ? null : _resetPassword(),
                suffix: _eye(
                  _obscureConfirm,
                  () => setState(() => _obscureConfirm = !_obscureConfirm),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) return 'Confirm your password';
                  if (value != _password.text) return 'Passwords do not match';
                  return null;
                },
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        AuthButton(label: 'Update password', loading: _loading, onPressed: _resetPassword),
      ],
    );
  }
}
