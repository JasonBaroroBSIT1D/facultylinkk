import 'criterion_c_catalog.dart';
import 'criterion_c_evidence.dart';

abstract final class CriterionCUx {
  static String humanizeFlag(String flag) {
    switch (flag) {
      case 'duplicate_service_suspected':
        return 'This may duplicate another accomplishment you already saved.';
      case 'adviser_panel_same_thesis_review':
        return 'Adviser and panel roles on the same thesis need reviewer/policy review.';
      case 'project_title_missing':
        return 'Project or thesis title is required.';
      case 'student_names_missing':
        return 'Student name(s) are required.';
      case 'completion_date_missing':
        return 'Completion or approval date is required.';
      case 'competition_name_missing':
        return 'Competition or award name is required.';
      case 'review_rejected':
        return 'Reviewer rejected this accomplishment.';
      case 'reviewer_accomplishment_not_approved':
        return 'Awaiting reviewer approval.';
      default:
        if (flag.startsWith('missing_')) {
          final slot = flag.replaceFirst('missing_', '');
          return 'Missing: ${CriterionCCatalog.slotLabel(slot)}';
        }
        if (flag.startsWith('reviewer_required_')) {
          final slot = flag.replaceFirst('reviewer_required_', '');
          return '${CriterionCCatalog.slotLabel(slot)} uploaded — needs reviewer verification';
        }
        if (flag.startsWith('unverified_')) {
          return 'Evidence not yet verified by reviewer';
        }
        return flag.replaceAll('_', ' ');
    }
  }

  static String facultyWorkStatus(CriterionCValidation? validation, {String? reviewStatus}) {
    final rs = reviewStatus ?? validation?.reviewStatus;
    if (rs == 'rejected') return 'Rejected — see reviewer remarks';
    if (rs == 'approved') return 'Approved by reviewer';
    if (validation?.flags.contains('duplicate_service_suspected') == true) {
      return 'Needs review — possible duplicate';
    }
    if (validation?.flags.contains('adviser_panel_same_thesis_review') == true) {
      return 'Needs reviewer/policy review';
    }
    switch (validation?.validationStatus) {
      case 'valid':
        return 'Ready for reviewer scoring';
      case 'reviewer_required':
        return 'Under review — OCR does not mean approval';
      case 'invalid':
        return 'Not eligible';
      case 'incomplete':
      default:
        return 'Draft — finish details and evidence';
    }
  }

  /// Hub list line: backend review status + verified or estimated points (one accomplishment once).
  static String accomplishmentListStatusLine({
    String? reviewStatus,
    String? documentStatus,
    double? estimatedPoints,
    double? reviewerAssessedPoints,
    String? reviewerRemarks,
  }) {
    final rs = (reviewStatus ?? 'pending').toLowerCase();
    if (rs == 'approved') {
      final pts = reviewerAssessedPoints ?? estimatedPoints;
      if (pts != null) {
        return 'Approved by reviewer · ${pts.toStringAsFixed(1)} verified pts';
      }
      return 'Approved by reviewer';
    }
    if (rs == 'rejected') {
      final note = reviewerRemarks?.trim();
      if (note != null && note.isNotEmpty) {
        return 'Rejected · $note';
      }
      return 'Rejected';
    }
    final docSt = (documentStatus ?? '').toLowerCase().replaceAll('-', '_');
    if (docSt == 'draft') {
      final est = estimatedPoints;
      if (est != null) {
        return 'Draft · ${est.toStringAsFixed(1)} estimated pts';
      }
      return 'Draft — finish details and evidence';
    }
    final est = estimatedPoints;
    if (est != null) {
      return 'Under review · ${est.toStringAsFixed(1)} estimated pts';
    }
    return 'Under review';
  }

  static String checklistStatusLabel(String status) {
    switch (status) {
      case 'verified':
        return 'Verified by reviewer';
      case 'present_unverified':
        return 'Uploaded — pending review';
      case 'reviewer_required':
        return 'Needs reviewer verification';
      case 'missing':
      default:
        return 'Not uploaded';
    }
  }

  static String accomplishmentTitle(Map<String, dynamic>? bundle, {String? fallback}) {
    final title = bundle?['projectTitle']?.toString().trim();
    if (title != null && title.isNotEmpty) return title;
    return fallback ?? 'Criterion C accomplishment';
  }

  static String serviceSubtitle({String? indicatorId, Map<String, dynamic>? bundle}) {
    if (indicatorId == CriterionCCatalog.mentorIndicator) {
      final comp = bundle?['mentorship'];
      if (comp is Map) {
        final name = comp['competitionName']?.toString();
        if (name != null && name.isNotEmpty) return 'Mentorship · $name';
      }
      return 'Mentorship service';
    }
    for (final t in CriterionCCatalog.researchTypes) {
      if (indicatorId == t.adviserIndicator) return '${t.label} · Adviser';
      if (indicatorId == t.panelIndicator) return '${t.label} · Panel';
    }
    return indicatorId ?? '';
  }

  static bool needsPolicyReview(CriterionCValidation? validation) {
    if (validation == null) return false;
    return validation.flags.contains('adviser_panel_same_thesis_review') ||
        validation.flags.contains('duplicate_service_suspected');
  }
}
