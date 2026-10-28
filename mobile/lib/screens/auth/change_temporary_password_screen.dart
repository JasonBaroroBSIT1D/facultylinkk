import 'package:flutter/material.dart';

import '../../data/app_auth_exception.dart';
import '../../data/app_state.dart';
import '../../data/auth_response.dart';
import '../../navigation/app_routes.dart';
import '../../widgets/auth_ui.dart';
import '../../widgets/dialogs.dart';

/// First-login flow after an administrator-issued temporary password.
class ChangeTemporaryPasswordScreen extends StatefulWidget {
  const ChangeTemporaryPasswordScreen({super.key});

  @override
  State<ChangeTemporaryPasswordScreen> createState() =>
      _ChangeTemporaryPasswordScreenState();
}

class _ChangeTemporaryPasswordScreenState extends State<ChangeTemporaryPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  bool _obscureCurrent = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  bool _saving = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_saving || !_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await AppState.instance.changePassword(
        currentPassword: _current.text,
        newPassword: _next.text,
      );
      if (!mounted) return;
      Navigator.pushNamedAndRemoveUntil(context, AppRoutes.main, (_) => false);
    } on AppAuthException catch (error) {
      if (!mounted) return;
      showAppSnackBar(context, error.message, error: true);
    } catch (_) {
      if (!mounted) return;
      showAppSnackBar(context, 'Your password was not updated. Try again.', error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      child: AuthBackdrop(
        child: AuthCard(
          badgeIcon: Icons.vpn_key_rounded,
          children: [
            const AuthHeading(
              eyebrow: 'FACULTYLINK',
              title: 'Set your password',
              subtitle:
                  'Your account uses a temporary password.\nChoose a new password to continue.',
            ),
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  AuthField(
                    hint: 'Temporary password',
                    controller: _current,
                    prefixIcon: Icons.lock_outline_rounded,
                    obscureText: _obscureCurrent,
                    textInputAction: TextInputAction.next,
                    suffix: IconButton(
                      tooltip: _obscureCurrent ? 'Show password' : 'Hide password',
                      onPressed: () => setState(() => _obscureCurrent = !_obscureCurrent),
                      icon: Icon(
                        _obscureCurrent
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: AuthPalette.iconIdle,
                      ),
                    ),
                    validator: (value) =>
                        value == null || value.isEmpty ? 'Enter your temporary password' : null,
                  ),
                  AuthField(
                    hint: 'New password',
                    controller: _next,
                    prefixIcon: Icons.lock_reset_rounded,
                    obscureText: _obscureNew,
                    textInputAction: TextInputAction.next,
                    suffix: IconButton(
                      tooltip: _obscureNew ? 'Show password' : 'Hide password',
                      onPressed: () => setState(() => _obscureNew = !_obscureNew),
                      icon: Icon(
                        _obscureNew
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: AuthPalette.iconIdle,
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.length < AuthResponse.minPasswordLength) {
                        return 'Use at least ${AuthResponse.minPasswordLength} characters';
                      }
                      return null;
                    },
                  ),
                  AuthField(
                    hint: 'Confirm new password',
                    controller: _confirm,
                    prefixIcon: Icons.check_circle_outline_rounded,
                    obscureText: _obscureConfirm,
                    textInputAction: TextInputAction.done,
                    onSubmitted: (_) => _saving ? null : _submit(),
                    suffix: IconButton(
                      tooltip: _obscureConfirm ? 'Show password' : 'Hide password',
                      onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                      icon: Icon(
                        _obscureConfirm
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                        color: AuthPalette.iconIdle,
                      ),
                    ),
                    validator: (value) {
                      if (value != _next.text) return 'Passwords do not match';
                      return null;
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Password must be at least ${AuthResponse.minPasswordLength} characters and '
              'different from your temporary password.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: AuthPalette.muted, height: 1.35),
            ),
            const SizedBox(height: 16),
            AuthButton(label: 'Continue to FacultyLink', loading: _saving, onPressed: _submit),
          ],
        ),
      ),
    );
  }
}
