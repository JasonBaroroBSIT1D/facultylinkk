import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/teaching_effectiveness_mapper.dart';
import 'package:facultylink_app/models/teaching_evaluation_record.dart';

void main() {
  test('recordsFromBlock prefers evaluationRecords', () {
    final block = {
      'evaluationRecords': [
        {
          'id': 'tev_1',
          'documentId': 'doc_1',
          'fileName': 'mixed.pdf',
          'evaluationType': 'SET',
          'academicYear': '2024-2025',
          'semester': '1st Semester',
          'ratingRaw': '90/100',
          'reviewerValidationStatus': 'pending-review',
        },
      ],
    };
    final rows = TeachingEffectivenessMapper.recordsFromBlock(block);
    expect(rows.length, 1);
    expect(rows.first.evaluationType, 'SET');
  });

  test('displayStatusForRecord flags duplicate and incomplete', () {
    const incomplete = TeachingEvaluationRecord(
      id: 'a',
      documentId: 'd',
      fileName: 'f.pdf',
      evaluationType: 'SET',
      incompleteExtraction: true,
    );
    expect(
      TeachingEffectivenessMapper.displayStatusForRecord(incomplete),
      'Incomplete Extraction',
    );
    const dup = TeachingEvaluationRecord(
      id: 'b',
      documentId: 'd',
      fileName: 'f.pdf',
      evaluationType: 'SEF',
      duplicatePeriodWarning: true,
      reviewerValidationStatus: 'approved',
    );
    expect(
      TeachingEffectivenessMapper.displayStatusForRecord(dup),
      'Duplicate Conflict',
    );
  });

  test('recordCounts reads coverageSummary fields', () {
    final counts = TeachingEffectivenessMapper.recordCounts({
      'coverageSummary': {
        'detectedEvaluationRecords': 12,
        'verifiedEligibleRecords': 6,
        'pendingRecords': 4,
        'rejectedOrRevisionRecords': 1,
        'incompleteRecords': 1,
        'excludedDuplicateRecords': 2,
      },
    });
    expect(counts['detected'], 12);
    expect(counts['verified'], 6);
  });
}
