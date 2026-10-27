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
  });

  final FacultyDocument document;
  final VoidCallback? onTap;
  final VoidCallback? onView;
  final String? criterionLabel;

  @override
  Widget build(BuildContext context) {
    final date = formatDisplayDate(document.submittedAt);
    final meta = [
      if (criterionLabel != null && criterionLabel!.isNotEmpty) criterionLabel!,
      date,
      if (document.countsInSimulation)
        'Simulation: ${document.simulationScoreLabel} (${document.simulationSourceLabel})'
      else if (document.creditsPoints)
        document.indicatorId == 'kra1-a-student' ||
                document.indicatorId == 'kra1-a-supervisor'
            ? 'System approved · ${document.simulationScoreLabel}'
            : 'Credited: ${document.creditedLabel} pts'
      else if (document.indicatorId == 'kra1-a-student' ||
          document.indicatorId == 'kra1-a-supervisor')
        document.simulationScoreLabel
      else
        'Simulation: Score unavailable',
    ].join(' · ');

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap ?? onView,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      document.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: AppColors.textPrimary,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      document.fileName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    if (meta.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        meta,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textTertiary,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  StatusBadge(status: document.status, compact: true),
                  if (onView != null) ...[
                    const SizedBox(height: 6),
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
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
