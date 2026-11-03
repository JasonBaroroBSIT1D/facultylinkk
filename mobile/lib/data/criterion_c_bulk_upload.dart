import 'criterion_c_catalog.dart';

/// Faculty bulk upload: map files to Criterion C checklist slots (filename hints only).
abstract final class CriterionCBulkUpload {
  static const approvalSheetSlot = 'approval_sheet';
  static const rrpaCopcSlot = 'rrpa_copc';

  static List<String> assignableSlots({required bool mentorship}) {
    return CriterionCCatalog.requiredSlots(mentorship: mentorship);
  }

  static String primarySlot({required bool mentorship}) {
    if (mentorship) {
      return 'mentor_designation';
    }
    return approvalSheetSlot;
  }

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

    if (RegExp(r'approval|signed|endorsement|thesis title page').hasMatch(normalized)) {
      bump(approvalSheetSlot, 4);
    }
    if (RegExp(r'rrpa|copc|research requirement|program outcomes').hasMatch(normalized)) {
      bump(rrpaCopcSlot, 4);
    }
    if (RegExp(r'mentor|coach|designation').hasMatch(normalized)) {
      bump('mentor_designation', 3);
    }
    if (RegExp(r'award|certificate|prize|photo').hasMatch(normalized)) {
      bump('award_certificate', 3);
    }
    if (RegExp(r'mechanics|winners|competition rules').hasMatch(normalized)) {
      bump('competition_mechanics', 3);
    }
    if (RegExp(r'organization profile|award giving|awarding org').hasMatch(normalized)) {
      bump('awarding_organization', 3);
    }

    if (scores.isEmpty) return null;
    final best = scores.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    if (best.length == 1 || best[0].value > (best.length > 1 ? best[1].value : 0)) {
      return best[0].value >= 2 ? best[0].key : null;
    }
    return null;
  }

  static String? validateAssignments(
    List<String?> assignments, {
    required bool mentorship,
  }) {
    final primary = primarySlot(mentorship: mentorship);
    final primaryCount = assignments.where((s) => s == primary).length;
    if (!mentorship && primaryCount != 1) {
      return 'Choose exactly one file as the ${CriterionCCatalog.slotLabel(primary).toLowerCase()}.';
    }
    if (mentorship && primaryCount > 1) {
      return 'Choose at most one file for ${CriterionCCatalog.slotLabel(primary).toLowerCase()}.';
    }
    final used = <String>{};
    for (final slot in assignments) {
      if (slot == null || slot.isEmpty) {
        return 'Every selected file needs an evidence type.';
      }
      if (!used.add(slot)) {
        return 'Each evidence type can only be used once. Adjust duplicates.';
      }
    }
    return null;
  }
}
