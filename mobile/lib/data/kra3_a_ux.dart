import 'kra3_catalog.dart';

/// Plain-language labels for KRA III faculty mobile.
abstract final class Kra3AUx {
  static Kra3FacultyStatus facultyStatus({
    required String? reviewStatus,
    required String? validationStatus,
    required bool submittedForReview,
  }) {
    final rs = (reviewStatus ?? 'pending').toLowerCase();
    if (rs == 'approved') {
      return Kra3FacultyStatus.approved;
    }
    if (rs == 'rejected') {
      return Kra3FacultyStatus.needsChanges;
    }
    if (submittedForReview) {
      return Kra3FacultyStatus.underReview;
    }
    return Kra3FacultyStatus.draft;
  }

  static String statusLabel(Kra3FacultyStatus status) {
    switch (status) {
      case Kra3FacultyStatus.draft:
        return 'Not sent yet';
      case Kra3FacultyStatus.underReview:
        return 'Sent for review';
      case Kra3FacultyStatus.approved:
        return 'Your work was approved';
      case Kra3FacultyStatus.needsChanges:
        return 'Please fix a few details';
    }
  }

  static String statusExplanation(Kra3FacultyStatus status) {
    switch (status) {
      case Kra3FacultyStatus.draft:
        return 'Finish your details, then tap Send for Review.';
      case Kra3FacultyStatus.underReview:
        return 'You will be notified when your reviewer decides.';
      case Kra3FacultyStatus.approved:
        return 'Your reviewer confirmed this accomplishment.';
      case Kra3FacultyStatus.needsChanges:
        return 'Open this item, update what is needed, and send again.';
    }
  }

  static String statusNextAction(Kra3FacultyStatus status) {
    switch (status) {
      case Kra3FacultyStatus.draft:
        return 'Finish your details';
      case Kra3FacultyStatus.underReview:
        return 'No action needed right now';
      case Kra3FacultyStatus.approved:
        return 'You are done with this item';
      case Kra3FacultyStatus.needsChanges:
        return 'Edit details and send again';
    }
  }

  static String humanizeBlocker(String message, {String indicatorId = ''}) {
    final m = message.trim();
    if (m.toLowerCase().startsWith('please upload:')) {
      final label = m.contains(':') ? m.substring(m.indexOf(':') + 1).trim() : m;
      return label.isNotEmpty ? 'Please add: $label' : 'Please add the required document.';
    }
    if (m.toLowerCase().contains('connection') ||
        m.toLowerCase().contains('timeout') ||
        m.toLowerCase().contains('failed host lookup')) {
      return 'We could not reach the server at ${m.contains('http') ? 'your API' : 'the configured address'}. Check your network and API settings, then try again.';
    }
    if (m.toLowerCase().contains('host') && m.toLowerCase().contains('lookup')) {
      return 'Cannot reach the FacultyLink server. On a phone, use your computer\'s LAN IP with --dart-define=FL_API_BASE_URL=...';
    }
    const map = {
      'Please enter the activity or project name.': 'Please enter the activity name.',
      'Confirm publication metadata before submission.': 'Check the details below, then send for review.',
    };
    if (map.containsKey(m)) return map[m]!;
    return m;
  }

  static String readingFileLabel(String? status, {bool extractionIncomplete = false}) {
    switch ((status ?? '').toLowerCase()) {
      case 'complete':
      case 'completed':
      case 'done':
        if (extractionIncomplete) {
          return 'Please check these details.';
        }
        return 'We found your information.';
      case 'failed':
        return 'We couldn\'t read this document.';
      case 'processing':
      case 'pending':
      default:
        return 'Reading your document...';
    }
  }

  static String pointsLine({
    required Kra3FacultyStatus status,
    double? estimatedPoints,
    double? reviewerAssessedPoints,
    double? approvedPoints,
  }) {
    if (status == Kra3FacultyStatus.approved) {
      final pts = approvedPoints ?? estimatedPoints;
      if (pts != null) return 'Approved points: ${pts.toStringAsFixed(pts.truncateToDouble() == pts ? 0 : 1)}';
    }
    if (estimatedPoints != null && estimatedPoints > 0) {
      return 'Possible points: ${estimatedPoints.toStringAsFixed(estimatedPoints.truncateToDouble() == estimatedPoints ? 0 : 1)}';
    }
    return '';
  }

  static String pointsFootnote(Kra3FacultyStatus status) {
    if (status == Kra3FacultyStatus.approved) return '';
    return 'Final points will be confirmed after review.';
  }

  static String? reviewerFeedbackSummary({
    required Kra3FacultyStatus status,
    required String? reviewerRemarks,
    String? scoreAdjustmentReason,
  }) {
    final remarks = (reviewerRemarks ?? '').trim();
    if (status != Kra3FacultyStatus.approved && status != Kra3FacultyStatus.needsChanges) {
      return null;
    }
    if (remarks.isEmpty && (scoreAdjustmentReason ?? '').trim().isEmpty) {
      return null;
    }
    final parts = <String>[];
    if (remarks.isNotEmpty) parts.add(remarks);
    final reason = (scoreAdjustmentReason ?? '').trim();
    if (reason.isNotEmpty) {
      parts.add('Score adjustment: $reason');
    }
    return parts.join('\n\n');
  }
}

enum Kra3FacultyStatus { draft, underReview, approved, needsChanges }
