import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';
import 'progress_ring.dart';

class KraCard extends StatelessWidget {
  const KraCard({
    super.key,
    required this.score,
    this.compact = false,
    this.onTap,
  });

  final KraScore score;
  final bool compact;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.kra(score.type);
    final percent = (score.progress * 100).round();

    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.divider),
          ),
          padding: EdgeInsets.all(compact ? 12 : 16),
          child: compact ? _compact(color, percent) : _full(color, percent),
        ),
      ),
    );
  }

  Widget _compact(Color color, int percent) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: AppColors.kraSoft(score.type),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(score.type.icon, color: color, size: 20),
        ),
        const SizedBox(height: 10),
        Text(
          score.type.shortLabel,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            fontWeight: FontWeight.w700,
            fontSize: 13,
            color: AppColors.textPrimary,
            height: 1.2,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          '${score.currentPoints} pts',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 18,
            color: color,
          ),
        ),
        const SizedBox(height: 6),
        LinearProgressLabeled(progress: score.progress, color: color, height: 6),
        const SizedBox(height: 8),
        Text(
          '$percent% · ${score.documentCount} docs',
          style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
        ),
      ],
    );
  }

  Widget _full(Color color, int percent) {
    return Row(
      children: [
        Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: AppColors.kraSoft(score.type),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(score.type.icon, color: color, size: 26),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                score.type.label,
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${score.documentCount} supporting documents · ${score.statusLabel}',
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 10),
              LinearProgressLabeled(progress: score.progress, color: color),
            ],
          ),
        ),
        const SizedBox(width: 12),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${score.currentPoints}',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
            Text(
              '/ ${score.targetPoints} pts',
              style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
            ),
            const SizedBox(height: 4),
            Text(
              '$percent%',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(width: 4),
        const Icon(Icons.chevron_right_rounded, color: AppColors.textTertiary),
      ],
    );
  }
}
