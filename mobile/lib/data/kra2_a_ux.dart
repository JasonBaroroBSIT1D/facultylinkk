import 'kra2_catalog.dart';

/// Plain-language labels for KRA II faculty mobile (no backend jargon).
abstract final class Kra2AUx {
  static Kra2FacultyStatus facultyStatus({
    required String? reviewStatus,
    required String? validationStatus,
    required bool submittedForReview,
  }) {
    final rs = (reviewStatus ?? 'pending').toLowerCase();
    if (rs == 'approved') {
      return Kra2FacultyStatus.approved;
    }
    if (rs == 'rejected') {
      return Kra2FacultyStatus.needsChanges;
    }
    if (submittedForReview) {
      return Kra2FacultyStatus.underReview;
    }
    return Kra2FacultyStatus.draft;
  }

  static String statusLabel(Kra2FacultyStatus status) {
    switch (status) {
      case Kra2FacultyStatus.draft:
        return 'Not sent yet';
      case Kra2FacultyStatus.underReview:
        return 'Sent for review';
      case Kra2FacultyStatus.approved:
        return 'Your work was approved';
      case Kra2FacultyStatus.needsChanges:
        return 'Please fix a few details';
    }
  }

  static String statusExplanation(Kra2FacultyStatus status) {
    switch (status) {
      case Kra2FacultyStatus.draft:
        return 'Finish your details, then tap Send for Review.';
      case Kra2FacultyStatus.underReview:
        return 'You will be notified when your reviewer decides.';
      case Kra2FacultyStatus.approved:
        return 'Your reviewer confirmed this accomplishment.';
      case Kra2FacultyStatus.needsChanges:
        return 'Open this item, update what is needed, and send again.';
    }
  }

  static String statusNextAction(Kra2FacultyStatus status) {
    switch (status) {
      case Kra2FacultyStatus.draft:
        return 'Finish your details';
      case Kra2FacultyStatus.underReview:
        return 'No action needed right now';
      case Kra2FacultyStatus.approved:
        return 'You are done with this item';
      case Kra2FacultyStatus.needsChanges:
        return 'Edit details and send again';
    }
  }

  static String humanizeBlocker(String message, {String indicatorId = ''}) {
    final m = message.trim();
    if (m.contains('missing_evidence_slot') || m.toLowerCase().contains('contribution_certificate')) {
      return 'Please upload the shared authorship certificate.';
    }
    if (m.toLowerCase().startsWith('please upload:')) {
      final label = m.substring(m.indexOf(':') + 1).trim();
      if (label.isNotEmpty) {
        return 'Please add: $label';
      }
      return 'Please add the required document.';
    }
    if (m.toLowerCase().contains('connection timeout') || m.toLowerCase().contains('timeout')) {
      return 'We could not reach the server. Please try again.';
    }
    final family = indicatorId.isNotEmpty ? Kra2Catalog.workflowFamily(indicatorId) : '';
    if (m == 'Please enter the author or inventor names.') {
      if (family == 'invention_ip') {
        return 'Please check the inventor names.';
      }
      if (family == 'performance_work' || family == 'creative_work') {
        return 'Please check the performer or creator names.';
      }
      return 'Please check the author names.';
    }
    const map = {
      'Please enter the title of your accomplishment.': 'Please enter the title.',
      'Please enter the registration or patent number.': 'Please enter the patent number.',
      'Please enter the registration date.': 'Please check the patent date.',
      'Please enter the publication or registration date.': 'Please check the date.',
      'Title of the research output is required.': 'Please enter the title.',
      'Journal or publication venue is required.': 'Please enter the journal name.',
      'Author line is required.': 'Please check the author names.',
      'Publication date is required.': 'Please enter the date.',
      'Declared contribution percentage (1–100) is required for co-authored outputs.':
          'Please enter your share of the work (1–100%).',
      'Confirm publication metadata before submission.':
          'Check the details below, then send for review.',
    };
    if (map.containsKey(m)) return map[m]!;
    if (m.toLowerCase().contains('author') && indicatorId.contains('patent')) {
      return 'Please enter the inventor names.';
    }
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
        return 'We couldn\'t find this information.';
      case 'processing':
      case 'pending':
      default:
        return 'Reading your document...';
    }
  }

  @Deprecated('Use readingFileLabel')
  static String ocrStatusLabel(String? status) => readingFileLabel(status);

  static String pointsLine({
    required Kra2FacultyStatus status,
    double? estimatedPoints,
    double? reviewerAssessedPoints,
  }) {
    if (status == Kra2FacultyStatus.approved) {
      final pts = reviewerAssessedPoints ?? estimatedPoints;
      if (pts != null) return 'Approved points: ${pts.toStringAsFixed(0)}';
    }
    if (estimatedPoints != null && estimatedPoints > 0) {
      return 'Possible points: ${estimatedPoints.toStringAsFixed(0)}';
    }
    return '';
  }

  static String pointsFootnote(Kra2FacultyStatus status) {
    if (status == Kra2FacultyStatus.approved) return '';
    return 'Final points will be confirmed after review.';
  }
}

enum Kra2FacultyStatus { draft, underReview, approved, needsChanges }
