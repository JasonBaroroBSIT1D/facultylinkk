import 'criterion_b_catalog.dart';
import 'criterion_b_evidence.dart';

/// Guided workflow steps shown to faculty (not backend statuses).
enum CriterionBWorkflowPhase {
  chooseType,
  enterDetails,
  uploadEvidence,
  reviewSubmission,
  trackReview,
  viewAssessment,
}

enum EvidenceRequirement { required, conditional, optional, notRequired }

/// Human-facing copy and progress for Criterion B (backend field IDs unchanged).
abstract final class CriterionBUx {
  static const accomplishmentInstructional = 'instructional_material';
  static const accomplishmentProgram = 'academic_program';

  static String accomplishmentLabel(String? claimType) {
    switch (claimType) {
      case accomplishmentProgram:
        return 'Academic program';
      case accomplishmentInstructional:
        return 'Instructional material';
      default:
        return 'Accomplishment';
    }
  }

  static CriterionBWorkflowPhase phaseForPrimary({
    required Map<String, dynamic>? bundle,
    required CriterionBValidation? validation,
    required bool hasPrimaryFile,
  }) {
    if (bundle == null || !hasPrimaryFile) {
      return CriterionBWorkflowPhase.uploadEvidence;
    }
    final status = validation?.validationStatus;
    if (status == 'valid' && validation?.readyForScoring == true) {
      return CriterionBWorkflowPhase.viewAssessment;
    }
    if (status == 'reviewer_required' ||
        (validation?.readyForReviewer == true && status != 'incomplete')) {
      return CriterionBWorkflowPhase.trackReview;
    }
    if (status == 'incomplete' || _hasOpenChecklist(bundle)) {
      return CriterionBWorkflowPhase.reviewSubmission;
    }
    return CriterionBWorkflowPhase.trackReview;
  }

  static bool _hasOpenChecklist(Map<String, dynamic> bundle) {
    final cl = bundle['checklist'];
    if (cl is! Map) return true;
    for (final entry in cl.entries) {
      final v = entry.value;
      if (v is! Map) continue;
      final st = (v['status'] as String?) ?? 'missing';
      if (st == 'missing' || st == 'present_unverified' || st == 'reviewer_required') {
        return true;
      }
    }
    return false;
  }

  static String phaseTitle(CriterionBWorkflowPhase phase) {
    switch (phase) {
      case CriterionBWorkflowPhase.chooseType:
        return 'Choose accomplishment';
      case CriterionBWorkflowPhase.enterDetails:
        return 'Accomplishment details';
      case CriterionBWorkflowPhase.uploadEvidence:
        return 'Upload documents';
      case CriterionBWorkflowPhase.reviewSubmission:
        return 'Review your submission';
      case CriterionBWorkflowPhase.trackReview:
        return 'Reviewer verification';
      case CriterionBWorkflowPhase.viewAssessment:
        return 'Assessment preview';
    }
  }

  static String phaseSubtitle(CriterionBWorkflowPhase phase) {
    switch (phase) {
      case CriterionBWorkflowPhase.chooseType:
        return 'Pick instructional material or academic program work.';
      case CriterionBWorkflowPhase.enterDetails:
        return 'Use plain language—your reviewer sees the same summary.';
      case CriterionBWorkflowPhase.uploadEvidence:
        return 'Upload each required document from the checklist below.';
      case CriterionBWorkflowPhase.reviewSubmission:
        return 'Fix anything still missing before your reviewer verifies.';
      case CriterionBWorkflowPhase.trackReview:
        return 'Your assigned reviewer checks each item; OCR does not approve files.';
      case CriterionBWorkflowPhase.viewAssessment:
        return 'Estimated points appear only after verified evidence.';
    }
  }

