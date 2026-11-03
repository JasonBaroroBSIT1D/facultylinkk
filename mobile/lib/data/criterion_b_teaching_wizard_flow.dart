import 'criterion_b_mapper.dart';

/// Ordered steps for the Criterion B teaching-material add-work wizard.
enum CriterionBTeachingWizardStep {
  material,
  title,
  authorship,
  contribution,
  completeSet,
  almostDone,
  readyToUpload,
}

/// Pure step sequencing (testable without widgets).
abstract final class CriterionBTeachingWizardFlow {
  static List<CriterionBTeachingWizardStep> steps({
    required String? materialKind,
    required bool? withOthers,
  }) {
    final sequence = <CriterionBTeachingWizardStep>[
      CriterionBTeachingWizardStep.material,
      CriterionBTeachingWizardStep.title,
      CriterionBTeachingWizardStep.authorship,
    ];
    if (materialKind == null || withOthers == null) {
      return sequence;
    }
    final needsComplete =
        CriterionBMapper.showCompleteSetQuestion(materialKind);
    if (withOthers) {
      sequence.add(CriterionBTeachingWizardStep.contribution);
      if (needsComplete) {
        sequence.add(CriterionBTeachingWizardStep.completeSet);
      }
    } else {
      if (needsComplete) {
        sequence.add(CriterionBTeachingWizardStep.completeSet);
      } else {
        sequence.add(CriterionBTeachingWizardStep.almostDone);
      }
    }
    sequence.add(CriterionBTeachingWizardStep.readyToUpload);
    return sequence;
  }

  static bool includesCompleteSetStep({
    required String? materialKind,
    required bool? withOthers,
  }) {
    return steps(materialKind: materialKind, withOthers: withOthers)
        .contains(CriterionBTeachingWizardStep.completeSet);
  }

  static bool includesContributionStep({
    required String? materialKind,
    required bool? withOthers,
  }) {
    return withOthers == true &&
        steps(materialKind: materialKind, withOthers: withOthers)
            .contains(CriterionBTeachingWizardStep.contribution);
  }
}
