import '../models/teaching_evaluation_record.dart';

/// Labels and parsing for teaching-effectiveness API payloads (no client-side scoring).
abstract final class TeachingEffectivenessMapper {
  static Map<String, dynamic>? criterionAWorkspace(Map<String, dynamic>? tePayload) {
    final raw = tePayload?['criterionAWorkspace'];
    if (raw is Map) return Map<String, dynamic>.from(raw);
    return null;
  }

  static List<Map<String, dynamic>> sourceDocumentsFromTeachingPayload(
    Map<String, dynamic>? tePayload,
  ) {
    final ws = criterionAWorkspace(tePayload);
    final raw = ws?['sourceDocuments'];
    if (raw is! List) return const [];
    return raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  static List<TeachingEvaluationRecord> workspaceEvaluationRecords(
    Map<String, dynamic>? tePayload,
  ) {
    final ws = criterionAWorkspace(tePayload);
    return recordsFromBlock(ws);
  }

  static List<TeachingEvaluationRecord> recordsFromBlock(Map<String, dynamic>? block) {
    if (block == null) return const [];
    final raw = block['evaluationRecords'] ?? block['documents'];
    if (raw is! List) return const [];
    return raw
        .whereType<Map>()
        .map((e) => TeachingEvaluationRecord.fromApi(Map<String, dynamic>.from(e)))
        .toList();
  }

  static Map<String, int> recordCounts(Map<String, dynamic>? indicatorBlock) {
    final cov = indicatorBlock?['coverageSummary'];
    if (cov is Map) {
      return {
        'detected': _int(cov['detectedEvaluationRecords'] ?? cov['totalUploads']),
        'verified': _int(cov['verifiedEligibleRecords'] ?? cov['acceptedPeriods']),
        'pending': _int(cov['pendingRecords']),
        'rejectedOrRevision': _int(cov['rejectedOrRevisionRecords']),
        'incomplete': _int(cov['incompleteRecords']),
        'excludedDuplicates': _int(cov['excludedDuplicateRecords']),
      };
    }
    final rc = indicatorBlock?['recordCounts'];
    if (rc is Map) {
      return {
        'detected': _int(rc['detectedEvaluationRecords']),
        'verified': _int(rc['verifiedEligibleRecords']),
        'pending': _int(rc['pendingRecords']),
        'rejectedOrRevision': _int(rc['rejectedOrRevisionRecords']),
        'incomplete': _int(rc['incompleteRecords']),
        'excludedDuplicates': _int(rc['excludedDuplicateRecords']),
      };
    }
    return const {};
  }

  static String validationLabel(String? raw) {
    switch ((raw ?? '').replaceAll('_', '-')) {
      case 'approved':
      case 'valid':
        return 'Validated';
      case 'revision':
      case 'needs-revision':
        return 'Needs Revision';
      case 'rejected':
        return 'Rejected';
      case 'pending-review':
      case 'pending_review':
      case '':
        return 'Pending Review';
      default:
        return raw!.replaceAll('_', ' ');
    }
  }

  static String displayStatusForRecord(TeachingEvaluationRecord record) {
    if (record.duplicatePeriodWarning) return 'Duplicate Conflict';
    if (record.incompleteExtraction ||
        record.extractionStatus == 'partial' ||
        record.extractionStatus == 'ambiguous') {
      return 'Incomplete Extraction';
    }
    return validationLabel(record.reviewerValidationStatus);
  }

  static String? formatPoints(num? value) {
    if (value == null) return null;
    if (value == value.roundToDouble()) return value.toStringAsFixed(0);
    return value.toStringAsFixed(2);
  }

  static Map<String, dynamic>? criterionDisplay(Map<String, dynamic>? data) {
    final raw = data?['criterionADisplay'];
    if (raw is Map) return Map<String, dynamic>.from(raw);
    return null;
  }

  static String criterionEstimatedLabel(Map<String, dynamic>? data) {
    final disp = criterionDisplay(data);
    final est = data?['estimatedPoints'] ?? disp?['estimatedPoints'];
    if (est is num) {
      return 'Criterion A estimated: ${formatPoints(est)}';
    }
    final label = disp?['displayLabel'] as String?;
    if (label != null && label.isNotEmpty) return label;
    return 'Criterion A: not yet computable';
  }

  static String componentLine(Map<String, dynamic>? block) {
    if (block == null) return '—';
    final comp = block['componentDisplay'];
    if (comp is Map) {
      final label = comp['displayLabel'] as String?;
      if (label != null && label.isNotEmpty) return label;
    }
    final prov = block['provisionalPoints'] as num?;
    final val = block['validatedPoints'] as num?;
    final est = prov ?? val;
    if (est != null) return 'Estimated: ${formatPoints(est)}';
    final note = block['scoringNote'] as String?;
    if (note != null && note.isNotEmpty) return note;
    return 'Not yet computable';
  }

  static int _int(Object? value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return 0;
  }
}
