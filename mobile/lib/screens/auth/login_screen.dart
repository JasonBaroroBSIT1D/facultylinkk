import 'package:flutter/material.dart';

import '../../data/app_auth_exception.dart';
import '../../data/app_state.dart';
import '../../navigation/app_routes.dart';
import '../../widgets/auth_ui.dart';
import '../../widgets/dialogs.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, this.initialEmail});

  /// Pre-filled after a successful password reset.
  final String? initialEmail;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _email =
      TextEditingController(text: widget.initialEmail ?? '');
  final _password = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  bool _signInInProgress = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _tryRestore());
  }

  void _openPasswordChangeRequired() {
    Navigator.pushNamedAndRemoveUntil(
      context,
      AppRoutes.changeTemporaryPassword,
      (_) => false,
    );
  }

  void _openMainApp() {
    Navigator.pushNamedAndRemoveUntil(context, AppRoutes.main, (_) => false);
  }

  Future<void> _tryRestore() async {
    if (!AppState.instance.sessionRestoreEnabled || _signInInProgress) return;
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final restored = await AppState.instance.tryRestoreSession();
      if (!mounted || !restored) return;
      if (AppState.instance.mustChangePassword) {
        _openPasswordChangeRequired();
        return;
      }
      _openMainApp();
    } on AppAuthException catch (error) {
      if (!mounted) return;
      if (error.isPasswordChangeRequired && AppState.instance.isSignedIn) {
        AppState.instance.mustChangePassword = true;
        _openPasswordChangeRequired();
        return;
      }
      if (!error.isPasswordChangeRequired) {
        showAppSnackBar(context, error.message, error: true);
      }
    } catch (_) {
      /* stale token or offline — stay on login */
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate() || _loading) return;
    _signInInProgress = true;
    setState(() => _loading = true);
    try {
      await AppState.instance.login(_email.text, _password.text);
      if (!mounted) return;
      if (AppState.instance.mustChangePassword) {
        _openPasswordChangeRequired();
        return;
      }
      _openMainApp();
    } on AppAuthException catch (error) {
      if (!mounted) return;
      if (error.isPasswordChangeRequired && AppState.instance.isSignedIn) {
        AppState.instance.mustChangePassword = true;
        _openPasswordChangeRequired();
        return;
      }
      showAppSnackBar(context, error.message, error: true);
    } catch (_) {
      if (!mounted) return;
      showAppSnackBar(context, 'Sign-in failed. Please try again.', error: true);
    } finally {
      _signInInProgress = false;
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthBackdrop(
      child: AuthCard(
        badgeIcon: Icons.lock_open_rounded,
        children: [
          const AuthHeading(
            eyebrow: 'FACULTYLINK',
            title: 'Login here',
            subtitle: 'Welcome back! Sign in with your faculty\nemail to continue.',
          ),
          Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AuthField(
                  hint: 'Email',
                  controller: _email,
                  prefixIcon: Icons.mail_outline_rounded,
                  keyboardType: TextInputType.emailAddress,
                  textInputAction: TextInputAction.next,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Enter your faculty email';
                    }
                    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim())) {
                      return 'Enter a valid email address';
                    }
                    return null;
                  },
                ),
                AuthField(
                  hint: 'Password',
                  controller: _password,
                  prefixIcon: Icons.lock_outline_rounded,
                  obscureText: _obscure,
                  textInputAction: TextInputAction.done,
                  onSubmitted: (_) => _loading ? null : _login(),
                  suffix: IconButton(
                    tooltip: _obscure ? 'Show password' : 'Hide password',
                    onPressed: () => setState(() => _obscure = !_obscure),
                    icon: Icon(
                      _obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                      color: AuthPalette.iconIdle,
                    ),
                  ),
                  validator: (value) =>
                      value == null || value.isEmpty ? 'Enter your password' : null,
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AuthButton(label: 'Sign in', loading: _loading, onPressed: _login),
          const SizedBox(height: 10),
          AuthLink(
            label: 'Forgot your password?',
            onPressed: () => Navigator.pushNamed(context, AppRoutes.forgotPassword),
          ),
        ],
      ),
    );
  }
}
