import 'package:flutter/material.dart';

import 'kra3_catalog.dart';

/// Maps backend ``ocrExtraction.fields`` to form state and helper copy.
abstract final class Kra3OcrSync {
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
    if (v == null || v.isEmpty) return null;
    if (isMetadataLabelValue(v, fieldId: fieldId)) return null;
    if ((fieldId == 'outputTitle' || fieldId == 'activityTitle') &&
        isPlaceholderTitle(null, v)) {
      return null;
    }
    return v;
  }

  static String bundleValue(Map<String, dynamic>? bundle, String fieldId) {
    if (bundle == null) return '';
    if (fieldId == 'activityTitle') {
      return (bundle['activityTitle'] ?? bundle['outputTitle'] ?? '').toString().trim();
    }
    var v = bundle[fieldId]?.toString().trim() ?? '';
    if (fieldId == 'outputVenue' && v.isEmpty) {
      v = bundle['journalTitle']?.toString().trim() ?? '';
    }
    return v;
  }

  static final RegExp _disclaimerTitlePattern = RegExp(
    r'(fictional|for system testing|system testing only|not a real|not an official|'
    r'sample document|for testing purposes|facultylink test|simulated test evidence|'
    r'software testing only|synthetic|not issued|not authentic)',
    caseSensitive: false,
  );

  static bool isMetadataLabelValue(String value, {String fieldId = ''}) {
    final t = value.trim();
    if (t.isEmpty) return true;
    if (fieldId == 'outputTitle' && isDisclaimerTitle(t)) return true;
    if (fieldId == 'outputVenue' && _looksLikePublisherOrVenueName(t)) return false;
    if (t.endsWith('/') || t.endsWith(' /')) return true;
    final lower = t.toLowerCase();
    if (RegExp(r'^(authors?|journal|venue|publisher|doi|date|book|title)$').hasMatch(lower)) {
      return true;
    }
    if (t.contains('/') && RegExp(r'journal|publisher|author|inventor|organization|reference', caseSensitive: false).hasMatch(t)) {
      return true;
    }
    if (RegExp(
      r'publication information|page and publication|document details|journal / publisher|'
      r'issuing organization|testing instructions|supporting narrative|'
      r'please enter|enter the missing|try reading again|information below|'
      r"we couldn.t read|found in your document|before you send",
      caseSensitive: false,
    ).hasMatch(t)) {
      return true;
    }
    if (fieldId == 'authorsLine' &&
        t.length > 40 &&
        RegExp(r'\b(you|your|please|enter|missing)\b', caseSensitive: false).hasMatch(t) &&
        t.contains('.')) {
      return true;
    }
    if (fieldId == 'outputTitle' &&
        RegExp(r'\b(information|details|instructions|narrative|overview)\b', caseSensitive: false).hasMatch(t) &&
        t.length < 100) {
      return true;
    }
    if ((fieldId == 'publicationDate' || fieldId == 'registrationDate') &&
        !RegExp(r'^(19|20)\d{2}$').hasMatch(t) &&
        !RegExp(r'\d{4}[-/]\d{2}[-/]\d{2}').hasMatch(t) &&
        !RegExp(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', caseSensitive: false).hasMatch(t)) {
      return true;
    }
    return false;
  }

  static bool _looksLikePublisherOrVenueName(String value) {
    final t = value.trim();
    if (t.length < 4) return false;
    if (RegExp(r'\b(press|publisher|university|college|institute|journal of)\b', caseSensitive: false).hasMatch(t)) {
      return true;
    }
    return t.length >= 12 && !t.contains('/');
  }

  static bool isDisclaimerTitle(String value) {
    final t = value.trim();
    if (t.isEmpty) return false;
    if (!_disclaimerTitlePattern.hasMatch(t)) return false;
    if (t.length < 100 &&
        RegExp(r'\(FICTIONAL\)|\(NOT REAL\)', caseSensitive: false).hasMatch(t) &&
        RegExp(r'\b(press|publisher|university|college)\b', caseSensitive: false).hasMatch(t)) {
      return false;
    }
    return true;
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
      final groupTitle = Kra3Catalog.accomplishmentGroupTitle(indicatorId);
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
    if (isDisclaimerTitle(trimmed)) return true;
    if (isMetadataLabelValue(trimmed, fieldId: 'outputTitle')) return true;
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
      } else if (isMetadataLabelValue(current, fieldId: fieldId)) {
        // allow OCR to replace headings mistaken for values
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
    } else if (fromBundle.isNotEmpty &&
        !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, fromBundle)) &&
        !isMetadataLabelValue(fromBundle, fieldId: fieldId)) {
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
    if (isMetadataLabelValue(controllerText, fieldId: fieldId)) {
      return 'Please check this — we may have read a heading instead of the real value.';
    }
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
    if (text.isNotEmpty &&
        !isMetadataLabelValue(text, fieldId: fieldId) &&
        !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, text))) {
      return true;
    }
    final b = bundleValue(bundle, fieldId);
    if (b.isNotEmpty &&
        !isMetadataLabelValue(b, fieldId: fieldId) &&
        !(fieldId == 'outputTitle' && isPlaceholderTitle(bundle, b))) {
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
