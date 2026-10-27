import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/app_colors.dart';
import 'app_logo.dart';

class FacultyBrandCopy extends StatelessWidget {
  const FacultyBrandCopy({
    super.key,
    this.compact = false,
  });

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const AppLogo(size: 48, showWordmark: true, light: true, horizontal: true),
        const SizedBox(height: 18),
        Container(
          width: 42,
          height: 3,
          decoration: BoxDecoration(
            color: AppColors.gold,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          'Faculty Evaluation and Self-Assessment System',
          maxLines: compact ? 3 : 4,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: Colors.white,
            fontSize: compact ? 22 : 26,
            height: 1.2,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          compact
              ? 'Prepare your documents, review KRA scores, and preview a simulated rank path before official evaluation.'
              : 'Prepare your documents, review your KRA scores, and see a simulated rank path — before the official DBM–CHED evaluation.',
          maxLines: compact ? 4 : 5,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: const Color(0xF2FFFFFF),
            fontSize: compact ? 14 : 15,
            height: 1.5,
            fontWeight: FontWeight.w400,
          ),
        ),
      ],
    );
  }
}

class AcademicNavyBackdrop extends StatelessWidget {
  const AcademicNavyBackdrop({super.key, this.child});

  final Widget? child;

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const ColoredBox(color: AppColors.navy),
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [AppColors.navyDark, AppColors.navy, Color(0xFF0A3D68)],
            ),
          ),
        ),
        const CustomPaint(painter: _AcademicPatternPainter()),
        ?child,
      ],
    );
  }
}

class AcademicAuthScaffold extends StatelessWidget {
  const AcademicAuthScaffold({
    super.key,
    required this.form,
    this.onBack,
  });

  final Widget form;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: Scaffold(
        body: AcademicNavyBackdrop(
          child: Column(
            children: [
              Expanded(
                flex: 5,
                child: SafeArea(
                  bottom: false,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(8, 0, 24, 8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (onBack != null)
                          IconButton(
                            onPressed: onBack,
                            icon: const Icon(
                              Icons.arrow_back_ios_new_rounded,
                              color: Colors.white,
                              size: 18,
                            ),
                          ),
                        Expanded(
                          child: SingleChildScrollView(
                            padding: const EdgeInsets.fromLTRB(16, 4, 4, 12),
                            child: FacultyBrandCopy(compact: true),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Expanded(
                flex: 6,
                child: ClipPath(
                  clipper: const _TopWaveClipper(),
                  child: ColoredBox(
                    color: Colors.white,
                    child: form,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TopWaveClipper extends CustomClipper<Path> {
  const _TopWaveClipper();

  @override
  Path getClip(Size size) {
    final path = Path()
      ..moveTo(0, 28)
      ..quadraticBezierTo(size.width * 0.5, 0, size.width, 28)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    return path;
  }

  @override
  bool shouldReclip(covariant CustomClipper<Path> oldClipper) => false;
}

class _AcademicPatternPainter extends CustomPainter {
  const _AcademicPatternPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final line = Paint()
      ..color = Colors.white.withValues(alpha: 0.05)
      ..strokeWidth = 1;
    for (var x = 24.0; x < size.width; x += 28) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), line);
    }
    final gold = Paint()..color = AppColors.gold.withValues(alpha: 0.12);
    canvas.drawCircle(Offset(size.width - 28, 64), 90, gold);
    canvas.drawCircle(Offset(-20, size.height * 0.7), 110, gold);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class AuthOrDivider extends StatelessWidget {
  const AuthOrDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: [
        Expanded(child: Divider()),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 12),
          child: Text(
            'or',
            style: TextStyle(color: AppColors.textTertiary, fontWeight: FontWeight.w600),
          ),
        ),
        Expanded(child: Divider()),
      ],
    );
  }
}
