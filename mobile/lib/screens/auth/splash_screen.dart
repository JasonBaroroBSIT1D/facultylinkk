import 'dart:async';

import 'package:flutter/material.dart';

import '../../navigation/app_routes.dart';
import '../../widgets/app_logo.dart';
import '../../widgets/auth_ui.dart';
import 'login_screen.dart';

/// Animated launch screen.
///
/// Timeline: entrance animations (~1.8s) -> short hold -> a 450ms fade/slide
/// into the login screen, finishing at roughly 3 seconds in total. The splash
/// replaces itself, so Back can never return to it.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  /// When the transition to the login screen starts.
  static const Duration navigateAfter = Duration(milliseconds: 2600);
  static const Duration transition = Duration(milliseconds: 450);
  static const Duration entrance = Duration(milliseconds: 1800);

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late final AnimationController _entrance =
      AnimationController(vsync: this, duration: SplashScreen.entrance);
  late final AnimationController _drift =
      AnimationController(vsync: this, duration: const Duration(seconds: 6));
  Timer? _timer;
  bool _started = false;

  @override
  void initState() {
    super.initState();
    _timer = Timer(SplashScreen.navigateAfter, _goToLogin);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_started) return;
    _started = true;
    if (MediaQuery.disableAnimationsOf(context)) {
      // Respect reduced-motion: show the finished layout immediately.
      _entrance.value = 1;
    } else {
      _entrance.forward();
      _drift.repeat(reverse: true);
    }
  }

  void _goToLogin() {
    if (!mounted) return;
    final reduce = MediaQuery.disableAnimationsOf(context);
    Navigator.of(context).pushReplacement(
      PageRouteBuilder<void>(
        settings: const RouteSettings(name: AppRoutes.login),
        transitionDuration: reduce ? const Duration(milliseconds: 150) : SplashScreen.transition,
        reverseTransitionDuration: const Duration(milliseconds: 300),
        pageBuilder: (context, animation, secondary) => const LoginScreen(),
        transitionsBuilder: (context, animation, secondary, child) {
          final curved = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
          if (reduce) return FadeTransition(opacity: curved, child: child);
          return FadeTransition(
            opacity: curved,
            child: SlideTransition(
              position: Tween<Offset>(begin: const Offset(0, 0.03), end: Offset.zero)
                  .animate(curved),
              child: child,
            ),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _entrance.dispose();
    _drift.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final background = _entrance.drive(
      CurveTween(curve: const Interval(0.0, 0.35, curve: Curves.easeOut)),
    );
    // While the login page fades in, the splash card fades away so the two
    // cards never ghost over each other. The blue background stays put.
    final exit = ModalRoute.of(context)?.secondaryAnimation;
    final cardExit = exit == null
        ? const AlwaysStoppedAnimation<double>(1)
        : ReverseAnimation(exit.drive(CurveTween(curve: const Interval(0.0, 0.6))));

    return PopScope(
      canPop: false,
      child: AuthBackdrop(
        reveal: background,
        drift: _drift,
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: FadeTransition(
                opacity: cardExit,
                child: _Reveal(
                  animation: _entrance,
                  begin: 0.10,
                  end: 0.55,
                  slide: 0.05,
                  child: Container(
                    padding: const EdgeInsets.fromLTRB(24, 30, 24, 34),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(32),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF0A2A8A).withValues(alpha: 0.30),
                          blurRadius: 44,
                          offset: const Offset(0, 22),
                        ),
                        BoxShadow(
                          color: const Color(0xFF0A2A8A).withValues(alpha: 0.12),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _Reveal(
                          animation: _entrance,
                          begin: 0.30,
                          end: 0.60,
                          scaleFrom: 0.9,
                          child: const AppLogo(size: 44, showWordmark: true, horizontal: true),
                        ),
                        const SizedBox(height: 18),
                        _Reveal(
                          animation: _entrance,
                          begin: 0.40,
                          end: 0.78,
                          scaleFrom: 0.85,
                          child: const AuthIllustration(height: 210),
                        ),
                        const SizedBox(height: 24),
                        _Reveal(
                          animation: _entrance,
                          begin: 0.60,
                          end: 0.86,
                          slide: 0.12,
                          child: const Text(
                            'Prepare Your\nRank Upgrade here',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 28,
                              height: 1.2,
                              fontWeight: FontWeight.w800,
                              color: AuthPalette.primary,
                            ),
                          ),
                        ),
                        const SizedBox(height: 14),
                        _Reveal(
                          animation: _entrance,
                          begin: 0.74,
                          end: 1.0,
                          slide: 0.08,
                          child: const Text(
                            'Organize your documents, review your KRA scores, and preview a simulated rank path before the official DBM–CHED evaluation.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 14,
                              height: 1.5,
                              fontWeight: FontWeight.w500,
                              color: AuthPalette.ink,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Fades in (and optionally rises / scales) during one slice of [animation].
class _Reveal extends StatelessWidget {
  const _Reveal({
    required this.animation,
    required this.begin,
    required this.end,
    required this.child,
    this.slide = 0,
    this.scaleFrom = 1,
  });

  final Animation<double> animation;
  final double begin;
  final double end;
  final double slide;
  final double scaleFrom;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final curved = animation.drive(
      CurveTween(curve: Interval(begin, end, curve: Curves.easeOutCubic)),
    );
    Widget result = child;
    if (scaleFrom != 1) {
      result = ScaleTransition(
        scale: curved.drive(Tween<double>(begin: scaleFrom, end: 1)),
        child: result,
      );
    }
    if (slide != 0) {
      result = SlideTransition(
        position: curved.drive(Tween<Offset>(begin: Offset(0, slide), end: Offset.zero)),
        child: result,
      );
    }
    return FadeTransition(opacity: curved, child: result);
  }
}
