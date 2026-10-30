/// One SET or SEF semester row linked to an uploaded document (read-only faculty view).
class TeachingEvaluationRecord {
  const TeachingEvaluationRecord({
    required this.id,
    required this.documentId,
    required this.fileName,
    required this.evaluationType,
    this.academicYear,
    this.semester,
    this.ratingRaw,
    this.ratingScale,
    this.extractionStatus,
    this.ocrVerificationStatus,
    this.reviewerValidationStatus,
    this.reviewerRemarks,
    this.sourceSectionRef,
    this.incompleteExtraction = false,
    this.duplicatePeriodWarning = false,
    this.missingFields = const [],
  });

  final String id;
  final String documentId;
  final String fileName;
  final String evaluationType;
  final String? academicYear;
  final String? semester;
  final String? ratingRaw;
  final num? ratingScale;
  final String? extractionStatus;
  final String? ocrVerificationStatus;
  final String? reviewerValidationStatus;
  final String? reviewerRemarks;
  final String? sourceSectionRef;
  final bool incompleteExtraction;
  final bool duplicatePeriodWarning;
  final List<String> missingFields;

  factory TeachingEvaluationRecord.fromApi(Map<String, dynamic> json) {
    final missing = json['missingFields'];
    return TeachingEvaluationRecord(
      id: (json['id'] as String?) ??
          (json['teachingEvaluationId'] as String?) ??
          '',
      documentId: (json['documentId'] as String?) ?? '',
      fileName: (json['fileName'] as String?) ?? '',
      evaluationType: (json['evaluationType'] as String?) ?? '',
      academicYear: json['academicYear'] as String?,
      semester: json['semester'] as String?,
      ratingRaw: json['ratingRaw'] as String?,
      ratingScale: json['ratingScale'] as num?,
      extractionStatus: json['extractionStatus'] as String?,
      ocrVerificationStatus: json['ocrVerificationStatus'] as String?,
      reviewerValidationStatus: json['reviewerValidationStatus'] as String?,
      reviewerRemarks: json['reviewerRemarks'] as String?,
      sourceSectionRef: json['sourceSectionRef'] as String?,
      incompleteExtraction: json['incompleteExtraction'] == true,
      duplicatePeriodWarning: json['duplicatePeriodWarning'] == true,
      missingFields: missing is List
          ? missing.map((e) => '$e').toList()
          : const [],
    );
  }
}
