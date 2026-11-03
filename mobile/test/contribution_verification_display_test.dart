import 'package:flutter_test/flutter_test.dart';

import 'package:facultylink_app/data/criterion_b_evidence.dart';

void main() {
  test('Contribution status labels for faculty', () {
    const awaiting = CriterionBContributionVerification(
      confirmationStatus: 'not_confirmed',
    );
    expect(awaiting.facultyStatusLabel, 'Awaiting Contribution Verification');

    const verified = CriterionBContributionVerification(
      confirmationStatus: 'confirmed',
    );
    expect(verified.facultyStatusLabel, 'Contribution Verified');

    const legacy = CriterionBContributionVerification(
      confirmationStatus: 'legacy_grandfathered',
      legacyGrandfathered: true,
    );
    expect(legacy.facultyStatusLabel, 'Contribution Confirmation Required');

    const mismatch = CriterionBContributionVerification(
      confirmationStatus: 'mismatch',
    );
    expect(mismatch.facultyStatusLabel, 'Needs Correction');
  });
}
