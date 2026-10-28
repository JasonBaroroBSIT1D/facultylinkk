import 'enums.dart';

class AssignedReviewer {
  const AssignedReviewer({
    required this.id,
    required this.name,
    this.designation = '',
    this.office = '',
    this.department = '',
    required this.assignmentStatus,
  });

  final String id;
  final String name;
  final String designation;
  final String office;
  final String department;
  final String assignmentStatus;

  bool get isAssigned => assignmentStatus == 'assigned' && name.isNotEmpty;

  factory AssignedReviewer.fromApi(Map<String, dynamic> data) {
    final reviewer = data['reviewer'];
    final status = (data['assignmentStatus'] as String?) ?? 'unassigned';
    if (reviewer == null || reviewer is! Map<String, dynamic>) {
      return AssignedReviewer(
        id: '',
        name: '',
        assignmentStatus: status,
      );
    }
    return AssignedReviewer(
      id: (reviewer['id'] as String?) ?? '',
      name: (reviewer['name'] as String?) ?? '',
      designation: (reviewer['designation'] as String?) ?? 'Institutional Reviewer',
      office: (reviewer['office'] as String?) ?? '',
      department: (reviewer['department'] as String?) ?? '',
      assignmentStatus: status,
    );
  }
}

class FacultyProfile {
  const FacultyProfile({
    required this.fullName,
    required this.facultyId,
    required this.email,
    required this.department,
    required this.college,
    required this.currentRank,
    this.targetRank = '',
    required this.highestDegree,
    required this.specialization,
    required this.yearsInService,
    required this.employmentStatus,
    required this.campus,
    required this.phone,
  });

  final String fullName;
  final String facultyId;
  final String email;
  final String department;
  final String college;
  final String currentRank;
  final String targetRank;
  final String highestDegree;
  final String specialization;
  final int yearsInService;
  final String employmentStatus;
  final String campus;
  final String phone;

  String get firstName =>
      fullName.trim().isEmpty ? 'Faculty' : fullName.split(' ').first;

  factory FacultyProfile.fromApi(Map<String, dynamic> json) {
    String field(String key) => (json[key] as String?)?.trim() ?? '';
    final employee = field('employeeNo');
    final facultyId = field('facultyId');
    return FacultyProfile(
      fullName: field('fullName'),
      facultyId: facultyId.isNotEmpty ? facultyId : employee,
      email: field('email'),
      department: field('department'),
      college: field('college'),
      currentRank: field('currentRank'),
      targetRank: field('targetRank'),
      highestDegree: field('highestDegree'),
      specialization: field('specialization'),
      yearsInService: (json['yearsInService'] as num?)?.toInt() ?? 0,
      employmentStatus: field('employmentStatus'),
      campus: field('campus'),
      phone: field('phone'),
    );
  }

  FacultyProfile copyWith({
    String? fullName,
    String? email,
    String? department,
    String? phone,
  }) {
    return FacultyProfile(
      fullName: fullName ?? this.fullName,
      facultyId: facultyId,
      email: email ?? this.email,
      department: department ?? this.department,
      college: college,
      currentRank: currentRank,
      targetRank: targetRank,
      highestDegree: highestDegree,
      specialization: specialization,
      yearsInService: yearsInService,
      employmentStatus: employmentStatus,
      campus: campus,
      phone: phone ?? this.phone,
    );
  }
}

class KraScore {
  const KraScore({
    required this.type,
    required this.currentPoints,
    required this.targetPoints,
    required this.documentCount,
    required this.statusLabel,
    required this.breakdown,
  });

  final KraType type;
  final int currentPoints;
  final int targetPoints;
  final int documentCount;
  final String statusLabel;
  final List<KraBreakdownItem> breakdown;

  double get progress =>
      targetPoints == 0 ? 0 : (currentPoints / targetPoints).clamp(0, 1);

  factory KraScore.fromApi(Map<String, dynamic> json) {
    final kraId = json['kraId'] as String?;
    final breakdownRaw = json['breakdown'];
    final breakdown = <KraBreakdownItem>[];
    if (breakdownRaw is List) {
      for (final item in breakdownRaw.whereType<Map>()) {
        breakdown.add(
          KraBreakdownItem(
            title: (item['title'] as String?) ?? 'Item',
            points: (item['points'] as num?)?.toInt() ?? 0,
            note: (item['note'] as String?) ?? '',
          ),
        );
      }
    }
    return KraScore(
      type: FacultyDocument.kraFromWebId(kraId),
      currentPoints: (json['currentPoints'] as num?)?.toInt() ?? 0,
      targetPoints: (json['targetPoints'] as num?)?.toInt() ?? 0,
      documentCount: (json['documentCount'] as num?)?.toInt() ?? 0,
      statusLabel: (json['statusLabel'] as String?) ?? 'Not yet calculated',
      breakdown: breakdown,
    );
  }
}

class KraBreakdownItem {
  const KraBreakdownItem({
    required this.title,
    required this.points,
    required this.note,
  });

  final String title;
  final int points;
  final String note;
}

