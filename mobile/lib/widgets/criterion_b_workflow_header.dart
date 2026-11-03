import 'package:flutter/material.dart';

import '../data/criterion_b_ux.dart';
import '../theme/app_colors.dart';

/// Simple step indicator for faculty Criterion B submissions.
class CriterionBWorkflowHeader extends StatelessWidget {
  const CriterionBWorkflowHeader({super.key, required this.current});

  final CriterionBWorkflowPhase current;

  static const _order = [
    CriterionBWorkflowPhase.uploadEvidence,
    CriterionBWorkflowPhase.reviewSubmission,
    CriterionBWorkflowPhase.trackReview,
    CriterionBWorkflowPhase.viewAssessment,
  ];

  @override
  Widget build(BuildContext context) {
    final idx = _order.indexOf(current);
    final safeIdx = idx < 0 ? 0 : idx;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          CriterionBUx.phaseTitle(current),
          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: AppColors.navy),
        ),
        const SizedBox(height: 4),
        Text(
          CriterionBUx.phaseSubtitle(current),
          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
        ),
        const SizedBox(height: 12),
        Row(
          children: List.generate(_order.length, (i) {
            final done = i < safeIdx;
            final active = i == safeIdx;
            return Expanded(
              child: Container(
                margin: EdgeInsets.only(right: i < _order.length - 1 ? 4 : 0),
                height: 5,
                decoration: BoxDecoration(
                  color: done || active ? AppColors.forestLight : AppColors.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            );
          }),
        ),
      ],
    );
  }
}
