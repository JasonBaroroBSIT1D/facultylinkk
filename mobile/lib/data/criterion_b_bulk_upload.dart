import '../screens/documents/document_flow_args.dart';
import 'criterion_b_catalog.dart';

/// Faculty bulk upload: map files to evidence slots (filename hints only — not verification).
abstract final class CriterionBBulkUpload {
  static const primaryImSlot = 'primary_material';
  static const primaryProgramSlot = 'primary_contribution_document';

  static List<String> assignableSlots({
    required CriterionBAddWorkDraft? draft,
    required String? indicatorId,
  }) {
    if (draft?.isProgram == true || CriterionBCatalog.isProgramIndicator(indicatorId)) {
      return const [
        primaryProgramSlot,
        'dean_contribution_certification',
        'academic_council_resolution',
        'governing_board_resolution',
        'implementation_evidence',
        'feasibility_study',
        'benchmarking_report',
        'approved_program_outcomes',
        'curriculum_obe_mapping',
        'revised_curriculum_stakeholder_consultation',
        'rrpa_or_copc',
      ];
    }
    final materialType = draft?.materialType ?? _materialTypeFromIndicator(indicatorId);
    final co = CriterionBCatalog.isCoAuthorIndicator(indicatorId);
    final slots = <String>[
      primaryImSlot,
      'imdc_evaluation_approval',
      'approved_syllabus',
      'library_certification',
    ];
    if (co) slots.add('annex_c_contribution');
    if (materialType == 'module' || materialType == 'instructional_manual') {
      slots.add('complete_set_attestation');
    }
    if (materialType == 'multimedia') {
      slots.add('originality_proof');
      slots.add('pedagogical_validity_proof');
    }
    return slots;
  }

  static String? _materialTypeFromIndicator(String? indicatorId) {
    if (indicatorId == null) return null;
    if (indicatorId.contains('textbook')) return 'textbook';
    if (indicatorId.contains('module')) return 'module';
    if (indicatorId.contains('manual')) return 'instructional_manual';
    if (indicatorId.contains('multimedia')) return 'multimedia';
    return null;
  }

  /// Suggested slot from filename keywords (hint only). Returns null when uncertain.
  static String? suggestSlotFromFileName(
    String fileName, {
    required List<String> allowedSlots,
  }) {
    final normalized = fileName.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]+'), ' ');
    final scores = <String, int>{};
    void bump(String slot, int weight) {
      if (!allowedSlots.contains(slot)) return;
      scores[slot] = (scores[slot] ?? 0) + weight;
    }

    if (RegExp(r'\b01\b|primary|main text|textbook|instructional material').hasMatch(normalized)) {
      bump(primaryImSlot, 3);
    }
    if (RegExp(r'imdc|evaluation.*approval|approval.*use').hasMatch(normalized)) {
      bump('imdc_evaluation_approval', 4);
    }
    if (RegExp(r'syllabus|course guide|course outline').hasMatch(normalized)) {
      bump('approved_syllabus', 4);
    }
    if (RegExp(r'library|librarian|certification of library').hasMatch(normalized)) {
      bump('library_certification', 4);
    }
    if (RegExp(r'complete set|attestation|stand alone|standalone').hasMatch(normalized)) {
      bump('complete_set_attestation', 4);
    }
    if (RegExp(r'annex c|contribution form|coauth|co author|co-author').hasMatch(normalized)) {
      bump('annex_c_contribution', 4);
    }
    if (RegExp(r'originality|concept note').hasMatch(normalized)) {
      bump('originality_proof', 3);
    }
    if (RegExp(r'pedagogical|validity|expert review').hasMatch(normalized)) {
      bump('pedagogical_validity_proof', 3);
    }
    if (RegExp(r'dean|certification of role').hasMatch(normalized)) {
      bump('dean_contribution_certification', 3);
    }
    if (RegExp(r'academic council|board resolution|governing board').hasMatch(normalized)) {
      bump('academic_council_resolution', 2);
      bump('governing_board_resolution', 2);
    }
    if (RegExp(r'feasibility').hasMatch(normalized)) {
      bump('feasibility_study', 3);
    }
    if (RegExp(r'benchmark').hasMatch(normalized)) {
      bump('benchmarking_report', 3);
    }
    if (RegExp(r'rrpa|copc').hasMatch(normalized)) {
      bump('rrpa_or_copc', 3);
    }
    if (RegExp(r'implementation').hasMatch(normalized)) {
      bump('implementation_evidence', 2);
    }
    if (RegExp(r'program lead|primary contribution').hasMatch(normalized)) {
      bump(primaryProgramSlot, 3);
    }

    if (scores.isEmpty) return null;
    final best = scores.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    if (best.length == 1 || best[0].value > (best.length > 1 ? best[1].value : 0)) {
      return best[0].value >= 2 ? best[0].key : null;
    }
    return null;
  }

  static String? validateAssignments(List<String?> assignments, {required bool program}) {
    final primary = program ? primaryProgramSlot : primaryImSlot;
    final primaryCount = assignments.where((s) => s == primary).length;
    if (primaryCount != 1) {
      return 'Choose exactly one file as the ${CriterionBCatalog.slotLabel(primary).toLowerCase()}.';
    }
    final used = <String>{};
    for (final slot in assignments) {
      if (slot == null || slot.isEmpty) {
        return 'Every selected file needs a document type.';
      }
      if (slot != primary && !used.add(slot)) {
        return 'Each supporting document type can only be used once. Adjust duplicates.';
      }
    }
    return null;
  }
}
