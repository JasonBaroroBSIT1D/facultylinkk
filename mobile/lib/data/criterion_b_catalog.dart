/// KRA I Criterion B — indicator grouping (IDs unchanged; matches Reviewer Web).
abstract final class CriterionBCatalog {
  static const criterionId = 'kra1-b';

  static const imGroups = <CriterionBIndicatorGroup>[
    CriterionBIndicatorGroup(
      label: 'Textbook',
      indicatorIds: ['kra1-b-textbook-sole', 'kra1-b-textbook-co'],
    ),
    CriterionBIndicatorGroup(
      label: 'Module',
      indicatorIds: ['kra1-b-module-sole', 'kra1-b-module-co'],
    ),
    CriterionBIndicatorGroup(
      label: 'Instructional Manual',
      indicatorIds: ['kra1-b-manual-sole', 'kra1-b-manual-co'],
    ),
    CriterionBIndicatorGroup(
      label: 'Multimedia Teaching Materials',
      indicatorIds: ['kra1-b-multimedia-sole', 'kra1-b-multimedia-co'],
    ),
  ];

  static const programGroup = CriterionBIndicatorGroup(
    label: 'Academic Programs',
    indicatorIds: ['kra1-b-program-lead', 'kra1-b-program-contributor'],
  );

  static bool isCriterionBIndicator(String? indicatorId) {
    if (indicatorId == null || indicatorId.isEmpty) return false;
    return indicatorId.startsWith('kra1-b-');
  }

  static bool isProgramIndicator(String? indicatorId) {
    return indicatorId == 'kra1-b-program-lead' ||
        indicatorId == 'kra1-b-program-contributor';
  }

  static bool isCoAuthorIndicator(String? indicatorId) {
    return indicatorId != null && indicatorId.endsWith('-co');
  }

  /// Display labels for checklist slot IDs returned by the backend bundle.
  static const slotLabels = <String, String>{
    'primary_material': 'Instructional material (primary file)',
    'imdc_evaluation_approval': 'IMDC or equivalent approval',
    'approved_syllabus': 'Approved syllabus or course guide',
    'library_certification': 'Library certification',
    'annex_c_contribution': 'Annex C — Certificate of Contribution',
    'complete_set_attestation': 'Complete set attestation',
    'originality_proof': 'Originality proof',
    'pedagogical_validity_proof': 'Pedagogical validity proof',
    'primary_contribution_document': 'Primary contribution document',
    'feasibility_study': 'Feasibility study',
    'benchmarking_report': 'Benchmarking report',
    'approved_program_outcomes': 'Approved program outcomes',
    'curriculum_obe_mapping': 'Curriculum / OBE mapping',
    'revised_curriculum_stakeholder_consultation':
        'Revised curriculum & stakeholder consultation',
    'dean_contribution_certification': 'Dean certification of contribution',
    'academic_council_resolution': 'Academic Council resolution',
    'governing_board_resolution': 'Governing Board resolution',
    'rrpa_or_copc': 'RRPA or COPC (as applicable)',
    'implementation_evidence': 'Implementation evidence',
  };

  static String slotLabel(String slotId) =>
      slotLabels[slotId] ?? slotId.replaceAll('_', ' ');
}

class CriterionBIndicatorGroup {
  const CriterionBIndicatorGroup({
    required this.label,
    required this.indicatorIds,
  });

  final String label;
  final List<String> indicatorIds;
}
