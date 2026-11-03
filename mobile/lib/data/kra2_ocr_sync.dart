import 'package:flutter/material.dart';

import 'kra2_catalog.dart';

/// Maps backend ``ocrExtraction.fields`` to form state and helper copy.
abstract final class Kra2OcrSync {
  static Map<String, Map<String, dynamic>> parseExtractionFields(
    Map<String, dynamic>? ocrExtraction,
  ) {
    final fields = ocrExtraction?['fields'];
    if (fields is! Map) return {};
    final out = <String, Map<String, dynamic>>{};
    for (final entry in fields.entries) {
      if (entry.value is Map) {
        out[entry.key.toString()] = Map<String, dynamic>.from(entry.value as Map);
      }
    }
    return out;
  }

  static String? ocrValue(Map<String, Map<String, dynamic>> fields, String fieldId) {
    final block = fields[fieldId];
    final v = block?['value']?.toString().trim();
    return (v == null || v.isEmpty) ? null : v;
  }

  static String bundleValue(Map<String, dynamic>? bundle, String fieldId) {
    if (bundle == null) return '';
    var v = bundle[fieldId]?.toString().trim() ?? '';
    if (fieldId == 'outputVenue' && v.isEmpty) {
      v = bundle['journalTitle']?.toString().trim() ?? '';
    }
    return v;
  }

  static bool isYearOnlyDate(String value) {
    final t = value.trim();
    return RegExp(r'^(19|20)\d{2}$').hasMatch(t);
  }

  static bool isPlaceholderTitle(Map<String, dynamic>? bundle, String value) {
    if (value.trim().isEmpty) return true;
    final trimmed = value.trim();
    final lower = trimmed.toLowerCase();
    final indicatorTitle = bundle?['indicatorTitle']?.toString().trim() ?? '';
    if (indicatorTitle.isNotEmpty && lower == indicatorTitle.toLowerCase()) {
      return true;
    }
    final indicatorId = bundle?['indicatorId']?.toString() ?? '';
    if (indicatorId.isNotEmpty) {
      final groupTitle = Kra2Catalog.accomplishmentGroupTitle(indicatorId);
      if (lower == groupTitle.toLowerCase()) return true;
    }
    const genericTitles = {
      'patent application',
      'patent publication',
      'patent certificate',
      'utility model',
      'industrial design',
    };
    if (genericTitles.contains(lower)) return true;
    return false;
  }

  /// Apply bundle + OCR values to controllers without clobbering faculty edits.
  static void syncController({
    required TextEditingController controller,
    required String fieldId,
    required Map<String, dynamic>? bundle,
    required Map<String, Map<String, dynamic>> ocrFields,
    required Set<String> userEditedFields,
  }) {
    if (userEditedFields.contains(fieldId)) return;
    final current = controller.text.trim();
    final dateField = fieldId == 'registrationDate' || fieldId == 'publicationDate';
    if (current.isNotEmpty) {
      if (fieldId == 'outputTitle' && isPlaceholderTitle(bundle, current)) {
        // allow OCR to replace generic accomplishment titles
      } else if (dateField && isYearOnlyDate(current)) {
        // allow full date from OCR to replace year-only values
      } else {
        return;
      }
    }
    final fromBundle = bundleValue(bundle, fieldId);
    final fromOcr = ocrValue(ocrFields, fieldId);
    String? pick;
    if (dateField &&
        fromOcr != null &&
        !isYearOnlyDate(fromOcr) &&
        (fromBundle.isEmpty || isYearOnlyDate(fromBundle) || isYearOnlyDate(current))) {
      pick = fromOcr;
    } else if (fromBundle.isNotEmpty && !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, fromBundle))) {
      pick = fromBundle;
    } else if (fromOcr != null) {
      pick = fromOcr;
    } else if (fieldId == 'outputVenue' && ocrValue(ocrFields, 'journalTitle') != null) {
      pick = ocrValue(ocrFields, 'journalTitle');
    }
    if (pick != null && pick.isNotEmpty) {
      controller.text = pick;
    }
  }

  static String fieldHelper({
    required String fieldId,
    required String controllerText,
    required Map<String, Map<String, dynamic>> ocrFields,
    required Map<String, dynamic>? bundle,
    required Set<String> userEditedFields,
    required List<String> reviewFlags,
  }) {
    if (fieldId == 'authorsLine' &&
        reviewFlags.contains('logged_in_faculty_not_detected_in_authors')) {
      return 'Your name was not listed on the document. Please check the names.';
    }
    final hasValue = fieldHasValue(
      fieldId: fieldId,
      controllerText: controllerText,
      bundle: bundle,
      ocrFields: ocrFields,
    );
    if (!hasValue) {
      return 'Please add this information.';
    }
    if (userEditedFields.contains(fieldId)) {
      return 'You changed this field.';
    }
    final block = ocrFields[fieldId];
    final status = block?['status']?.toString() ?? '';
    if (status == 'partial') {
      return 'Please check this — we only found part of the date or number.';
    }
    if (status == 'extracted' || ocrValue(ocrFields, fieldId) != null) {
      return 'Found in your document';
    }
    return 'Please check this.';
  }

  static bool fieldHasValue({
    required String fieldId,
    required String controllerText,
    Map<String, dynamic>? bundle,
    Map<String, Map<String, dynamic>> ocrFields = const {},
  }) {
    final text = controllerText.trim();
    if (text.isNotEmpty && !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, text))) {
      return true;
    }
    final b = bundleValue(bundle, fieldId);
    if (b.isNotEmpty && !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, b))) {
      return true;
    }
    return ocrValue(ocrFields, fieldId) != null;
  }

  @Deprecated('Use fieldHasValue with controllerText')
  static bool controllerHasValue(
    String fieldId,
    Map<String, dynamic>? bundle,
    Map<String, Map<String, dynamic>> ocrFields,
    Set<String> userEditedFields,
  ) {
    return fieldHasValue(fieldId: fieldId, controllerText: '', bundle: bundle, ocrFields: ocrFields);
  }
}
