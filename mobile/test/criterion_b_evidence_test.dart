import 'package:facultylink_app/data/criterion_b_catalog.dart';
import 'package:facultylink_app/data/criterion_b_evidence.dart';
import 'package:facultylink_app/models/enums.dart';
import 'package:facultylink_app/models/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Criterion B indicator grouping preserves IDs', () {
    expect(CriterionBCatalog.imGroups.length, 4);
    expect(CriterionBCatalog.programGroup.indicatorIds.length, 2);
    expect(CriterionBCatalog.isCriterionBIndicator('kra1-b-module-co'), isTrue);
    expect(CriterionBCatalog.isProgramIndicator('kra1-b-program-lead'), isTrue);
    expect(CriterionBCatalog.isCoAuthorIndicator('kra1-b-textbook-co'), isTrue);
  });

  test('scoring context single current score display', () {
    final estimated = CriterionBScoringContext.fromApi({
      'systemEstimatePoints': 30,
      'displayScore': {'label': 'Estimated', 'points': 30, 'source': 'automated_estimate'},
    });
    expect(estimated.currentScoreLabel, 'Estimated');
    expect(estimated.currentScoreDisplay, contains('30.00'));

    final assessed = CriterionBScoringContext.fromApi({
      'systemEstimatePoints': 30,
      'reviewerProposedAssessment': {
        'points': 28,
        'justification': 'Strong evidence with minor gaps',
      },
      'displayScore': {
        'label': 'Reviewer Assessed',
        'points': 28,
        'source': 'reviewer_assessment',
      },
    });
    expect(assessed.currentScoreLabel, 'Reviewer Assessed');
    expect(assessed.currentScoreDisplay, contains('28.00'));
    expect(assessed.systemEstimatePoints, 30);
  });

  test('supporting link role excludes primary claim', () {
    final doc = FacultyDocument(
      id: 'syl',
      title: 'Syllabus',
      category: DocumentCategory.supportingEvidence,
      kra: KraType.instruction,
      submittedAt: DateTime(2026),
      status: DocumentStatus.pendingReview,
      points: 0,
      fileName: 'syllabus.pdf',
      criterionId: CriterionBCatalog.criterionId,
      indicatorId: 'kra1-b-textbook-sole',
      criterionBEvidence: CriterionBEvidencePayload.fromApi({
        'link': {
          'role': 'supporting',
          'primaryDocumentId': 'doc_515',
          'evidenceSlot': 'approved_syllabus',
        },
      }),
    );
    expect(doc.isCriterionBPrimaryClaim, isFalse);
  });

  test('validation incomplete is not labeled invalid', () {
    final v = CriterionBValidation.fromApi({
      'validationStatus': 'incomplete',
      'flags': ['missing_imdc_evaluation_approval'],
    });
    expect(v.isHardInvalid, isFalse);
    expect(v.statusLabel, contains('Incomplete'));
  });

  test('checklist rows come from backend bundle only', () {
    final rows = CriterionBChecklistRow.fromBundle({
      'checklist': {
        'library_certification': {
          'status': 'missing',
          'documentId': null,
        },
        'imdc_evaluation_approval': {
          'status': 'present_unverified',
          'documentId': 'doc-2',
          'ocrHintOnly': true,
        },
      },
    });
    expect(rows.length, 2);
    expect(rows.any((r) => r.slotId == 'library_certification'), isTrue);
    expect(rows.firstWhere((r) => r.slotId == 'imdc_evaluation_approval').ocrHintOnly, isTrue);
  });

  test('supporting document does not count in simulation', () {
    final doc = FacultyDocument(
      id: 's1',
      title: 'Support',
      category: DocumentCategory.supportingEvidence,
      kra: KraType.instruction,
      submittedAt: DateTime(2026),
      status: DocumentStatus.pendingReview,
      points: 0,
      fileName: 'a.pdf',
      criterionId: CriterionBCatalog.criterionId,
      indicatorId: 'kra1-b-module-sole',
      effectiveSimulationScore: 16,
      criterionBEvidence: CriterionBEvidencePayload.fromApi({
        'isSupportingDocument': true,
        'link': {'role': 'supporting', 'primaryDocumentId': 'p1'},
      }),
    );
    expect(doc.isCriterionBSupportingDocument, isTrue);
    expect(doc.countsInSimulation, isFalse);
  });

  test('primary claim detection', () {
    final doc = FacultyDocument(
      id: 'p1',
      title: 'Primary',
      category: DocumentCategory.supportingEvidence,
      kra: KraType.instruction,
      submittedAt: DateTime(2026),
      status: DocumentStatus.pendingReview,
      points: 0,
      fileName: 'b.pdf',
      criterionId: CriterionBCatalog.criterionId,
      indicatorId: 'kra1-b-program-contributor',
    );
    expect(doc.isCriterionBPrimaryClaim, isTrue);
  });

  test('Criterion A constants unchanged for regression', () {
    expect(FacultyDocument.criterionAId, 'kra1-a');
    expect(FacultyDocument.isSetSefIndicatorId('kra1-a-student'), isTrue);
    expect(CriterionBCatalog.criterionId, isNot('kra1-a'));
  });

  test('payload parses reviewer remarks path via bundle', () {
    final payload = CriterionBEvidencePayload.fromApi({
      'bundle': {'reviewerRemarks': 'Please add dean certification.'},
      'validation': {'validationStatus': 'reviewer_required', 'readyForScoring': false},
    });
    expect(payload.bundle?['reviewerRemarks'], contains('dean'));
    expect(payload.validation?.readyForScoring, isFalse);
  });
}
