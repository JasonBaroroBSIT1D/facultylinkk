import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class AppLogo extends StatelessWidget {
  const AppLogo({
    super.key,
    this.size = 72,
    this.showWordmark = false,
    this.light = false,
    this.horizontal = false,
  });

  final double size;
  final bool showWordmark;
  final bool light;
  final bool horizontal;

  @override
  Widget build(BuildContext context) {
    final mark = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
            color: (light ? AppColors.gold : AppColors.navy).withValues(alpha: 0.28),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Image.asset(
        'assets/images/app_icon.png',
        width: size,
        height: size,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.high,
        errorBuilder: (_, _, _) => ColoredBox(
          color: light ? AppColors.gold : AppColors.navy,
          child: Icon(
            Icons.assignment_outlined,
            color: Colors.white,
            size: size * 0.46,
          ),
        ),
      ),
    );

    if (!showWordmark) return mark;

    final titleColor = light ? Colors.white : AppColors.navy;
    final taglineColor = light ? AppColors.mint : AppColors.forestMid;

    final wordmark = Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment:
          horizontal ? CrossAxisAlignment.start : CrossAxisAlignment.center,
      children: [
        Text(
          'FacultyLink',
          style: TextStyle(
            fontSize: horizontal ? 20 : size * 0.28,
            fontWeight: FontWeight.w800,
            color: titleColor,
            letterSpacing: 0.2,
            height: 1.1,
          ),
        ),
        SizedBox(height: horizontal ? 2 : 4),
        Text(
          'Self Assessment',
          style: TextStyle(
            fontSize: horizontal ? 12 : size * 0.16,
            fontWeight: FontWeight.w700,
            color: taglineColor,
            letterSpacing: 0.15,
            height: 1.1,
          ),
        ),
      ],
    );

    if (horizontal) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          mark,
          const SizedBox(width: 10),
          Flexible(child: wordmark),
        ],
      );
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        mark,
        SizedBox(height: size * 0.14),
        wordmark,
      ],
    );
  }
}