class FacultyDocument {
  const FacultyDocument({
    required this.id,
    required this.title,
    required this.category,
    required this.kra,
    required this.submittedAt,
    required this.status,
    required this.points,
    required this.fileName,
    this.author,
    this.extractedInfo = const {},
    this.reviewerFeedback,
    this.validationResult,
    this.indicatorId,
    this.criterionId,
    this.mimeType,
    this.fileSize,
    this.hasFile = false,
    this.fileUrl,
    this.canDelete = false,
    this.canReplace = false,
    this.canRequestWithdrawal = false,
    this.effectiveSimulationScore,
    this.simulationScoreSource,
    this.reviewerOversightStatus,
    this.scoringStatus,
  });

  final String id;
  final String title;
  final DocumentCategory category;
  final KraType kra;
  final DateTime submittedAt;
  final DocumentStatus status;
  final int points;
  final String fileName;
  final String? author;
  final Map<String, String> extractedInfo;
  final String? reviewerFeedback;
  final String? validationResult;
  final String? indicatorId;
  final String? criterionId;
  final String? mimeType;
  final int? fileSize;
  final bool hasFile;
  final String? fileUrl;
  final bool canDelete;
  final bool canReplace;
  final bool canRequestWithdrawal;
  final double? effectiveSimulationScore;
  final String? simulationScoreSource;
  final String? reviewerOversightStatus;
  final String? scoringStatus;

  bool get countsInSimulation =>
      (effectiveSimulationScore != null && effectiveSimulationScore! > 0) ||
      (extractedInfo['SET period simulation score'] ?? '').trim().isNotEmpty ||
      (extractedInfo['SEF period simulation score'] ?? '').trim().isNotEmpty;

  bool get creditsPoints =>
      status == DocumentStatus.validated || status == DocumentStatus.systemApproved;

  String get creditedLabel {
    if (!creditsPoints) return '0';
    final verified = (extractedInfo['Verified score'] ?? '').trim();
    if (verified.isNotEmpty) return verified;
    return '$points';
  }

  String get provisionalLabel {
    final value = (extractedInfo['Provisional score'] ?? '').trim();
    return value.isEmpty ? '—' : value;
  }

  String get simulationScoreLabel {
    final periodRaw = (extractedInfo['SET period simulation score'] ??
            extractedInfo['SEF period simulation score'] ??
            '')
        .trim();
    final filled = (extractedInfo['Evaluation period filled'] ?? '').trim();
    if (periodRaw.isNotEmpty) {
      return 'Period $filled · $periodRaw pts';
    }
    if ((indicatorId == 'kra1-a-student' || indicatorId == 'kra1-a-supervisor') &&
        filled.isNotEmpty) {
      return 'Period $filled — need 6/6 for rank sim';
    }
    if (effectiveSimulationScore != null) {
      return effectiveSimulationScore!.toStringAsFixed(
        effectiveSimulationScore!.truncateToDouble() == effectiveSimulationScore! ? 0 : 1,
      );
    }
    return 'Score unavailable';
  }

  String get simulationSourceLabel {
    final source = simulationScoreSource ??
        extractedInfo['Simulation score source'] ??
        'Unavailable';
    if (source == 'System-calculated') return 'System-calculated';
    if (source == 'Reviewer-adjusted') return 'Reviewer-adjusted';
    return source;
  }

  bool get canResubmit =>
      status == DocumentStatus.needsRevision ||
      status == DocumentStatus.invalid;

  bool get requiresAction => status == DocumentStatus.needsRevision;

  static KraType kraFromWebId(String? kraId) {
    switch (kraId) {
      case 'kra1':
        return KraType.instruction;
      case 'kra2':
        return KraType.research;
      case 'kra3':
        return KraType.extension;
      case 'kra4':
        return KraType.professionalDevelopment;
      default:
        return KraType.instruction;
    }
  }

  static DocumentStatus statusFromWeb(String? raw) {
    switch (raw) {
      case 'draft':
        return DocumentStatus.draft;
      case 'approved':
      case 'valid':
        return DocumentStatus.validated;
      case 'revision':
      case 'needs_revision':
        return DocumentStatus.needsRevision;
      case 'rejected':
        return DocumentStatus.invalid;
      case 'pending-review':
      case 'pending_review':
        return DocumentStatus.pendingReview;
      default:
        return DocumentStatus.processing;
    }
  }

