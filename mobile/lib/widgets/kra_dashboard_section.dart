import 'package:flutter/material.dart';

import '../models/models.dart';
import '../navigation/app_routes.dart';
import '../theme/app_colors.dart';
import 'kra_module_card.dart';

/// Dashboard "Key Result Areas" — responsive academic module grid.
class KraDashboardSection extends StatelessWidget {
  const KraDashboardSection({super.key, required this.kraScores});

  final List<KraScore> kraScores;

  static bool useTwoColumns(double maxWidth, TextScaler textScaler) {
    final scale = textScaler.scale(14) / 14;
    if (scale > 1.12) return false;
    const minColumnWidth = 184.0;
    const spacing = 10.0;
    return maxWidth >= (minColumnWidth * 2 + spacing);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Key Result Areas',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w800,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Track your academic contributions across four areas.',
          style: TextStyle(
            fontSize: 12,
            height: 1.4,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            const spacing = 10.0;
            final twoCol = useTwoColumns(
              constraints.maxWidth,
              MediaQuery.textScalerOf(context),
            );
            final itemWidth = twoCol
                ? (constraints.maxWidth - spacing) / 2
                : constraints.maxWidth;

            return Wrap(
              spacing: spacing,
              runSpacing: spacing,
              children: [
                for (final score in kraScores)
                  SizedBox(
                    width: itemWidth,
                    child: KraModuleCard(
                      score: score,
                      onTap: () {
                        Navigator.pushNamed(
                          context,
                          AppRoutes.kraDetails,
                          arguments: score.type,
                        );
                      },
                    ),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }
}
