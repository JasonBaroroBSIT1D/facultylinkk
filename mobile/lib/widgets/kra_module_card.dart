import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';

/// Modern academic module tile for dashboard KRA overview.
class KraModuleCard extends StatefulWidget {
  const KraModuleCard({super.key, required this.score, this.onTap});

  final KraScore score;
  final VoidCallback? onTap;

  @override
  State<KraModuleCard> createState() => _KraModuleCardState();
}

class _KraModuleCardState extends State<KraModuleCard> {
  bool _pressed = false;

  KraScore get score => widget.score;

  @override
  Widget build(BuildContext context) {
    final accent = AppColors.kra(score.type);
    final soft = AppColors.kraSoft(score.type);
    final disableMotion = MediaQuery.disableAnimationsOf(context);
    final scale = !disableMotion && _pressed ? 0.985 : 1.0;
    final showPointsProgress = score.targetPoints > 0;

    final docLabel = score.documentCount == 1
        ? '1 supporting document'
        : '${score.documentCount} supporting documents';

    final targetLabel = score.targetPoints > 0
        ? 'of ${score.targetPoints} preview points'
        : 'Preview points';

    return AnimatedScale(
      scale: scale,
      duration: const Duration(milliseconds: 90),
      curve: Curves.easeOut,
      child: Material(
        color: AppColors.surface,
        elevation: 0,
        borderRadius: BorderRadius.circular(14),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: widget.onTap,
          onHighlightChanged: (value) {
            if (disableMotion) return;
            setState(() => _pressed = value);
          },
          child: Ink(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.divider),
            ),
            child: IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    width: 4,
                    decoration: BoxDecoration(
                      color: accent,
                      borderRadius: const BorderRadius.only(
                        topLeft: Radius.circular(13),
                        bottomLeft: Radius.circular(13),
                      ),
                    ),
                  ),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(12, 12, 10, 12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 38,
                                height: 38,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: soft,
                                  borderRadius: BorderRadius.circular(11),
                                ),
                                child: Icon(
                                  score.type.icon,
                                  size: 20,
                                  color: accent,
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      score.type.code.toUpperCase(),
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        letterSpacing: 0.6,
                                        color: accent.withValues(alpha: 0.85),
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      score.type.dashboardModuleTitle,
                                      maxLines: 3,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w700,
                                        height: 1.3,
                                        color: AppColors.textPrimary,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(
                                Icons.chevron_right_rounded,
                                color: AppColors.textSecondary,
                                size: 22,
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            '${score.currentPoints}',
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w800,
                              height: 1,
                              color: accent,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            targetLabel,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textSecondary,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            docLabel,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 11,
                              height: 1.35,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          if (showPointsProgress) ...[
                            const SizedBox(height: 8),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(999),
                              child: LinearProgressIndicator(
                                value: score.progress,
                                minHeight: 4,
                                backgroundColor: soft,
                                color: accent,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Points toward KRA target (preview)',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontSize: 9,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textTertiary.withValues(
                                  alpha: 0.95,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
