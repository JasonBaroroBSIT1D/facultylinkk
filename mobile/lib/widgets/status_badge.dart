import 'package:flutter/material.dart';

import '../models/enums.dart';
import '../theme/app_colors.dart';

class StatusBadge extends StatelessWidget {
  const StatusBadge({
    super.key,
    required this.status,
    this.compact = false,
  });

  final DocumentStatus status;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return _Pill(
      label: status.label,
      color: AppColors.status(status),
      background: AppColors.statusSoft(status),
      icon: status.icon,
      compact: compact,
    );
  }
}

class RequirementBadge extends StatelessWidget {
  const RequirementBadge({super.key, required this.status});

  final RequirementStatus status;

  @override
  Widget build(BuildContext context) {
    final (color, background, icon) = switch (status) {
      RequirementStatus.completed => (
          AppColors.success,
          AppColors.successSoft,
          Icons.check_circle_rounded,
        ),
      RequirementStatus.missing => (
          AppColors.error,
          AppColors.errorSoft,
          Icons.error_outline_rounded,
        ),
      RequirementStatus.pending => (
          AppColors.warning,
          AppColors.warningSoft,
          Icons.schedule_rounded,
        ),
      RequirementStatus.needsRevision => (
          AppColors.error,
          AppColors.errorSoft,
          Icons.edit_note_rounded,
        ),
    };

    return _Pill(
      label: status.label,
      color: color,
      background: background,
      icon: icon,
      compact: true,
    );
  }
}

class EligibilityBadge extends StatelessWidget {
  const EligibilityBadge({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return _Pill(
      label: label,
      color: AppColors.success,
      background: AppColors.successSoft,
      icon: Icons.verified_outlined,
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({
    required this.label,
    required this.color,
    required this.background,
    required this.icon,
    this.compact = false,
  });

  final String label;
  final Color color;
  final Color background;
  final IconData icon;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 10,
        vertical: compact ? 4 : 5,
      ),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: compact ? 12 : 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: color,
              fontSize: compact ? 11 : 12,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
