import 'package:flutter/material.dart';

import '../data/app_state.dart';
import '../models/enums.dart';
import '../models/models.dart';
import '../theme/app_colors.dart';
import '../utils/formatters.dart';

/// Compact prep-period strip. Tap opens details so lists stay short to scroll.
class PreparationPeriodCard extends StatelessWidget {
  const PreparationPeriodCard({super.key, this.compact = false});

  final bool compact;

  static const disclaimer =
      'FacultyLink is preparatory self-assessment only under DBM–CHED JC No. 01, s. 2026. Scores and reviewer feedback here are not the official evaluation or final rank decision.';

  @override
  Widget build(BuildContext context) {
    final period = AppState.instance.preparationPeriod;
    final palette = _statusPalette(period.status);
    final start = formatDisplayDate(period.startDate);
    final end = formatDisplayDate(period.endDate);
    final until = formatDisplayDate(period.reviewerAvailableUntil);
    final available = period.status != PreparationPeriodStatus.closed;

    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: () => _showDetails(context, period, palette),
        borderRadius: BorderRadius.circular(18),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.divider),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Colors.white,
                palette.soft.withValues(alpha: 0.45),
              ],
            ),
          ),
          child: Padding(
            padding: EdgeInsets.fromLTRB(
              compact ? 12 : 14,
              compact ? 11 : 13,
              compact ? 12 : 14,
              compact ? 11 : 13,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        color: AppColors.navy.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.event_available_outlined,
                        color: AppColors.navy,
                        size: 18,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Preparation period',
                            style: TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 14,
                              color: AppColors.textPrimary,
                              height: 1.15,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            period.cycleName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    _StatusChip(status: period.status, palette: palette),
                    const SizedBox(width: 2),
                    const Icon(
                      Icons.chevron_right_rounded,
                      color: AppColors.textTertiary,
                      size: 22,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                _TimelineRail(
                  start: start,
                  end: end,
                  accent: palette.color,
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Icon(
                      available ? Icons.groups_outlined : Icons.lock_outline_rounded,
                      size: 15,
                      color: available ? AppColors.info : AppColors.textTertiary,
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        available
                            ? 'Reviewers available until $until'
                            : 'Reviewer window ended $until',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: available ? AppColors.navy : AppColors.textSecondary,
                        ),
                      ),
                    ),
                    Text(
                      'Details',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppColors.navy.withValues(alpha: 0.75),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  static Future<void> _showDetails(
    BuildContext context,
    PreparationPeriod period,
    _StatusPalette palette,
  ) {
    return showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  period.cycleName,
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 17,
                    color: AppColors.navy,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${formatDisplayDate(period.startDate)} – ${formatDisplayDate(period.endDate)}',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 14),
                _DetailBlock(
                  icon: palette.icon,
                  color: palette.color,
                  soft: palette.soft,
                  text: period.status.guidance,
                ),
                const SizedBox(height: 8),
                const _DetailBlock(
                  icon: Icons.info_outline_rounded,
                  color: AppColors.warning,
                  soft: Color(0xFFFFF7E8),
                  text: PreparationPeriodCard.disclaimer,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  static _StatusPalette _statusPalette(PreparationPeriodStatus status) {
    switch (status) {
      case PreparationPeriodStatus.open:
        return const _StatusPalette(
          color: AppColors.success,
          soft: AppColors.successSoft,
          icon: Icons.check_circle_outline_rounded,
        );
      case PreparationPeriodStatus.closingSoon:
        return const _StatusPalette(
          color: AppColors.warning,
          soft: AppColors.warningSoft,
          icon: Icons.schedule_rounded,
        );
      case PreparationPeriodStatus.closed:
        return const _StatusPalette(
          color: AppColors.error,
          soft: AppColors.errorSoft,
          icon: Icons.lock_outline_rounded,
        );
    }
  }
}

class _TimelineRail extends StatelessWidget {
  const _TimelineRail({
    required this.start,
    required this.end,
    required this.accent,
  });

  final String start;
  final String end;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _DateEnd(label: 'Start', value: start, alignEnd: false),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  height: 3,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(99),
                    gradient: LinearGradient(
                      colors: [
                        accent.withValues(alpha: 0.25),
                        accent,
                        accent.withValues(alpha: 0.25),
                      ],
                    ),
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _Dot(color: accent),
                    _Dot(color: accent),
                  ],
                ),
              ],
            ),
          ),
        ),
        _DateEnd(label: 'End', value: end, alignEnd: true),
      ],
    );
  }
}

class _Dot extends StatelessWidget {
  const _Dot({required this.color});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 9,
      height: 9,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.35),
            blurRadius: 4,
          ),
        ],
      ),
    );
  }
}

class _DateEnd extends StatelessWidget {
  const _DateEnd({
    required this.label,
    required this.value,
    required this.alignEnd,
  });

  final String label;
  final String value;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: AppColors.textTertiary,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w800,
            color: AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}

class _DetailBlock extends StatelessWidget {
  const _DetailBlock({
    required this.icon,
    required this.color,
    required this.soft,
    required this.text,
  });

  final IconData icon;
  final Color color;
  final Color soft;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(10, 9, 10, 9),
      decoration: BoxDecoration(
        color: soft,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 12,
                height: 1.35,
                fontWeight: FontWeight.w600,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPalette {
  const _StatusPalette({
    required this.color,
    required this.soft,
    required this.icon,
  });

  final Color color;
  final Color soft;
  final IconData icon;
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status, required this.palette});

  final PreparationPeriodStatus status;
  final _StatusPalette palette;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: palette.soft,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: palette.color.withValues(alpha: 0.35)),
      ),
      child: Text(
        status.label,
        style: TextStyle(
          color: palette.color,
          fontWeight: FontWeight.w800,
          fontSize: 11,
        ),
      ),
    );
  }
}
