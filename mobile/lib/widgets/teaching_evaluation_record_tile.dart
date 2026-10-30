import 'package:flutter/material.dart';

import '../data/teaching_effectiveness_mapper.dart';
import '../models/teaching_evaluation_record.dart';
import '../theme/app_colors.dart';

class TeachingEvaluationRecordTile extends StatelessWidget {
  const TeachingEvaluationRecordTile({
    super.key,
    required this.record,
    this.onTap,
    this.compact = false,
  });

  final TeachingEvaluationRecord record;
  final VoidCallback? onTap;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final status = TeachingEffectivenessMapper.displayStatusForRecord(record);
    final (color, bg) = _colorsForStatus(status);
    final rating = record.ratingRaw ?? '—';
    final scale = record.ratingScale != null ? ' / ${record.ratingScale}' : '';

    return Card(
      margin: EdgeInsets.only(bottom: compact ? 6 : 8),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  _TypeChip(label: record.evaluationType.isEmpty ? '—' : record.evaluationType),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${record.academicYear ?? '—'} · ${record.semester ?? '—'}',
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: AppColors.navy,
                      ),
                    ),
                  ),
                  _StatusChip(label: status, color: color, background: bg),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Rating: $rating$scale',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              if (!compact) ...[
                const SizedBox(height: 4),
                Text(
                  record.fileName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
                ),
                if (record.sourceSectionRef?.isNotEmpty == true)
                  Text(
                    'Section: ${record.sourceSectionRef}',
                    style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
                  ),
                if (record.extractionStatus?.isNotEmpty == true)
                  Text(
                    'OCR: ${record.extractionStatus}',
                    style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
                  ),
                if (record.reviewerRemarks?.trim().isNotEmpty == true) ...[
                  const SizedBox(height: 6),
                  Text(
                    'Reviewer: ${record.reviewerRemarks!.trim()}',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textPrimary,
                      height: 1.35,
                    ),
                  ),
                ],
              ],
            ],
          ),
        ),
      ),
    );
  }

  static (Color, Color) _colorsForStatus(String status) {
    switch (status) {
      case 'Verified':
        return (AppColors.success, AppColors.successSoft);
      case 'Rejected':
        return (AppColors.error, AppColors.errorSoft);
      case 'Needs Revision':
        return (AppColors.warning, AppColors.warningSoft);
      case 'Incomplete Extraction':
      case 'Duplicate Conflict':
        return (AppColors.error, AppColors.errorSoft);
      default:
        return (AppColors.navy, AppColors.infoSoft);
    }
  }
}

class _TypeChip extends StatelessWidget {
  const _TypeChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.goldSoft,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          color: AppColors.navy,
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.label,
    required this.color,
    required this.background,
  });

  final String label;
  final Color color;
  final Color background;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color),
      ),
    );
  }
}