  factory FacultyDocument.fromApi(Map<String, dynamic> json) {
    final extractedRaw = json['extractedInfo'];
    final extracted = <String, String>{};
    if (extractedRaw is Map) {
      extractedRaw.forEach((key, value) {
        extracted['$key'] = '$value';
      });
    }
    final kraId = json['kraId'] as String?;
    final statusRaw = json['status'] as String?;
    final submitted = json['submittedAt'] as String? ?? json['uploadedAt'] as String?;
    DateTime submittedAt = DateTime.now();
    if (submitted != null && submitted.isNotEmpty) {
      submittedAt = DateTime.tryParse(submitted) ?? submittedAt;
    }
    final webStatus = statusFromWeb(statusRaw);
    return FacultyDocument(
      id: (json['id'] as String?) ?? '',
      title: (json['title'] as String?) ?? (json['name'] as String?) ?? 'Document',
      category: DocumentCategory.supportingEvidence,
      kra: kraFromWebId(kraId),
      submittedAt: submittedAt,
      status: webStatus,
      points: (json['verifiedPoints'] as num?)?.toInt() ?? 0,
      fileName: (json['fileName'] as String?) ?? '',
      extractedInfo: extracted,
      reviewerFeedback: json['feedback'] as String? ?? json['remarks'] as String?,
      indicatorId: json['indicatorId'] as String?,
      criterionId: json['criterionId'] as String?,
      mimeType: json['mimeType'] as String?,
      fileSize: json['fileSize'] as int?,
      hasFile: json['hasFile'] == true,
      fileUrl: json['fileApiPath'] as String? ?? json['fileUrl'] as String?,
      canDelete: webStatus == DocumentStatus.draft,
      canReplace: webStatus == DocumentStatus.needsRevision || webStatus == DocumentStatus.draft,
    );
  }
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.kind,
    required this.message,
    required this.createdAt,
    required this.visualState,
    this.relatedDocumentId,
    this.relatedKra,
  });

  final String id;
  final NotificationKind kind;
  final String message;
  final DateTime createdAt;
  final NotificationVisualState visualState;
  final String? relatedDocumentId;
  final KraType? relatedKra;

  String get title => kind.title;

  AppNotification copyWith({NotificationVisualState? visualState}) {
    return AppNotification(
      id: id,
      kind: kind,
      message: message,
      createdAt: createdAt,
      visualState: visualState ?? this.visualState,
      relatedDocumentId: relatedDocumentId,
      relatedKra: relatedKra,
    );
  }
}

class RequirementItem {
  const RequirementItem({
    required this.id,
    required this.title,
    required this.description,
    required this.kra,
    required this.status,
    this.hint,
  });

  final String id;
  final String title;
  final String description;
  final KraType kra;
  final RequirementStatus status;
  final String? hint;
}

class ImprovementArea {
  const ImprovementArea({
    required this.kra,
    required this.recommendedPoints,
    required this.guidance,
  });

  final KraType kra;
  final int recommendedPoints;
  final String guidance;
}

class RankSimulation {
  const RankSimulation({
    required this.currentRank,
    required this.targetRank,
    required this.currentPoints,
    required this.requiredPoints,
    required this.eligibilityLabel,
    required this.areasToImprove,
    this.kraConfigVersion = 0,
    this.scoringFormula =
        'Weighted Final Score = Σ (KRA points × Table 2.2 rank weight %)',
    this.weightBand = '',
    this.appliedWeights = const {},
    this.isPlaceholder = false,
  });

  final String currentRank;
  final String targetRank;
  final int currentPoints;
  final int requiredPoints;
  final String eligibilityLabel;
  final List<ImprovementArea> areasToImprove;
  final int kraConfigVersion;
  final String scoringFormula;
  final String weightBand;
  final Map<String, num> appliedWeights;
  final bool isPlaceholder;

  double get progress =>
      requiredPoints == 0 ? 0 : (currentPoints / requiredPoints).clamp(0, 1);

  int get remainingPoints =>
      (requiredPoints - currentPoints).clamp(0, requiredPoints);
}

class RecentActivity {
  const RecentActivity({
    required this.title,
    required this.subtitle,
    required this.timeLabel,
    required this.status,
  });

  final String title;
  final String subtitle;
  final String timeLabel;
  final DocumentStatus status;
}

class ReviewerFeedbackPreview {
  const ReviewerFeedbackPreview({
    required this.documentTitle,
    required this.message,
    required this.timeLabel,
  });

  final String documentTitle;
  final String message;
  final String timeLabel;
}

class PreparationPeriod {
  const PreparationPeriod({
    required this.cycleName,
    required this.startDate,
    required this.endDate,
    required this.reviewerAvailableUntil,
    required this.status,
    this.isPlaceholder = false,
  });

  final String cycleName;
  final DateTime startDate;
  final DateTime endDate;
  final DateTime reviewerAvailableUntil;
  final PreparationPeriodStatus status;
  final bool isPlaceholder;
}

class DashboardSnapshot {
  const DashboardSnapshot({
    required this.totalPoints,
    required this.targetPoints,
    required this.documentCompletionPercent,
    required this.validatedCount,
    required this.pendingCount,
    required this.actionRequiredCount,
    required this.kraScores,
    required this.recentActivity,
    required this.recentFeedback,
    required this.simulation,
    this.isPlaceholder = false,
  });

  final int totalPoints;
  final int targetPoints;
  final int documentCompletionPercent;
  final int validatedCount;
  final int pendingCount;
  final int actionRequiredCount;
  final List<KraScore> kraScores;
  final List<RecentActivity> recentActivity;
  final List<ReviewerFeedbackPreview> recentFeedback;
  final RankSimulation simulation;
  final bool isPlaceholder;

  double get overallProgress =>
      targetPoints == 0 ? 0 : (totalPoints / targetPoints).clamp(0, 1);
}
