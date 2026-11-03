import 'package:facultylink_app/data/criterion_b_teaching_wizard_flow.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CriterionBTeachingWizardFlow.steps', () {
    test('sole module includes complete set, not contribution', () {
      final steps = CriterionBTeachingWizardFlow.steps(
        materialKind: 'module',
        withOthers: false,
      );
      expect(steps, contains(CriterionBTeachingWizardStep.completeSet));
      expect(steps, isNot(contains(CriterionBTeachingWizardStep.contribution)));
      expect(steps.last, CriterionBTeachingWizardStep.readyToUpload);
    });

    test('co module includes contribution then complete set', () {
      final steps = CriterionBTeachingWizardFlow.steps(
        materialKind: 'module',
        withOthers: true,
      );
      final contrib = steps.indexOf(CriterionBTeachingWizardStep.contribution);
      final complete = steps.indexOf(CriterionBTeachingWizardStep.completeSet);
      expect(contrib, greaterThan(-1));
      expect(complete, greaterThan(contrib));
    });

    test('sole manual includes complete set', () {
      final steps = CriterionBTeachingWizardFlow.steps(
        materialKind: 'manual',
        withOthers: false,
      );
      expect(steps, contains(CriterionBTeachingWizardStep.completeSet));
    });

    test('co manual includes contribution and complete set', () {
      final steps = CriterionBTeachingWizardFlow.steps(
        materialKind: 'manual',
        withOthers: true,
      );
      expect(steps, contains(CriterionBTeachingWizardStep.contribution));
      expect(steps, contains(CriterionBTeachingWizardStep.completeSet));
    });

    test('co textbook skips complete set', () {
      final steps = CriterionBTeachingWizardFlow.steps(
        materialKind: 'book',
        withOthers: true,
      );
      expect(steps, contains(CriterionBTeachingWizardStep.contribution));
      expect(steps, isNot(contains(CriterionBTeachingWizardStep.completeSet)));
    });
  });
}
