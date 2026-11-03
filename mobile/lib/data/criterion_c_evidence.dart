import 'criterion_c_catalog.dart';
import 'criterion_c_research_metadata.dart';

class CriterionCEvidencePayload {
  const CriterionCEvidencePayload({
    this.bundle,
    this.validation,
    this.scoring,
    this.isSupportingDocument = false,
    this.link,
    this.ocrStatus,
    this.ocrExtraction,
  });

  final Map<String, dynamic>? bundle;
  final CriterionCValidation? validation;
  final CriterionCScoring? scoring;
  final bool isSupportingDocument;
  final Map<String, dynamic>? link;
  final String? ocrStatus;
  final Map<String, dynamic>? ocrExtraction;

  factory CriterionCEvidencePayload.fromApi(Map<String, dynamic>? json) {
    if (json == null) return const CriterionCEvidencePayload();
    final bundleRaw = json['bundle'];
    final validationRaw = json['validation'];
    final scoringRaw = json['scoring'];
    final ocrRaw = json['ocrExtraction'];
    return CriterionCEvidencePayload(
      bundle: bundleRaw is Map ? Map<String, dynamic>.from(bundleRaw) : null,
      validation: validationRaw is Map
          ? CriterionCValidation.fromApi(Map<String, dynamic>.from(validationRaw))
          : null,
      scoring: scoringRaw is Map
          ? CriterionCScoring.fromApi(Map<String, dynamic>.from(scoringRaw))
          : null,
      isSupportingDocument: json['isSupportingDocument'] == true,
      link: json['link'] is Map ? Map<String, dynamic>.from(json['link'] as Map) : null,
      ocrStatus: json['ocrStatus'] as String?,
      ocrExtraction: ocrRaw is Map ? Map<String, dynamic>.from(ocrRaw) : null,
    );
  }
}

/// Bundle + OCR advisory values for the research confirmation step.
class CriterionCResearchMetadataForm {
  CriterionCResearchMetadataForm({
    required this.projectTitle,
    required this.studentNames,
    required this.studentGroupLabel,
    required this.academicYear,
    required this.completionDate,
    required this.needsConfirmation,
  });

  final String projectTitle;
  final String studentNames;
  final String studentGroupLabel;
  final String academicYear;
  final String completionDate;
  final Set<String> needsConfirmation;

  static CriterionCResearchMetadataForm fromPayload(CriterionCEvidencePayload payload) {
    final bundle = payload.bundle ?? {};
    String field(String key) => (bundle[key] ?? '').toString().trim();
    final ocrFields = payload.ocrExtraction?['fields'];
    final needs = <String>{};
    const keys = [
      'projectTitle',
      'studentNames',
      'studentGroupLabel',
      'academicYear',
      'completionDate',
    ];
    final confirmedMap =
        bundle['metadataConfirmed'] is Map ? Map<String, dynamic>.from(bundle['metadataConfirmed'] as Map) : null;
    final values = <String, String>{};
    for (final key in keys) {
      final value = CriterionCResearchMetadata.effectiveFieldValue(
        key: key,
        bundleValue: field(key),
        ocrFields: ocrFields is Map ? Map<String, dynamic>.from(ocrFields) : null,
        metadataConfirmed: confirmedMap,
      );
      values[key] = value;
      final confirmed = confirmedMap?[key] == true;
      if (key == 'studentGroupLabel' && value.isEmpty) {
        continue;
      }
      if (value.isEmpty || !confirmed) {
        needs.add(key);
      }
    }
    return CriterionCResearchMetadataForm(
      projectTitle: values['projectTitle']!,
      studentNames: values['studentNames']!,
      studentGroupLabel: values['studentGroupLabel']!,
      academicYear: values['academicYear']!,
      completionDate: values['completionDate']!,
      needsConfirmation: needs,
    );
  }

  bool get canContinue =>
      projectTitle.trim().isNotEmpty &&
      studentNames.trim().isNotEmpty &&
      completionDate.trim().isNotEmpty;

  Map<String, dynamic> toPatchBody() => {
        'projectTitle': projectTitle.trim(),
        'studentNames': studentNames.trim(),
        'studentGroupLabel': studentGroupLabel.trim(),
        'academicYear': academicYear.trim(),
        'completionDate': completionDate.trim(),
        'confirmMetadata': true,
      };
}

class CriterionCValidation {
  const CriterionCValidation({
    this.validationStatus,
    this.flags = const [],
    this.blockers = const [],
    this.checklistSummary = const {},
    this.readyForReviewer = false,
    this.readyForScoring = false,
    this.reviewStatus,
  });

  final String? validationStatus;
  final List<String> flags;
  final List<String> blockers;
  final Map<String, String> checklistSummary;
  final bool readyForReviewer;
  final bool readyForScoring;
  final String? reviewStatus;

  bool get isHardInvalid => validationStatus == 'invalid';

  factory CriterionCValidation.fromApi(Map<String, dynamic> json) {
    final flagsRaw = json['flags'];
    final blockersRaw = json['blockers'];
    final summaryRaw = json['checklistSummary'];
    final summary = <String, String>{};
    if (summaryRaw is Map) {
      summaryRaw.forEach((k, v) {
        summary[k.toString()] = v?.toString() ?? '';
      });
    }
    return CriterionCValidation(
      validationStatus: json['validationStatus'] as String?,
      flags: flagsRaw is List ? flagsRaw.map((e) => e.toString()).toList() : const [],
      blockers: blockersRaw is List ? blockersRaw.map((e) => e.toString()).toList() : const [],
      checklistSummary: summary,
      readyForReviewer: json['readyForReviewer'] == true,
      readyForScoring: json['readyForScoring'] == true,
      reviewStatus: json['reviewStatus'] as String?,
    );
  }
}

