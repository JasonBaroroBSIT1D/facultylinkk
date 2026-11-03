import '../../models/enums.dart';

/// Opens [KraExplorerScreen] at KRA, criterion, or indicator level.
class KraExplorerLaunch {
  const KraExplorerLaunch({
    required this.kra,
    this.criterionId,
    this.indicatorId,
  });

  final KraType kra;
  final String? criterionId;
  final String? indicatorId;
}

/// Pre-selects KRA hierarchy on the upload form.
class UploadDocumentLaunch {
  const UploadDocumentLaunch({
    this.kra,
    this.criterionId,
    this.indicatorId,
    this.bundlePrimaryDocumentId,
    this.evidenceSlot,
    this.criterionBPrimaryFlow = false,
    this.criterionBDraft,
    this.criterionCPrimaryFlow = false,
    this.criterionCOcrFirstResearch = false,
    this.criterionCDraft,
  });

  final KraType? kra;
  final String? criterionId;
  final String? indicatorId;
  /// When set, upload attaches to an existing Criterion B primary claim.
  final String? bundlePrimaryDocumentId;
  final String? evidenceSlot;
  /// Guided Criterion B: upload main file then continue to checklist screens.
  final bool criterionBPrimaryFlow;
  final CriterionBAddWorkDraft? criterionBDraft;
  final bool criterionCPrimaryFlow;
  /// Research advising: upload approval sheet first, then remaining evidence (OCR runs in background).
  final bool criterionCOcrFirstResearch;
  final CriterionCAddWorkDraft? criterionCDraft;
}

/// Answers from Add Work — mapped to PATCH body after primary upload.
class CriterionBAddWorkDraft {
  const CriterionBAddWorkDraft({
    required this.accomplishmentKind,
    required this.indicatorId,
    this.materialTitle,
    this.materialType,
    this.contributionPercent,
    this.completeSetDeclared,
    this.programName,
    this.programDevelopmentKind,
    this.contributionDescription,
    this.committeeName,
  });

  final String accomplishmentKind;
  final String indicatorId;
  final String? materialTitle;
  final String? materialType;
  final int? contributionPercent;
  final bool? completeSetDeclared;
  final String? programName;
  final String? programDevelopmentKind;
  final String? contributionDescription;
  final String? committeeName;

  bool get isProgram =>
      accomplishmentKind == 'program' || accomplishmentKind == 'academic_program';
}

enum CriterionBWorkKind { teaching, program }

/// Wizard answers for Criterion C — PATCH after primary upload.
class CriterionCAddWorkDraft {
  const CriterionCAddWorkDraft({
    required this.serviceKind,
    required this.indicatorId,
    this.projectTitle,
    this.ocrFirstResearch = false,
    this.studentNames,
    this.studentGroupLabel,
    this.academicYear,
    this.completionDate,
    this.competitionName,
    this.prizeLevel,
    this.prizePlacement,
  });

  final String serviceKind;
  final String indicatorId;
  final String? projectTitle;
  final bool ocrFirstResearch;
  final String? studentNames;
  final String? studentGroupLabel;
  final String? academicYear;
  final String? completionDate;
  final String? competitionName;
  final String? prizeLevel;
  final String? prizePlacement;

  bool get isMentorship => serviceKind == 'mentorship';
}
