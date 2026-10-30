import 'package:flutter/material.dart';

enum KraType {
  instruction,
  research,
  extension,
  professionalDevelopment;

  String get label {
    switch (this) {
      case KraType.instruction:
        return 'Instruction';
      case KraType.research:
        return 'Research and Innovation';
      case KraType.extension:
        return 'Extension or Community Services';
      case KraType.professionalDevelopment:
        return 'Professional Development';
    }
  }

  String get shortLabel {
    switch (this) {
      case KraType.instruction:
        return 'Instruction';
      case KraType.research:
        return 'Research';
      case KraType.extension:
        return 'Extension';
      case KraType.professionalDevelopment:
        return 'Prof. Development';
    }
  }

  String get code {
    switch (this) {
      case KraType.instruction:
        return 'KRA I';
      case KraType.research:
        return 'KRA II';
      case KraType.extension:
        return 'KRA III';
      case KraType.professionalDevelopment:
        return 'KRA IV';
    }
  }

  /// Compact dashboard module title (detail screens use [label]).
  String get dashboardModuleTitle {
    switch (this) {
      case KraType.instruction:
        return 'Instruction';
      case KraType.research:
        return 'Research & Innovation';
      case KraType.extension:
        return 'Extension Services';
      case KraType.professionalDevelopment:
        return 'Professional Development';
    }
  }

  IconData get icon {
    switch (this) {
      case KraType.instruction:
        return Icons.menu_book_rounded;
      case KraType.research:
        return Icons.science_outlined;
      case KraType.extension:
        return Icons.diversity_3_outlined;
      case KraType.professionalDevelopment:
        return Icons.workspace_premium_outlined;
    }
  }
}

enum DocumentStatus {
  draft,
  validated,
  systemApproved,
  pendingReview,
  needsRevision,
  invalid,
  processing;

  String get label {
    switch (this) {
      case DocumentStatus.draft:
        return 'Draft';
      case DocumentStatus.validated:
        return 'Validated';
      case DocumentStatus.systemApproved:
        return 'System Approved';
      case DocumentStatus.pendingReview:
        return 'Pending Review';
      case DocumentStatus.needsRevision:
        return 'Needs Revision';
      case DocumentStatus.invalid:
        return 'Invalid';
      case DocumentStatus.processing:
        return 'Processing';
    }
  }

  IconData get icon {
    switch (this) {
      case DocumentStatus.draft:
        return Icons.drafts_outlined;
      case DocumentStatus.validated:
        return Icons.verified_rounded;
      case DocumentStatus.systemApproved:
        return Icons.auto_awesome_rounded;
      case DocumentStatus.pendingReview:
        return Icons.hourglass_top_rounded;
      case DocumentStatus.needsRevision:
        return Icons.edit_note_rounded;
      case DocumentStatus.invalid:
        return Icons.gpp_bad_outlined;
      case DocumentStatus.processing:
        return Icons.sync_rounded;
    }
  }
}

enum DocumentCategory {
  supportingEvidence,
  teachingRecords,
  researchPublications,
  advisershipRecords,
  certifications,
  trainingCertificates,
  extensionDocuments;

  String get label {
    switch (this) {
      case DocumentCategory.supportingEvidence:
        return 'Supporting evidence';
      case DocumentCategory.teachingRecords:
        return 'Teaching records';
      case DocumentCategory.researchPublications:
        return 'Research publications';
      case DocumentCategory.advisershipRecords:
        return 'Advisership records';
      case DocumentCategory.certifications:
        return 'Certifications';
      case DocumentCategory.trainingCertificates:
        return 'Training/seminar certificates';
      case DocumentCategory.extensionDocuments:
        return 'Extension/community service documents';
    }
  }
}

enum RequirementStatus {
  completed,
  missing,
  pending,
  needsRevision;

  String get label {
    switch (this) {
      case RequirementStatus.completed:
        return 'Completed';
      case RequirementStatus.missing:
        return 'Missing';
      case RequirementStatus.pending:
        return 'Pending';
      case RequirementStatus.needsRevision:
        return 'Needs revision';
    }
  }
}

enum NotificationKind {
  documentValidated,
  documentNeedsRevision,
  reviewerFeedback,
  documentSubmitted,
  kraScoreUpdated,
  rankSimulationUpdated,
  missingRequirement;

  String get title {
    switch (this) {
      case NotificationKind.documentValidated:
        return 'Document validated';
      case NotificationKind.documentNeedsRevision:
        return 'Document requires revision';
      case NotificationKind.reviewerFeedback:
        return 'Reviewer provided feedback';
      case NotificationKind.documentSubmitted:
        return 'Document submitted successfully';
      case NotificationKind.kraScoreUpdated:
        return 'KRA score updated';
      case NotificationKind.rankSimulationUpdated:
        return 'Rank simulation updated';
      case NotificationKind.missingRequirement:
        return 'Missing requirement reminder';
    }
  }

  IconData get icon {
    switch (this) {
      case NotificationKind.documentValidated:
        return Icons.verified_rounded;
      case NotificationKind.documentNeedsRevision:
        return Icons.priority_high_rounded;
      case NotificationKind.reviewerFeedback:
        return Icons.chat_bubble_outline_rounded;
      case NotificationKind.documentSubmitted:
        return Icons.cloud_done_outlined;
      case NotificationKind.kraScoreUpdated:
        return Icons.insights_outlined;
      case NotificationKind.rankSimulationUpdated:
        return Icons.trending_up_rounded;
      case NotificationKind.missingRequirement:
        return Icons.playlist_add_check_rounded;
    }
  }
}

enum NotificationVisualState { unread, read, actionRequired }

enum PreparationPeriodStatus {
  upcoming,
  open,
  closingSoon,
  closed;

  String get label {
    switch (this) {
      case PreparationPeriodStatus.upcoming:
        return 'Upcoming';
      case PreparationPeriodStatus.open:
        return 'Open';
      case PreparationPeriodStatus.closingSoon:
        return 'Closing Soon';
      case PreparationPeriodStatus.closed:
        return 'Closed';
    }
  }

  String get guidance {
    switch (this) {
      case PreparationPeriodStatus.upcoming:
        return 'The published Rank Upgrade and Reclassification evaluation period has not started yet. You may sign in, upload documents, and review provisional simulation scores while you prepare supporting evidence.';
      case PreparationPeriodStatus.open:
        return 'The evaluation period is open. You may continue preparing evidence and provisional self-assessment; reviewers may provide preparatory feedback according to institutional policy.';
      case PreparationPeriodStatus.closingSoon:
        return 'The preparatory review period is ending soon. Please ensure that your documentary requirements are submitted for preparatory review.';
      case PreparationPeriodStatus.closed:
        return 'The evaluation period has ended. You may still view the schedule and continue document preparation where allowed; official submission and reviewer verification follow existing institutional restrictions for closed periods.';
    }
  }
}