class CriterionCScoring {
  const CriterionCScoring({
    this.estimatedPoints,
    this.reviewerAssessedPoints,
    this.indicatorId,
  });

  final double? estimatedPoints;
  final double? reviewerAssessedPoints;
  final String? indicatorId;

  factory CriterionCScoring.fromApi(Map<String, dynamic> json) {
    double? est;
    final e = json['estimatedPoints'];
    if (e is num) est = e.toDouble();
    double? assessed;
    final a = json['reviewerAssessedPoints'];
    if (a is num) assessed = a.toDouble();
    return CriterionCScoring(
      estimatedPoints: est,
      reviewerAssessedPoints: assessed,
      indicatorId: json['indicatorId'] as String?,
    );
  }
}

class CriterionCChecklistRow {
  CriterionCChecklistRow({
    required this.slotId,
    required this.status,
    this.documentId,
  });

  final String slotId;
  final String status;
  final String? documentId;

  String get label => CriterionCCatalog.slotLabel(slotId);

  static List<CriterionCChecklistRow> fromBundle(Map<String, dynamic>? bundle) {
    if (bundle == null) return [];
    final checklist = bundle['checklist'];
    if (checklist is! Map) return [];
    final mentorship = (bundle['serviceCategory'] ?? '').toString() == 'mentorship';
    final slots = CriterionCCatalog.requiredSlots(mentorship: mentorship);
    return slots
        .map((slot) {
          final entry = checklist[slot];
          if (entry is! Map) {
            return CriterionCChecklistRow(slotId: slot, status: 'missing');
          }
          return CriterionCChecklistRow(
            slotId: slot,
            status: (entry['status'] ?? 'missing').toString(),
            documentId: entry['documentId'] as String?,
          );
        })
        .toList();
  }
}

class CriterionCSummary {
  CriterionCSummary({
    this.estimatedPoints,
    this.validatedPoints,
    double? maxPoints,
    this.assessed = false,
    this.rawServiceSum,
    this.services = const [],
    this.accomplishmentCount = 0,
    this.aggregationPolicy,
  }) : maxPoints = maxPoints ?? CriterionCCatalog.maxPoints;

  final double? estimatedPoints;
  final double? validatedPoints;
  final double maxPoints;
  final bool assessed;
  final double? rawServiceSum;
  final List<Map<String, dynamic>> services;
  final int accomplishmentCount;
  final String? aggregationPolicy;

  factory CriterionCSummary.fromApi(Map<String, dynamic> json) {
    double? est;
    final e = json['estimatedPoints'];
    if (e is num) est = e.toDouble();
    double? raw;
    final r = json['rawServiceSum'];
    if (r is num) raw = r.toDouble();
    final servicesRaw = json['services'];
    final services = servicesRaw is List
        ? servicesRaw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
        : <Map<String, dynamic>>[];
    double? validated;
    final v = json['validatedPoints'];
    if (v is num) validated = v.toDouble();
    return CriterionCSummary(
      estimatedPoints: est,
      validatedPoints: validated,
      maxPoints: (json['maxPoints'] as num?)?.toDouble() ?? CriterionCCatalog.maxPoints,
      assessed: json['assessed'] == true,
      rawServiceSum: raw,
      services: services,
      accomplishmentCount: (json['accomplishmentCount'] as num?)?.toInt() ?? 0,
      aggregationPolicy: json['aggregationPolicy'] as String?,
    );
  }
}

class CriterionCAccomplishmentRow {
  const CriterionCAccomplishmentRow({
    required this.documentId,
    this.title,
    this.indicatorId,
    this.status,
    this.accomplishmentId,
    this.reviewStatus,
    this.validationStatus,
    this.projectTitle,
    this.estimatedPoints,
    this.reviewerAssessedPoints,
  });

  final String documentId;
  final String? title;
  final String? indicatorId;
  final String? status;
  final String? accomplishmentId;
  final String? reviewStatus;
  final String? validationStatus;
  final String? projectTitle;
  final double? estimatedPoints;
  final double? reviewerAssessedPoints;

  factory CriterionCAccomplishmentRow.fromApi(Map<String, dynamic> json) {
    double? est;
    final e = json['estimatedPoints'];
    if (e is num) est = e.toDouble();
    double? assessed;
    final a = json['reviewerAssessedPoints'];
    if (a is num) assessed = a.toDouble();
    return CriterionCAccomplishmentRow(
      documentId: (json['documentId'] ?? '').toString(),
      title: json['title'] as String?,
      indicatorId: json['indicatorId'] as String?,
      status: json['status'] as String?,
      accomplishmentId: json['accomplishmentId'] as String?,
      reviewStatus: json['reviewStatus'] as String?,
      validationStatus: json['validationStatus'] as String?,
      projectTitle: json['projectTitle'] as String?,
      estimatedPoints: est,
      reviewerAssessedPoints: assessed,
    );
  }
}
