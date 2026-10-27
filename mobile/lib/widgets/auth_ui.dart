import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Colors for the blue "card on gradient" auth screens.
abstract final class AuthPalette {
  static const Color bgTop = Color(0xFF2F7BFF);
  static const Color bgMid = Color(0xFF1D6BFF);
  static const Color bgBottom = Color(0xFF0B5BFF);

  /// Must match `facultylink_launch_blue` in the Android native launch screen.
  static const Color nativeBlue = Color(0xFF1D6BFF);

  static const Color primary = Color(0xFF1F41BB);
  static const Color primaryDark = Color(0xFF14308F);
  static const Color primaryLight = Color(0xFF3B63E8);
  static const Color field = Color(0xFFF1F4FF);
  static const Color fieldFocused = Color(0xFFE8EEFF);
  static const Color iconIdle = Color(0xFF7C7F93);
  static const Color ink = Color(0xFF1B1F3B);
  static const Color muted = Color(0xFF5B6078);
  static const Color accent = Color(0xFF7B3FF2);
  static const Color error = Color(0xFFD92D20);
}

bool _reduceMotion(BuildContext context) => MediaQuery.disableAnimationsOf(context);

/// Blue gradient background with soft depth and gentle decorative shapes.
///
/// [reveal] fades the gradient and shapes in over the plain launch blue (splash).
/// [drift] adds a very subtle movement to the shapes.
class AuthBackdrop extends StatelessWidget {
  const AuthBackdrop({
    super.key,
    required this.child,
    this.onBack,
    this.reveal,
    this.drift,
  });

  final Widget child;
  final VoidCallback? onBack;
  final Animation<double>? reveal;
  final Animation<double>? drift;

  @override
  Widget build(BuildContext context) {
    Widget decor = _BackdropDecor(drift: drift);
    if (reveal != null) decor = FadeTransition(opacity: reveal!, child: decor);

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        backgroundColor: AuthPalette.nativeBlue,
        body: Stack(
          fit: StackFit.expand,
          children: [
            decor,
            SafeArea(child: child),
            if (onBack != null)
              SafeArea(
                child: Align(
                  alignment: Alignment.topLeft,
                  child: Padding(
                    padding: const EdgeInsets.only(left: 6, top: 2),
                    child: IconButton(
                      tooltip: 'Back',
                      onPressed: onBack,
                      icon: const Icon(
                        Icons.arrow_back_ios_new_rounded,
                        color: Colors.white,
                        size: 20,
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _BackdropDecor extends StatelessWidget {
  const _BackdropDecor({this.drift});

  final Animation<double>? drift;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Stack(
        fit: StackFit.expand,
        children: [
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [AuthPalette.bgTop, AuthPalette.bgMid, AuthPalette.bgBottom],
              ),
            ),
          ),
          // Soft light from the top-left and a deeper tone at the bottom-right.
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: const Alignment(-0.55, -0.9),
                radius: 1.15,
                colors: [Colors.white.withValues(alpha: 0.20), Colors.white.withValues(alpha: 0)],
              ),
            ),
          ),
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: const Alignment(0.95, 1.1),
                radius: 1.0,
                colors: [
                  const Color(0xFF0A2FA8).withValues(alpha: 0.38),
                  const Color(0xFF0A2FA8).withValues(alpha: 0),
                ],
              ),
            ),
          ),
          _Drift(
            animation: drift,
            dx: 10,
            dy: 8,
            child: Align(
              alignment: const Alignment(1.35, -1.05),
              child: _Blob(size: 230, color: Colors.white.withValues(alpha: 0.10)),
            ),
          ),
          _Drift(
            animation: drift,
            dx: -9,
            dy: -8,
            child: Align(
              alignment: const Alignment(-1.45, 1.15),
              child: _Blob(size: 270, color: Colors.white.withValues(alpha: 0.08)),
            ),
          ),
          _Drift(
            animation: drift,
            dx: -7,
            dy: 9,
            child: Align(
              alignment: const Alignment(1.28, 0.62),
              child: _Blob(size: 112, color: const Color(0xFF3DD6A4)),
            ),
          ),
          _Drift(
            animation: drift,
            dx: 8,
            dy: -6,
            child: Align(
              alignment: const Alignment(-1.3, -0.42),
              child: _Blob(
                size: 92,
                color: AuthPalette.accent.withValues(alpha: 0.28),
              ),
            ),
          ),
          Align(
            alignment: const Alignment(-0.8, -0.8),
            child: _Blob(size: 12, color: Colors.white.withValues(alpha: 0.38)),
          ),
          Align(
            alignment: const Alignment(0.84, -0.46),
            child: _Blob(size: 8, color: Colors.white.withValues(alpha: 0.32)),
          ),
        ],
      ),
    );
  }
}

