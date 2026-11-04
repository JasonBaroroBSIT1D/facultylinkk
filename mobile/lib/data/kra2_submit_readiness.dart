import 'kra2_catalog.dart';
import 'kra2_ocr_sync.dart';

/// Faculty "Send for Review" readiness from live form state + checklist (not stale API validation).
abstract final class Kra2SubmitReadiness {
  static bool metadataComplete({
    required List<String> fieldIds,
    required String indicatorId,
    required String Function(String fieldId) controllerText,
    Map<String, dynamic>? bundle,
    Map<String, Map<String, dynamic>> ocrFields = const {},
  }) {
    for (final fieldId in fieldIds) {
      if (fieldId == 'publicationReference') continue;
      if (fieldId == 'declaredContributionPercent' &&
          Kra2Catalog.contributionMode(indicatorId) != 'declared') {
        continue;
      }
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: controllerText(fieldId),
        bundle: bundle,
        ocrFields: ocrFields,
      )) {
        return false;
      }
    }
    return true;
  }

  static bool allSlotsPresent({
    required List<String> requiredSlotIds,
    required bool Function(String slotId) slotMissing,
  }) {
    for (final slotId in requiredSlotIds) {
      if (slotMissing(slotId)) return false;
    }
    return true;
  }

  static bool canSubmitForReview({
    required List<String> fieldIds,
    required String indicatorId,
    required List<String> requiredSlotIds,
    required String Function(String fieldId) controllerText,
    required bool Function(String slotId) slotMissing,
    Map<String, dynamic>? bundle,
    Map<String, Map<String, dynamic>> ocrFields = const {},
  }) {
    return metadataComplete(
          fieldIds: fieldIds,
          indicatorId: indicatorId,
          controllerText: controllerText,
          bundle: bundle,
          ocrFields: ocrFields,
        ) &&
        allSlotsPresent(requiredSlotIds: requiredSlotIds, slotMissing: slotMissing);
  }

  static List<String> localBlockers({
    required List<String> fieldIds,
    required String indicatorId,
    required List<String> requiredSlotIds,
    required String Function(String fieldId) controllerText,
    required String Function(String fieldId) fieldLabel,
    required String Function(String slotId) slotLabel,
    required bool Function(String slotId) slotMissing,
    Map<String, dynamic>? bundle,
    Map<String, Map<String, dynamic>> ocrFields = const {},
  }) {
    final out = <String>[];
    for (final fieldId in fieldIds) {
      if (fieldId == 'publicationReference') continue;
      if (fieldId == 'declaredContributionPercent' &&
          Kra2Catalog.contributionMode(indicatorId) != 'declared') {
        continue;
      }
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: controllerText(fieldId),
        bundle: bundle,
        ocrFields: ocrFields,
      )) {
        final label = fieldLabel(fieldId);
        if (fieldId == 'outputTitle') {
          out.add('Please enter the title.');
        } else if (fieldId == 'authorsLine') {
          final family = Kra2Catalog.workflowFamily(indicatorId);
          if (family == 'performance_work' || indicatorId.startsWith('${Kra2Catalog.criterionC}-')) {
            out.add('Please check the performer or creator names.');
          } else {
            out.add('Please check the author names.');
          }
        } else {
          out.add('Please complete $label.');
        }
      }
    }
    for (final slotId in requiredSlotIds) {
      if (slotMissing(slotId)) {
        out.add('Please add: ${slotLabel(slotId)}.');
      }
    }
    return out;
  }
}
