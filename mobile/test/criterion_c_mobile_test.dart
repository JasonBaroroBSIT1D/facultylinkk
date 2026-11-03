import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/criterion_c_catalog.dart';
import 'package:facultylink_app/data/scoring_configuration.dart';
import 'package:facultylink_app/data/criterion_c_evidence.dart';
import 'package:facultylink_app/data/criterion_c_mapper.dart';
import 'package:facultylink_app/data/criterion_c_ux.dart';
import 'package:facultylink_app/navigation/app_routes.dart';

void main() {
  tearDown(ScoringConfigurationHolder.clear);

  test('Criterion C hub route registered', () {
    expect(AppRoutes.criterionCHub, '/criterion-c-hub');
  });

  test('research adviser UT maps to five estimated points', () {
    ScoringConfigurationHolder.current =
        ScoringConfiguration.fromApi(scoringConfigurationFixture());
    final type = CriterionCCatalog.researchTypes.firstWhere((t) => t.id == 'ut');
    expect(
      CriterionCMapper.previewPoints(
        kind: CriterionCServiceKind.research,
        researchType: type,
        role: CriterionCRole.adviser,
      ),
      5,
    );
  });

  test('mentorship maps to three points', () {
    ScoringConfigurationHolder.current =
        ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(
      CriterionCMapper.previewPoints(kind: CriterionCServiceKind.mentorship),
      3,
    );
  });

  test('panel DD maps to two points', () {
    ScoringConfigurationHolder.current =
        ScoringConfiguration.fromApi(scoringConfigurationFixture());
    final type = CriterionCCatalog.researchTypes.firstWhere((t) => t.id == 'dd');
    expect(
      CriterionCMapper.indicatorId(
        kind: CriterionCServiceKind.research,
        researchType: type,
        role: CriterionCRole.panel,
      ),
      'kra1-c-panel-dd',
    );
    expect(type.pointsForRole(CriterionCRole.panel), 2);
  });

  test('checklist rows for research', () {
    final rows = CriterionCChecklistRow.fromBundle({
      'serviceCategory': 'research',
      'checklist': {
        'approval_sheet': {'status': 'missing'},
        'rrpa_copc': {'status': 'present_unverified', 'documentId': 'd1'},
      },
    });
    expect(rows.length, 2);
    expect(rows.first.slotId, 'approval_sheet');
    expect(rows.last.documentId, 'd1');
  });

  test('checklist rows for mentorship', () {
    final rows = CriterionCChecklistRow.fromBundle({
      'serviceCategory': 'mentorship',
      'checklist': {
        'mentor_designation': {'status': 'missing'},
        'award_certificate': {'status': 'missing'},
        'competition_mechanics': {'status': 'missing'},
        'awarding_organization': {'status': 'missing'},
      },
    });
    expect(rows.length, 4);
  });

  test('duplicate flag humanized', () {
    expect(
      CriterionCUx.humanizeFlag('duplicate_service_suspected'),
      contains('duplicate'),
    );
  });

  test('adviser panel policy flag', () {
    expect(
      CriterionCUx.humanizeFlag('adviser_panel_same_thesis_review'),
      contains('policy'),
    );
  });

  test('validation parses API payload', () {
    final v = CriterionCValidation.fromApi({
      'validationStatus': 'incomplete',
      'flags': ['missing_approval_sheet'],
      'blockers': ['Project title required'],
      'checklistSummary': {'approval_sheet': 'missing'},
      'readyForReviewer': false,
    });
    expect(v.validationStatus, 'incomplete');
    expect(v.flags.first, 'missing_approval_sheet');
  });

  test('summary from API applies cap fields', () {
    final s = CriterionCSummary.fromApi({
      'estimatedPoints': 10,
      'maxPoints': 10,
      'assessed': true,
      'rawServiceSum': 12,
      'accomplishmentCount': 4,
    });
    expect(s.estimatedPoints, 10);
    expect(s.rawServiceSum, 12);
  });

  test('accomplishment row parses estimated points', () {
    final row = CriterionCAccomplishmentRow.fromApi({
      'documentId': 'doc_1',
      'indicatorId': 'kra1-c-adviser-sp',
      'estimatedPoints': 3,
      'reviewStatus': 'pending',
    });
    expect(row.estimatedPoints, 3);
  });

  test('accomplishment row parses reviewer assessed points', () {
    final row = CriterionCAccomplishmentRow.fromApi({
      'documentId': 'doc_help',
      'reviewStatus': 'approved',
      'estimatedPoints': 3,
      'reviewerAssessedPoints': 3,
    });
    expect(row.reviewerAssessedPoints, 3);
  });

  test('accomplishment list status line approved and pending', () {
    expect(
      CriterionCUx.accomplishmentListStatusLine(
        reviewStatus: 'approved',
        documentStatus: 'approved',
        estimatedPoints: 3,
        reviewerAssessedPoints: 3,
      ),
      'Approved by reviewer · 3.0 verified pts',
    );
    expect(
      CriterionCUx.accomplishmentListStatusLine(
        reviewStatus: 'pending',
        documentStatus: 'pending_review',
        estimatedPoints: 3,
      ),
      'Under review · 3.0 estimated pts',
    );
    expect(
      CriterionCUx.accomplishmentListStatusLine(
        reviewStatus: 'rejected',
        documentStatus: 'rejected',
        reviewerRemarks: 'Incomplete evidence',
      ),
      'Rejected · Incomplete evidence',
    );
  });

  test('summary from API parses validated points', () {
    final s = CriterionCSummary.fromApi({
      'validatedPoints': 3,
      'maxPoints': 10,
      'estimatedPoints': 3,
    });
    expect(s.validatedPoints, 3);
  });

  test('ten point cap constant', () {
    expect(CriterionCCatalog.maxPoints, 10);
  });

  test('official annex table covers all research types', () {
    expect(CriterionCCatalog.researchTypes.length, 4);
    for (final t in CriterionCCatalog.researchTypes) {
      expect(CriterionCCatalog.officialPointsForIndicator(t.adviserIndicator), isNotNull);
      expect(CriterionCCatalog.officialPointsForIndicator(t.panelIndicator), isNotNull);
    }
  });

  test('CriterionCResearchMetadataForm marks unconfirmed OCR fields', () {
    final payload = CriterionCEvidencePayload.fromApi({
      'bundle': {
        'projectTitle': 'Thesis Alpha',
        'studentNames': '',
        'completionDate': '2024-05-01',
        'metadataConfirmed': {'completionDate': true},
      },
      'ocrExtraction': {
        'fields': {
          'studentNames': {'value': 'Lee, Kim', 'confidence': 'medium'},
        },
      },
      'ocrStatus': 'completed',
    });
    final form = CriterionCResearchMetadataForm.fromPayload(payload);
    expect(form.projectTitle, 'Thesis Alpha');
    expect(form.studentNames, 'Lee, Kim');
    expect(form.needsConfirmation, contains('projectTitle'));
    expect(form.needsConfirmation, contains('studentNames'));
    expect(form.needsConfirmation, isNot(contains('completionDate')));
    expect(form.canContinue, isTrue);
  });

  test('CriterionCResearchMetadataForm patch body confirms metadata', () {
    final form = CriterionCResearchMetadataForm(
      projectTitle: 'T',
      studentNames: 'S',
      studentGroupLabel: '',
      academicYear: '2024-2025',
      completionDate: '2024-06-01',
      needsConfirmation: const {},
    );
    expect(form.canContinue, isTrue);
    expect(form.toPatchBody()['confirmMetadata'], isTrue);
  });
}
