import 'package:facultylink_app/data/criterion_b_catalog.dart';
import 'package:facultylink_app/data/criterion_b_ux.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('humanizeFlag explains missing slots', () {
    expect(
      CriterionBUx.humanizeFlag('missing_library_certification'),
      contains('Library'),
    );
  });

  test('requirement reflects co-author annex C', () {
    expect(
      CriterionBUx.requirementForSlot(
        'annex_c_contribution',
        claimType: CriterionBUx.accomplishmentInstructional,
        indicatorId: 'kra1-b-module-co',
        bundle: const {'materialType': 'module'},
      ),
      EvidenceRequirement.required,
    );
    expect(
      CriterionBUx.requirementForSlot(
        'annex_c_contribution',
        claimType: CriterionBUx.accomplishmentInstructional,
        indicatorId: 'kra1-b-module-sole',
        bundle: const {'materialType': 'module'},
      ),
      EvidenceRequirement.notRequired,
    );
  });

  test('checklist status labels are nontechnical', () {
    expect(CriterionBUx.checklistStatusLabel('present_unverified'), contains('reviewer'));
    expect(CriterionBUx.checklistStatusLabel('verified'), contains('Verified'));
  });
}
