import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';
import '../utils/formatters.dart';
import 'status_badge.dart';

class DocumentCard extends StatelessWidget {
  const DocumentCard({
    super.key,
    required this.document,
    this.onTap,
    this.onView,
    this.criterionLabel,
    this.showOcr = true,
  });

  final FacultyDocument document;
  final VoidCallback? onTap;
  final VoidCallback? onView;
  final String? criterionLabel;
  final bool showOcr;

  static ({String short, Color bg, Color fg}) _fileType(FacultyDocument doc) {
    final name = doc.fileName.toLowerCase();
    if (name.endsWith('.pdf')) {
      return (short: 'PDF', bg: AppColors.errorSoft, fg: AppColors.error);
    }
    if (RegExp(r'\.(png|jpe?g|gif|webp|bmp)$').hasMatch(name)) {
      return (short: 'IMG', bg: AppColors.successSoft, fg: AppColors.success);
    }
    return (short: 'FILE', bg: AppColors.infoSoft, fg: AppColors.info);
  }

  @override
  Widget build(BuildContext context) {
    final date = formatDisplayDate(document.submittedAt);
    final ft = _fileType(document);
    final scoringMeta = document.countsInSimulation
        ? 'Simulation: ${document.simulationScoreLabel}'
        : document.creditsPoints
            ? 'Credited: ${document.creditedLabel} pts'
            : null;

    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap ?? onView,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.divider),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: ft.bg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: ft.fg.withValues(alpha: 0.15)),
                ),
                child: Text(
                  ft.short,
                  style: TextStyle(
                    fontSize: 9,
                    fontWeight: FontWeight.w800,
                    color: ft.fg,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      document.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 13,
                        color: AppColors.textPrimary,
                        height: 1.3,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      document.fileName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      [
                        ?criterionLabel?.isNotEmpty == true ? criterionLabel : null,
                        date,
                        ?scoringMeta,
                      ].whereType<String>().join(' · '),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textTertiary,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        StatusBadge(status: document.status, compact: true),
                        if (showOcr && document.ocrStatus != null)
                          _OcrChip(label: document.ocrStatusLabel),
                      ],
                    ),
                  ],
                ),
              ),
              if (onView != null)
                TextButton(
                  onPressed: onView,
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  ),
                  child: const Text('View'),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OcrChip extends StatelessWidget {
  const _OcrChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.divider),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w700,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