  /// Required / conditional / optional — mirrors backend docs, not new rules.
  static EvidenceRequirement requirementForSlot(
    String slotId, {
    required String? claimType,
    required String? indicatorId,
    required Map<String, dynamic>? bundle,
  }) {
    if (slotId == 'rrpa_or_copc') {
      return EvidenceRequirement.conditional;
    }
    if (claimType == accomplishmentProgram) {
      const mandatory = {
        'primary_contribution_document',
        'dean_contribution_certification',
        'academic_council_resolution',
        'governing_board_resolution',
        'implementation_evidence',
      };
      if (mandatory.contains(slotId)) return EvidenceRequirement.required;
      if (slotId == 'feasibility_study' || slotId == 'benchmarking_report') {
        final kind = bundle?['programDevelopmentKind']?.toString();
        if (kind == 'new_program') return EvidenceRequirement.conditional;
        return EvidenceRequirement.optional;
      }
      if (slotId == 'revised_curriculum_stakeholder_consultation') {
        final kind = bundle?['programDevelopmentKind']?.toString();
        if (kind == 'substantial_revision') return EvidenceRequirement.conditional;
        return EvidenceRequirement.optional;
      }
      if (slotId == 'approved_program_outcomes' || slotId == 'curriculum_obe_mapping') {
        return EvidenceRequirement.optional;
      }
      return EvidenceRequirement.required;
    }

    // Instructional material
    const always = {
      'primary_material',
      'imdc_evaluation_approval',
      'approved_syllabus',
      'library_certification',
    };
    if (always.contains(slotId)) return EvidenceRequirement.required;
    if (slotId == 'annex_c_contribution') {
      if (CriterionBCatalog.isCoAuthorIndicator(indicatorId)) {
        return EvidenceRequirement.required;
      }
      return EvidenceRequirement.notRequired;
    }
    if (slotId == 'complete_set_attestation') {
      final mt = bundle?['materialType']?.toString();
      if (mt == 'module' || mt == 'instructional_manual') {
        return EvidenceRequirement.required;
      }
      return EvidenceRequirement.notRequired;
    }
    if (slotId == 'originality_proof' || slotId == 'pedagogical_validity_proof') {
      final mt = bundle?['materialType']?.toString();
      if (mt == 'multimedia') return EvidenceRequirement.required;
      return EvidenceRequirement.notRequired;
    }
    return EvidenceRequirement.required;
  }

  static String requirementLabel(EvidenceRequirement r) {
    switch (r) {
      case EvidenceRequirement.required:
        return 'Required';
      case EvidenceRequirement.conditional:
        return 'Conditional';
      case EvidenceRequirement.optional:
        return 'Optional';
      case EvidenceRequirement.notRequired:
        return 'Not required';
    }
  }

  static String? slotPurpose(String slotId) {
    return _slotPurpose[slotId];
  }

  static const _slotPurpose = <String, String>{
    'primary_material': 'Your main textbook, module, manual, or multimedia file.',
    'imdc_evaluation_approval':
        'Proof that your material was evaluated and approved by IMDC or an equivalent body.',
    'approved_syllabus':
        'Official syllabus or course guide aligned with the material.',
    'library_certification': 'Certification that the material is available in the library.',
    'annex_c_contribution': 'Annex C certificate showing your co-author contribution.',
    'complete_set_attestation':
        'Attestation that a complete set of module or manual materials was submitted.',
    'originality_proof': 'Evidence of originality for multimedia materials.',
    'pedagogical_validity_proof': 'Evidence of pedagogical validity for multimedia.',
    'primary_contribution_document': 'Your main document describing the program work.',
    'feasibility_study': 'Feasibility study for a new program (when applicable).',
    'benchmarking_report': 'Benchmarking report for a new program (when applicable).',
    'approved_program_outcomes': 'Approved program outcomes (optional supporting file).',
    'curriculum_obe_mapping': 'Curriculum / outcomes-based education mapping (optional).',
    'revised_curriculum_stakeholder_consultation':
        'Stakeholder consultation record for a substantial revision.',
    'dean_contribution_certification':
        'Dean certification of your role and contribution to the program.',
    'academic_council_resolution': 'Academic Council resolution approving the program work.',
    'governing_board_resolution': 'Governing Board resolution approving the program work.',
    'rrpa_or_copc':
        'Risk Reduction and Prevention Assessment or Continuity of Operations Plan when applicable.',
    'implementation_evidence':
        'Evidence that the program change is implemented, not only approved on paper.',
  };