class _Drift extends StatelessWidget {
  const _Drift({
    required this.animation,
    required this.dx,
    required this.dy,
    required this.child,
  });

  final Animation<double>? animation;
  final double dx;
  final double dy;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final animation = this.animation;
    if (animation == null) return child;
    return AnimatedBuilder(
      animation: animation,
      child: child,
      builder: (context, child) {
        final t = Curves.easeInOut.transform(animation.value) * 2 - 1;
        return Transform.translate(offset: Offset(dx * t, dy * t), child: child);
      },
    );
  }
}

class _Blob extends StatelessWidget {
  const _Blob({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}

/// White floating card that holds an auth form, with a glowing badge on its top edge.
///
/// The card slides up and the badge scales in using the route's own transition
/// animation, so it never fights with the page transition. Nothing animates when
/// reduced motion is requested.
class AuthCard extends StatelessWidget {
  const AuthCard({
    super.key,
    required this.children,
    this.badgeIcon = Icons.lock_rounded,
    this.maxWidth = 420,
  });

  final List<Widget> children;
  final IconData badgeIcon;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    final routeAnimation = ModalRoute.of(context)?.animation;
    final Animation<double> entrance =
        (_reduceMotion(context) || routeAnimation == null)
            ? const AlwaysStoppedAnimation<double>(1)
            : routeAnimation;

    final slide = entrance.drive(
      Tween<Offset>(begin: const Offset(0, 0.035), end: Offset.zero)
          .chain(CurveTween(curve: const Interval(0.0, 0.9, curve: Curves.easeOutCubic))),
    );
    final badgeScale = entrance.drive(
      Tween<double>(begin: 0.7, end: 1)
          .chain(CurveTween(curve: const Interval(0.25, 1.0, curve: Curves.easeOutCubic))),
    );
    final badgeFade = entrance.drive(
      CurveTween(curve: const Interval(0.2, 0.9, curve: Curves.easeOut)),
    );

    return Center(
      child: SingleChildScrollView(
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        padding: const EdgeInsets.fromLTRB(22, 60, 22, 28),
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: SlideTransition(
            position: slide,
            child: Stack(
              clipBehavior: Clip.none,
              alignment: Alignment.topCenter,
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.fromLTRB(26, 58, 26, 28),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(30),
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
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: children,
                  ),
                ),
                Positioned(
                  top: -40,
                  child: ScaleTransition(
                    scale: badgeScale,
                    child: FadeTransition(
                      opacity: badgeFade,
                      child: _GlowBadge(icon: badgeIcon),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _GlowBadge extends StatelessWidget {
  const _GlowBadge({required this.icon});

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 112,
      height: 80,
      child: Stack(
        alignment: Alignment.center,
        clipBehavior: Clip.none,
        children: [
          // Soft glow halo.
          Container(
            width: 112,
            height: 112,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: RadialGradient(
                colors: [
                  AuthPalette.accent.withValues(alpha: 0.34),
                  AuthPalette.accent.withValues(alpha: 0),
                ],
              ),
            ),
          ),
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFFA77BFF), AuthPalette.accent],
              ),
              border: Border.all(color: Colors.white, width: 4),
              boxShadow: [
                BoxShadow(
                  color: AuthPalette.accent.withValues(alpha: 0.45),
                  blurRadius: 22,
                  spreadRadius: 1,
                  offset: const Offset(0, 8),
                ),
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.10),
                  blurRadius: 8,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: Icon(icon, color: Colors.white, size: 34),
          ),
        ],
      ),
    );
  }
}

class AuthHeading extends StatelessWidget {
  const AuthHeading({super.key, required this.title, this.subtitle, this.eyebrow});

