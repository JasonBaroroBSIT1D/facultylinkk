import '../models/enums.dart';
import '../models/models.dart';

/// Empty live-session placeholders (not demo data).
abstract final class FacultySessionDefaults {
  static const faculty = FacultyProfile(
    fullName: '',
    facultyId: '',
    email: '',
    department: '',
    college: '',
    currentRank: '',
    targetRank: '',
    highestDegree: '',
    specialization: '',
    yearsInService: 0,
    employmentStatus: '',
    campus: '',
    phone: '',
  );

  static RankSimulation unavailableSimulation({
    String currentRank = '',
    String targetRank = '',
  }) =>
      RankSimulation(
        currentRank: currentRank.isNotEmpty ? currentRank : 'Not provided',
        targetRank: targetRank.isNotEmpty ? targetRank : 'Not provided',
        currentPoints: 0,
        requiredPoints: 0,
        eligibilityLabel:
            'No simulation available yet. Complete your KRA self-assessment to generate an estimate.',
        areasToImprove: const [],
        isPlaceholder: true,
      );

  static final preparationPeriod = PreparationPeriod(
    cycleName: '',
    startDate: DateTime(1970, 1, 1),
    endDate: DateTime(1970, 1, 1),
    reviewerAvailableUntil: DateTime(1970, 1, 1),
    status: PreparationPeriodStatus.closed,
    isPlaceholder: true,
  );

  static final dashboard = DashboardSnapshot(
    totalPoints: 0,
    targetPoints: 100,
    documentCompletionPercent: 0,
    validatedCount: 0,
    pendingCount: 0,
    actionRequiredCount: 0,
    kraScores: kraScoresEmpty,
    recentActivity: const [],
    recentFeedback: const [],
    simulation: unavailableSimulation(),
    isPlaceholder: true,
  );

  static const kraScoresEmpty = [
    KraScore(
      type: KraType.instruction,
      currentPoints: 0,
      targetPoints: 0,
      documentCount: 0,
      statusLabel: 'Not yet calculated',
      breakdown: [],
    ),
    KraScore(
      type: KraType.research,
      currentPoints: 0,
      targetPoints: 0,
      documentCount: 0,
      statusLabel: 'Not yet calculated',
      breakdown: [],
    ),
    KraScore(
      type: KraType.extension,
      currentPoints: 0,
      targetPoints: 0,
      documentCount: 0,
      statusLabel: 'Not yet calculated',
      breakdown: [],
    ),
    KraScore(
      type: KraType.professionalDevelopment,
      currentPoints: 0,
      targetPoints: 0,
      documentCount: 0,
      statusLabel: 'Not yet calculated',
      breakdown: [],
    ),
  ];
}