  static String humanizeFlag(String flag) {
    if (_flagMessages.containsKey(flag)) return _flagMessages[flag]!;
    if (flag.startsWith('missing_')) {
      final slot = flag.substring('missing_'.length);
      return 'Still needed: ${CriterionBCatalog.slotLabel(slot)}';
    }
    if (flag.startsWith('optional_') && flag.endsWith('_reviewer_required')) {
      return 'Optional document uploaded—reviewer has not verified it yet.';
    }
    return flag.replaceAll('_', ' ');
  }

  static const _flagMessages = <String, String>{
    'rrpa_copc_applicability_undetermined':
        'Your reviewer must decide whether RRPA or COPC applies to this program.',
    'missing_imdc_evaluation_approval': 'IMDC or equivalent approval is still required.',
    'missing_library_certification': 'Library certification is still required.',
    'missing_approved_syllabus': 'Approved syllabus or course guide is still required.',
    'missing_complete_set_attestation': 'Complete set attestation is still required.',
    'missing_dean_contribution_certification': 'Dean certification is still required.',
    'missing_implementation_evidence': 'Implementation evidence is still required.',
  };

  /// Faculty-facing four-state labels (not backend codes).
  static String facultyDocumentStatus(String status) {
    switch (status) {
      case 'verified':
        return 'Verified';
      case 'reviewer_required':
        return 'Needs correction';
      case 'present_unverified':
        return 'Uploaded';
      case 'missing':
        return 'Missing';
      case 'not_applicable':
        return 'Not required';
      default:
        return checklistStatusLabel(status);
    }
  }

  static String facultyWorkStatus(CriterionBValidation? validation) {
    if (validation == null) return 'In progress';
    if (validation.isHardInvalid) return 'Needs attention';
    if (validation.validationStatus == 'incomplete') return 'Incomplete';
    if (validation.readyForScoring) return 'Ready for assessment';
    if (validation.validationStatus == 'reviewer_required') return 'With reviewer';
    return validation.statusLabel;
  }

  static String checklistStatusLabel(String status) {
    switch (status) {
      case 'verified':
        return 'Verified by reviewer';
      case 'present_unverified':
        return 'Uploaded — waiting for reviewer';
      case 'reviewer_required':
        return 'Reviewer asked for more evidence';
      case 'missing':
        return 'Not uploaded yet';
      case 'not_applicable':
        return 'Not applicable (reviewer confirmed)';
      default:
        return status.replaceAll('_', ' ');
    }
  }

  static String submissionSummaryTitle(Map<String, dynamic>? bundle) {
    if (bundle == null) return 'Criterion B submission';
    if (bundle['claimType'] == accomplishmentProgram) {
      return (bundle['programName'] as String?)?.trim().isNotEmpty == true
          ? bundle['programName'] as String
          : 'Academic program submission';
    }
    return (bundle['materialTitle'] as String?)?.trim().isNotEmpty == true
        ? bundle['materialTitle'] as String
        : 'Instructional material submission';
  }

  static String accomplishmentTypeSubtitle({
    Map<String, dynamic>? bundle,
    String? indicatorId,
  }) {
    if (bundle?['claimType'] == accomplishmentProgram) {
      final role = bundle?['facultyRole']?.toString();
      if (role == 'lead') return 'Academic program · Lead';
      if (role == 'contributor') return 'Academic program · Contributor';
      return 'Academic program';
    }
    final mt = bundle?['materialType']?.toString();
    final typeLabel = switch (mt) {
      'textbook' => 'Textbook',
      'module' => 'Module',
      'instructional_manual' => 'Instructional manual',
      'multimedia' => 'Multimedia',
      _ => 'Teaching material',
    };
    final co = bundle?['authorship']?.toString() == 'co' ||
        CriterionBCatalog.isCoAuthorIndicator(indicatorId);
    return co ? '$typeLabel · Co-author' : '$typeLabel · Sole author';
  }
}
