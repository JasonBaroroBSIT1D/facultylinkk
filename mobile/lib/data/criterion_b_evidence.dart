import 'criterion_b_catalog.dart';

/// Parsed `criterionBEvidence` payload from faculty document APIs.
class CriterionBEvidencePayload {
  const CriterionBEvidencePayload({
    this.bundle,
    this.validation,
    this.scoring,
    this.contributionVerification,
    this.crossKraWarnings = const [],
    this.isSupportingDocument = false,
    this.link,
  });

  final Map<String, dynamic>? bundle;
  final CriterionBValidation? validation;
  final CriterionBScoringContext? scoring;
  final CriterionBContributionVerification? contributionVerification;
  final List<Map<String, dynamic>> crossKraWarnings;
  final bool isSupportingDocument;
  final Map<String, dynamic>? link;

  factory CriterionBEvidencePayload.fromApi(Map<String, dynamic>? json) {
    if (json == null) {
      return const CriterionBEvidencePayload();
    }
    final validationRaw = json['validation'];
    final scoringRaw = json['scoring'];
    final contribRaw = json['contributionVerification'];
    return CriterionBEvidencePayload(
      bundle: json['bundle'] is Map
          ? Map<String, dynamic>.from(json['bundle'] as Map)
          : null,
      validation: validationRaw is Map
          ? CriterionBValidation.fromApi(Map<String, dynamic>.from(validationRaw))
          : null,
      scoring: scoringRaw is Map
          ? CriterionBScoringContext.fromApi(Map<String, dynamic>.from(scoringRaw))
          : null,
      contributionVerification: contribRaw is Map
          ? CriterionBContributionVerification.fromApi(
              Map<String, dynamic>.from(contribRaw),
            )
          : null,
      crossKraWarnings: json['crossKraWarnings'] is List
          ? (json['crossKraWarnings'] as List)
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList()
          : const [],
      isSupportingDocument: json['isSupportingDocument'] == true,
      link: json['link'] is Map
          ? Map<String, dynamic>.from(json['link'] as Map)
          : null,
    );
  }

  String? get primaryDocumentIdFromLink =>
      link?['primaryDocumentId']?.toString();

  String? get evidenceSlotFromLink => link?['evidenceSlot']?.toString();
}

class CriterionBValidation {
  const CriterionBValidation({
    this.validationStatus,
    this.flags = const [],
    this.blockers = const [],
    this.checklistSummary = const {},
    this.readyForReviewer = false,
    this.readyForScoring = false,
    this.rrpaCopcApplicability,
    this.rrpaCopcApplicabilityNote,
  });

  final String? validationStatus;
  final List<String> flags;
  final List<String> blockers;
  final Map<String, String> checklistSummary;
  final bool readyForReviewer;
  final bool readyForScoring;
  final String? rrpaCopcApplicability;
  final String? rrpaCopcApplicabilityNote;

  factory CriterionBValidation.fromApi(Map<String, dynamic> json) {
    final flagsRaw = json['flags'];
    final blockersRaw = json['blockers'];
    final summaryRaw = json['checklistSummary'];
    final summary = <String, String>{};
    if (summaryRaw is Map) {
      summaryRaw.forEach((key, value) {
        summary['$key'] = '$value';
      });
    }
    return CriterionBValidation(
      validationStatus: json['validationStatus'] as String?,
      flags: flagsRaw is List ? flagsRaw.map((e) => '$e').toList() : const [],
      blockers:
          blockersRaw is List ? blockersRaw.map((e) => '$e').toList() : const [],
      checklistSummary: summary,
      readyForReviewer: json['readyForReviewer'] == true,
      readyForScoring: json['readyForScoring'] == true,
      rrpaCopcApplicability: json['rrpaCopcApplicability'] as String?,
      rrpaCopcApplicabilityNote: json['rrpaCopcApplicabilityNote'] as String?,
    );
  }

  String get statusLabel {
    switch (validationStatus) {
      case 'incomplete':
        return 'Incomplete — more evidence needed';
      case 'reviewer_required':
        return 'With reviewer — not verified yet';
      case 'valid':
        return 'Ready for scoring (reviewer verified)';
      case 'invalid':
        return 'Not eligible (confirmed issue)';
      default:
        return validationStatus ?? 'Unknown';
    }
  }

  bool get isHardInvalid => validationStatus == 'invalid';
}

/// Faculty-facing Annex C contribution confirmation status (co-author claims).
class CriterionBContributionVerification {
  const CriterionBContributionVerification({
    this.confirmationStatus,
    this.matchStatusLabel,
    this.recordedContributionPercent,
    this.legacyGrandfathered = false,
  });

  final String? confirmationStatus;
  final String? matchStatusLabel;
  final double? recordedContributionPercent;
  final bool legacyGrandfathered;

  factory CriterionBContributionVerification.fromApi(Map<String, dynamic> json) {
    double? asDouble(Object? raw) {
      if (raw is num) return raw.toDouble();
      if (raw is String) return double.tryParse(raw);
      return null;
    }

    return CriterionBContributionVerification(
      confirmationStatus: json['confirmationStatus'] as String?,
      matchStatusLabel: json['matchStatusLabel'] as String?,
      recordedContributionPercent: asDouble(json['recordedContributionPercent']),
      legacyGrandfathered: json['legacyGrandfathered'] == true,
    );
  }

