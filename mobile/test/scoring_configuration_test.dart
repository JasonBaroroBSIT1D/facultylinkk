import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/criterion_c_catalog.dart';
import 'package:facultylink_app/data/criterion_c_evidence.dart';
import 'package:facultylink_app/data/criterion_c_mapper.dart';
import 'package:facultylink_app/data/scoring_configuration.dart';

void main() {
  tearDown(ScoringConfigurationHolder.clear);

  test('parses Phase C5 faculty scoring configuration payload', () {
    final cfg = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(cfg.hasApplicableConfiguration, isTrue);
    expect(cfg.metadata.version, 5);
    expect(cfg.metadata.effectiveFrom, '2023-08-01');
    expect(cfg.criterionMax('kra1-c'), 10);
    expect(cfg.indicatorPoints('kra1-c-adviser-ut'), 5);
  });

  test('dynamic Criterion C max from published configuration', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(CriterionCCatalog.maxPoints, 10);
    expect(CriterionCCatalog.usesPublishedConfiguration, isTrue);
  });

  test('dynamic UT adviser preview points', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi(scoringConfigurationFixture());
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

  test('mentorship points from configuration', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(CriterionCCatalog.mentorshipPoints, 3);
  });

  test('missing applicable configuration does not use annex fallback', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi({
      'configuration': null,
      'kraSettings': {},
      'metadata': {'provenance': 'none_available'},
      'message': 'No applicable official scoring configuration.',
    });
    expect(CriterionCCatalog.officialPointsForIndicator('kra1-c-adviser-sp'), isNull);
    expect(CriterionCCatalog.criterionCScoringReady, isFalse);
  });

  test('annex fallback when holder empty (mock/tests)', () {
    ScoringConfigurationHolder.clear();
    expect(CriterionCCatalog.officialPointsForIndicator('kra1-c-adviser-sp'), 3);
    expect(CriterionCCatalog.maxPoints, 10);
  });

  test('criterion C indicators completeness check', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(ScoringConfigurationHolder.current!.criterionCIndicatorsComplete, isTrue);
  });

  test('KRA max from kraSettings', () {
    final cfg = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    expect(cfg.kraMax('kra1'), 100);
  });

  test('evaluation-period provenance flags version binding', () {
    final payload = Map<String, dynamic>.from(scoringConfigurationFixture());
    (payload['metadata'] as Map)['provenance'] = 'evaluation_period';
    final cfg = ScoringConfiguration.fromApi(payload);
    expect(cfg.isEvaluationBound, isTrue);
  });

  test('CriterionCSummary maxPoints prefers API then published cap', () {
    ScoringConfigurationHolder.current = ScoringConfiguration.fromApi(scoringConfigurationFixture());
    final fromApi = CriterionCSummary.fromApi({'maxPoints': 9, 'estimatedPoints': 4});
    expect(fromApi.maxPoints, 9);
    final fallback = CriterionCSummary.fromApi({'estimatedPoints': 4});
    expect(fallback.maxPoints, 10);
  });
}