  final String title;
  final String? subtitle;

  /// Small branding label above the title, e.g. "FACULTYLINK".
  final String? eyebrow;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (eyebrow != null) ...[
          Text(
            eyebrow!,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 2.4,
              color: AuthPalette.accent.withValues(alpha: 0.85),
            ),
          ),
          const SizedBox(height: 8),
        ],
        Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 30,
            fontWeight: FontWeight.w800,
            letterSpacing: -0.4,
            color: AuthPalette.primary,
            height: 1.1,
          ),
        ),
        if (subtitle != null) ...[
          const SizedBox(height: 10),
          Text(
            subtitle!,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 14.5,
              height: 1.45,
              fontWeight: FontWeight.w500,
              color: AuthPalette.muted,
            ),
          ),
        ],
        const SizedBox(height: 24),
      ],
    );
  }
}

/// Filled, rounded input. It highlights smoothly on focus, and error messages
/// appear in reserved space so the layout never jumps.
class AuthField extends StatelessWidget {
  const AuthField({
    super.key,
    required this.hint,
    this.controller,
    this.obscureText = false,
    this.keyboardType,
    this.textInputAction,
    this.prefixIcon,
    this.suffix,
    this.validator,
    this.onSubmitted,
    this.inputFormatters,
    this.codeStyle = false,
    this.autofillHints,
  });

  final String hint;
  final TextEditingController? controller;
  final bool obscureText;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final IconData? prefixIcon;
  final Widget? suffix;
  final String? Function(String?)? validator;
  final ValueChanged<String>? onSubmitted;
  final List<TextInputFormatter>? inputFormatters;
  final Iterable<String>? autofillHints;

  /// Large, centered, letter-spaced text for one-time codes.
  final bool codeStyle;

  @override
  Widget build(BuildContext context) {
    OutlineInputBorder border(Color color, [double width = 1.6]) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: color, width: width),
        );

    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      textInputAction: textInputAction,
      validator: validator,
      onFieldSubmitted: onSubmitted,
      inputFormatters: inputFormatters,
      autofillHints: autofillHints,
      cursorColor: AuthPalette.primary,
      textAlign: codeStyle ? TextAlign.center : TextAlign.start,
      style: TextStyle(
        fontSize: codeStyle ? 24 : 15,
        fontWeight: codeStyle ? FontWeight.w700 : FontWeight.w500,
        letterSpacing: codeStyle ? 8 : 0,
        color: AuthPalette.ink,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(color: AuthPalette.iconIdle, fontWeight: FontWeight.w500),
        // A blank helper reserves one line, so an error replaces it without moving anything.
        helperText: ' ',
        helperStyle: const TextStyle(fontSize: 12, height: 0.9),
        errorStyle: const TextStyle(
          fontSize: 12,
          height: 0.9,
          fontWeight: FontWeight.w600,
          color: AuthPalette.error,
        ),
        filled: true,
        fillColor: WidgetStateColor.resolveWith(
          (states) => states.contains(WidgetState.focused)
              ? AuthPalette.fieldFocused
              : AuthPalette.field,
        ),
        prefixIcon: prefixIcon == null ? null : Icon(prefixIcon, size: 21),
        prefixIconColor: WidgetStateColor.resolveWith(
          (states) => states.contains(WidgetState.error)
              ? AuthPalette.error
              : states.contains(WidgetState.focused)
                  ? AuthPalette.primary
                  : AuthPalette.iconIdle,
        ),
        suffixIcon: suffix,
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
        border: border(Colors.transparent),
        enabledBorder: border(Colors.transparent),
        focusedBorder: border(AuthPalette.primary),
        errorBorder: border(AuthPalette.error.withValues(alpha: 0.7), 1.2),
        focusedErrorBorder: border(AuthPalette.error),
      ),
    );
  }
}

/// Gradient primary action button with a gentle press animation and a loading state.
class AuthButton extends StatefulWidget {
  const AuthButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.loading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;