  String get facultyStatusLabel {
    switch (confirmationStatus) {
      case 'confirmed':
        return 'Contribution Verified';
      case 'mismatch':
      case 'needs_clarification':
        return 'Needs Correction';
      case 'legacy_grandfathered':
        return 'Contribution Confirmation Required';
      case 'not_confirmed':
      default:
        return 'Awaiting Contribution Verification';
    }
  }

  String get facultyStatusDetail {
    switch (confirmationStatus) {
      case 'confirmed':
        return 'Your reviewer confirmed that your recorded contribution matches the Annex C certificate.';
      case 'mismatch':
        return 'Your recorded contribution does not match the Annex C on file. Update your claim or upload a corrected certificate using the usual document correction process.';
      case 'needs_clarification':
        return 'Your reviewer needs clarification on your contribution percentage. Check their feedback and submit corrections if asked.';
      case 'legacy_grandfathered':
        return 'Your assessment is on file. Your reviewer may confirm the Annex C contribution percentage when they next review this accomplishment.';
      default:
        return 'Your reviewer will confirm your contribution percentage against Annex C before any new assessment is finalized.';
    }
  }
}

class CriterionBScoringContext {
  const CriterionBScoringContext({
    this.systemEstimatePoints,
    this.guidelineCompliantVerifiedPoints,
    this.reviewerProposedPoints,
    this.reviewerProposedJustification,
    this.displayScoreLabel,
    this.displayScorePoints,
    this.displayScoreSource,
  });

  final double? systemEstimatePoints;
  final double? guidelineCompliantVerifiedPoints;
  final double? reviewerProposedPoints;
  final String? reviewerProposedJustification;
  final String? displayScoreLabel;
  final double? displayScorePoints;
  final String? displayScoreSource;

  factory CriterionBScoringContext.fromApi(Map<String, dynamic> json) {
    double? asDouble(Object? raw) {
      if (raw is num) return raw.toDouble();
      if (raw is String) return double.tryParse(raw);
      return null;
    }

    final proposed = json['reviewerProposedAssessment'];
    Map<String, dynamic>? proposedMap;
    if (proposed is Map) {
      proposedMap = Map<String, dynamic>.from(proposed);
    }
    final displayRaw = json['displayScore'];
    Map<String, dynamic>? displayMap;
    if (displayRaw is Map) {
      displayMap = Map<String, dynamic>.from(displayRaw);
    }
    return CriterionBScoringContext(
      systemEstimatePoints: asDouble(json['systemEstimatePoints']),
      guidelineCompliantVerifiedPoints: asDouble(json['guidelineCompliantVerifiedPoints']),
      reviewerProposedPoints: proposedMap != null ? asDouble(proposedMap['points']) : null,
      reviewerProposedJustification: proposedMap?['justification']?.toString(),
      displayScoreLabel: displayMap?['label']?.toString(),
      displayScorePoints: displayMap != null ? asDouble(displayMap['points']) : null,
      displayScoreSource: displayMap?['source']?.toString(),
    );
  }

  String get currentScoreLabel => displayScoreLabel ?? 'Estimated';

  String get currentScoreDisplay {
    if (displayScorePoints != null) {
      return '${displayScorePoints!.toStringAsFixed(2)} pts';
    }
    if (currentScoreLabel == 'Reviewer Assessed' && reviewerProposedPoints != null) {
      return '${reviewerProposedPoints!.toStringAsFixed(2)} pts';
    }
    if (systemEstimatePoints != null) {
      return '${systemEstimatePoints!.toStringAsFixed(2)} pts';
    }
    return 'Not available yet';
  }
}

/// Checklist row built from backend bundle (never a hardcoded required list).
class CriterionBChecklistRow {
  CriterionBChecklistRow({
    required this.slotId,
    required this.status,
    this.documentId,
    this.reviewerNote,
    this.ocrHintOnly = false,
  });

  final String slotId;
  final String status;
  final String? documentId;
  final String? reviewerNote;
  final bool ocrHintOnly;

  static List<CriterionBChecklistRow> fromBundle(Map<String, dynamic>? bundle) {
    if (bundle == null) return const [];
    final checklist = bundle['checklist'];
    if (checklist is! Map) return const [];
    final rows = <CriterionBChecklistRow>[];
    for (final entry in checklist.entries) {
      final slotId = entry.key.toString();
      final value = entry.value;
      if (value is! Map) continue;
      rows.add(
        CriterionBChecklistRow(
          slotId: slotId,
          status: (value['status'] as String?) ?? 'missing',
          documentId: value['documentId']?.toString(),
          reviewerNote: value['reviewerNote']?.toString(),
          ocrHintOnly: value['ocrHintOnly'] == true,
        ),
      );
    }
    rows.sort((a, b) => a.slotId.compareTo(b.slotId));
    return rows;
  }

  String get label => CriterionBCatalog.slotLabel(slotId);

  bool get isVerified => status == 'verified';

  bool get isMissing =>
      status == 'missing' ||
      (status != 'not_applicable' && (documentId == null || documentId!.isEmpty));
}
