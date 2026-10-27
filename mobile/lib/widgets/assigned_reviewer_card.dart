import 'package:flutter/material.dart';

import '../data/app_state.dart';
import '../theme/app_colors.dart';
import 'common.dart';

class AssignedReviewerCard extends StatelessWidget {
  const AssignedReviewerCard({super.key, this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;
    final loading = state.assignedReviewerLoading;
    final error = state.assignedReviewerError;
    final reviewer = state.assignedReviewer;

    if (loading && reviewer == null) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(compact ? 12 : 16),
          child: Row(
            children: const [
              SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              SizedBox(width: 12),
              Expanded(child: Text('Loading assigned reviewer…')),
            ],
          ),
        ),
      );
    }

    if (error != null && reviewer == null) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(compact ? 12 : 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Assigned Reviewer',
                style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
              ),
              const SizedBox(height: 8),
              Text(error, style: const TextStyle(color: AppColors.textSecondary)),
              const SizedBox(height: 10),
              TextButton(
                onPressed: () => state.fetchAssignedReviewer(),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (reviewer == null || !reviewer.isAssigned) {
      return Card(
        child: Padding(
          padding: EdgeInsets.all(compact ? 12 : 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text(
                'Assigned Reviewer',
                style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
              ),
              SizedBox(height: 8),
              Text(
                'No reviewer assigned yet. Your administrator will assign a reviewer when available.',
                style: TextStyle(color: AppColors.textSecondary, height: 1.35),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: EdgeInsets.all(compact ? 12 : 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Assigned Reviewer',
              style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                FacultyAvatar(name: reviewer.name, size: compact ? 40 : 48),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        reviewer.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 16,
                        ),
                      ),
                      if (reviewer.designation.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          reviewer.designation,
                          style: const TextStyle(color: AppColors.textSecondary),
                        ),
                      ],
                      if (reviewer.office.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          reviewer.office,
                          style: const TextStyle(color: AppColors.textTertiary, fontSize: 13),
                        ),
                      ],
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.infoSoft,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: const Text(
                          'Assigned',
                          style: TextStyle(
                            color: AppColors.info,
                            fontWeight: FontWeight.w700,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
