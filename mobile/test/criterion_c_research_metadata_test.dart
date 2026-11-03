import 'package:facultylink_app/data/criterion_c_evidence.dart';
import 'package:facultylink_app/data/criterion_c_research_metadata.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('unreliable title rejects sample approval sheet filename', () {
    expect(CriterionCResearchMetadata.isUnreliableTitle('01 Signed Approval Sheet SAMPLE'), isTrue);
    expect(CriterionCResearchMetadata.isUnreliableTitle('Campus Safety Drone System'), isFalse);
  });

  test('form prefers OCR title when bundle holds filename junk', () {
    final payload = CriterionCEvidencePayload.fromApi({
      'bundle': {
        'projectTitle': '01 Signed Approval Sheet SAMPLE',
        'studentNames': '',
        'academicYear': '2025-2026',
        'metadataConfirmed': {},
      },
      'ocrExtraction': {
        'fields': {
          'projectTitle': {'value': 'AI Tutor for Calculus Labs'},
          'studentNames': {'value': 'Kim Lee'},
        },
      },
    });
    final form = CriterionCResearchMetadataForm.fromPayload(payload);
    expect(form.projectTitle, 'AI Tutor for Calculus Labs');
    expect(form.studentNames, 'Kim Lee');
    expect(form.academicYear, '2025-2026');
  });

  test('optional group not flagged when empty', () {
    final payload = CriterionCEvidencePayload.fromApi({
      'bundle': {
        'projectTitle': 'Title',
        'studentNames': 'A',
        'completionDate': '2025-01-01',
        'metadataConfirmed': {
          'projectTitle': true,
          'studentNames': true,
          'completionDate': true,
        },
      },
    });
    final form = CriterionCResearchMetadataForm.fromPayload(payload);
    expect(form.needsConfirmation, isNot(contains('studentGroupLabel')));
  });
}
