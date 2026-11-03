import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/criterion_b_evidence.dart';
import 'package:facultylink_app/models/models.dart';

void main() {
  test('KraScore maps integrated Criterion B (adapter on staging shape)', () {
    final kra1 = KraScore.fromApi({
      'kraId': 'kra1',
      'estimatedPoints': 14,
      'targetPoints': 100,
      'documentCount': 5,
      'statusLabel': 'Estimated from eligible evidence',
      'assessed': true,
      'criteriaScores': [
        {
          'criterionId': 'kra1-b',
          'estimatedPoints': 14,
          'maxPoints': 30,
          'simulationAdapterEnabled': true,
        },
      ],
    });
    expect(kra1.currentPoints, 14);
    expect(kra1.estimatedPoints, 14);
    expect(kra1.integrationFootnote, isNull);
  });

  test('KraScore shows footnote when adapter off but preview exists', () {
    final kra1 = KraScore.fromApi({
      'kraId': 'kra1',
      'estimatedPoints': 0,
      'targetPoints': 100,
      'documentCount': 5,
      'assessed': false,
      'criteriaScores': [
        {
          'criterionId': 'kra1-b',
          'accomplishmentPreviewPoints': 14,
          'accomplishmentPreviewNote': 'Not yet in KRA totals.',
          'simulationAdapterEnabled': false,
        },
      ],
    });
    expect(kra1.integrationFootnote, isNotNull);
    expect(kra1.integrationFootnote, contains('14'));
    expect(kra1.integrationFootnote, contains('preview'));
  });

  test('Accomplishment scoring: single Reviewer Assessed current score', () {
    final scoring = CriterionBScoringContext.fromApi({
      'displayScore': {
        'label': 'Reviewer Assessed',
        'points': 14,
        'source': 'reviewer_assessment',
      },
      'systemEstimatePoints': 15,
      'reviewerProposedAssessment': {'points': 14, 'justification': 'Verified evidence.'},
    });
    expect(scoring.currentScoreLabel, 'Reviewer Assessed');
    expect(scoring.displayScorePoints, 14);
    expect(scoring.systemEstimatePoints, 15);
  });
}