  @override
  State<AuthButton> createState() => _AuthButtonState();
}

class _AuthButtonState extends State<AuthButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final reduce = _reduceMotion(context);
    final enabled = widget.onPressed != null && !widget.loading;
    final radius = BorderRadius.circular(14);

    return AnimatedScale(
      scale: (_pressed && enabled && !reduce) ? 0.97 : 1,
      duration: reduce ? Duration.zero : const Duration(milliseconds: 110),
      curve: Curves.easeOut,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: radius,
          boxShadow: [
            BoxShadow(
              color: AuthPalette.primary.withValues(alpha: _pressed ? 0.25 : 0.38),
              blurRadius: _pressed ? 10 : 18,
              offset: Offset(0, _pressed ? 4 : 9),
            ),
          ],
        ),
        child: Material(
          type: MaterialType.transparency,
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: radius,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [AuthPalette.primaryLight, AuthPalette.primary],
              ),
            ),
            child: InkWell(
              borderRadius: radius,
              splashColor: Colors.white.withValues(alpha: 0.18),
              highlightColor: Colors.white.withValues(alpha: 0.06),
              onTap: enabled ? widget.onPressed : null,
              onHighlightChanged: (value) => setState(() => _pressed = value),
              child: SizedBox(
                height: 56,
                child: Center(
                  child: AnimatedSwitcher(
                    duration: reduce ? Duration.zero : const Duration(milliseconds: 160),
                    child: widget.loading
                        ? const SizedBox(
                            key: ValueKey('loading'),
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.4,
                              color: Colors.white,
                            ),
                          )
                        : Text(
                            widget.label,
                            key: const ValueKey('label'),
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.3,
                              color: Colors.white,
                            ),
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

/// Small text link, e.g. "Forgot your password?".
class AuthLink extends StatelessWidget {
  const AuthLink({
    super.key,
    required this.label,
    required this.onPressed,
    this.color = AuthPalette.ink,
    this.alignment = Alignment.center,
    this.fontSize = 14,
  });

  final String label;
  final VoidCallback onPressed;
  final Color color;
  final Alignment alignment;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: alignment,
      child: TextButton(
        style: TextButton.styleFrom(
          foregroundColor: color,
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
          minimumSize: const Size(48, 40),
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
        ),
        onPressed: onPressed,
        child: Text(
          label,
          style: TextStyle(fontSize: fontSize, fontWeight: FontWeight.w700),
        ),
      ),
    );
  }
}

/// Simple vector illustration (person at a laptop) used on the splash card.
class AuthIllustration extends StatelessWidget {
  const AuthIllustration({super.key, this.height = 210});

  final double height;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      width: double.infinity,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            width: height * 0.92,
            height: height * 0.92,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: Color(0xFFEAF0FF),
            ),
          ),
          Positioned(
            right: 14,
            bottom: 14,
            child: Icon(Icons.eco_rounded, size: height * 0.32, color: const Color(0xFF3F51B5)),
          ),
          Positioned(
            left: 18,
            top: 26,
            child: Icon(Icons.star_rounded, size: 22, color: AuthPalette.accent.withValues(alpha: 0.6)),
          ),
          const Positioned(
            right: 34,
            top: 34,
            child: Icon(Icons.auto_awesome, size: 20, color: Color(0xFF3DD6A4)),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: height * 0.26,
                height: height * 0.26,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: Color(0xFFFFC9A6),
                ),
                child: Icon(Icons.face_rounded, size: height * 0.2, color: const Color(0xFF3B2A1E)),
              ),
              const SizedBox(height: 4),
              Container(
                width: height * 0.46,
                height: height * 0.3,
                decoration: const BoxDecoration(
                  color: AuthPalette.primary,
                  borderRadius: BorderRadius.vertical(
                    top: Radius.circular(26),
                    bottom: Radius.circular(8),
                  ),
                ),
                child: Icon(Icons.laptop_mac_rounded, size: height * 0.2, color: Colors.white),
              ),
              const SizedBox(height: 4),
              Container(
                width: height * 0.4,
                height: 8,
                decoration: BoxDecoration(
                  color: AuthPalette.primaryDark.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}