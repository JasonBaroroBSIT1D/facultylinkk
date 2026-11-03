import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

/// Large tap target that behaves reliably on Flutter Web and mobile.
///
/// Uses [Material.shape] for borders (not a decorated [Container] inside
/// [InkWell]) and defers [onTap] to the next frame so navigation does not
/// re-enter [MouseTracker] during pointer dispatch.
class TappableCard extends StatelessWidget {
  const TappableCard({
    super.key,
    required this.onTap,
    required this.child,
    this.color = Colors.white,
    this.borderRadius = const BorderRadius.all(Radius.circular(16)),
    this.selected = false,
    this.padding,
    this.deferTap = true,
  });

  final VoidCallback onTap;
  final Widget child;
  final Color color;
  final BorderRadius borderRadius;
  final bool selected;
  final EdgeInsetsGeometry? padding;

  /// Defer only for [Navigator] calls. In-form [setState] should use `false`.
  final bool deferTap;

  static void scheduleTap(BuildContext context, VoidCallback action) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (context.mounted) action();
    });
  }

  @override
  Widget build(BuildContext context) {
    final side = BorderSide(
      color: selected ? AppColors.forestLight : AppColors.divider,
      width: selected ? 2 : 1,
    );
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: selected ? AppColors.mint.withValues(alpha: 0.4) : color,
        shape: RoundedRectangleBorder(borderRadius: borderRadius, side: side),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: deferTap ? () => scheduleTap(context, onTap) : onTap,
          child: padding != null ? Padding(padding: padding!, child: child) : child,
        ),
      ),
    );
  }
}
