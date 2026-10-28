import '../models/enums.dart';
import '../models/models.dart';
import 'faculty_session_defaults.dart';

abstract final class FacultyApiMapper {
  static DashboardSnapshot dashboardFromApi(
    Map<String, dynamic> json,
    FacultyProfile profile,
  ) {
    final kraRaw = json['kraScores'];
    final kraScores = kraRaw is List
        ? kraRaw
            .whereType<Map>()
            .map((e) => KraScore.fromApi(Map<String, dynamic>.from(e)))
            .toList()
        : List<KraScore>.from(FacultySessionDefaults.kraScoresEmpty);

    final simRaw = json['simulation'];
    final RankSimulation simulation;
    if (simRaw is Map<String, dynamic>) {
      simulation = simulationFromApi(simRaw);
    } else {
      simulation = FacultySessionDefaults.unavailableSimulation(
        currentRank: profile.currentRank,
        targetRank: profile.targetRank,
      );
    }

    final recentActivity = <RecentActivity>[];
    final activityRaw = json['recentActivity'];
    if (activityRaw is List) {
      for (final row in activityRaw.whereType<Map>()) {
        recentActivity.add(recentActivityFromApi(Map<String, dynamic>.from(row)));
      }
    }

    final recentFeedback = <ReviewerFeedbackPreview>[];
    final feedbackRaw = json['recentFeedback'];
    if (feedbackRaw is List) {
      for (final row in feedbackRaw.whereType<Map>()) {
        recentFeedback.add(reviewerFeedbackFromApi(Map<String, dynamic>.from(row)));
      }
    }

    return DashboardSnapshot(
      totalPoints: (json['totalPoints'] as num?)?.toInt() ?? 0,
      targetPoints: (json['targetPoints'] as num?)?.toInt() ?? 100,
      documentCompletionPercent: (json['documentCompletionPercent'] as num?)?.toInt() ?? 0,
      validatedCount: (json['validatedCount'] as num?)?.toInt() ?? 0,
      pendingCount: (json['pendingCount'] as num?)?.toInt() ?? 0,
      actionRequiredCount: (json['actionRequiredCount'] as num?)?.toInt() ?? 0,
      kraScores: kraScores,
      recentActivity: recentActivity,
      recentFeedback: recentFeedback,
      simulation: simulation,
    );
  }

  static RankSimulation simulationFromApi(Map<String, dynamic> json) {
    return RankSimulation(
      currentRank: (json['currentRank'] as String?) ?? '',
      targetRank: (json['targetRank'] as String?) ?? '',
      currentPoints: (json['currentPoints'] as num?)?.toInt() ?? 0,
      requiredPoints: (json['requiredPoints'] as num?)?.toInt() ?? 0,
      eligibilityLabel: (json['eligibilityLabel'] as String?) ?? 'Simulation snapshot',
      areasToImprove: const [],
    );
  }

  static PreparationPeriod? preparationPeriodFromApi(Map<String, dynamic>? json) {
    if (json == null) return null;
    final start = _parseDate(json['startDate']);
    final end = _parseDate(json['endDate']);
    if (start == null || end == null) return null;
    final until = _parseDate(json['reviewerAvailableUntil']) ?? end;
    return PreparationPeriod(
      cycleName: (json['cycleName'] as String?) ?? '',
      startDate: start,
      endDate: end,
      reviewerAvailableUntil: until,
      status: _prepStatus(json['status'] as String?),
    );
  }

  static RecentActivity recentActivityFromApi(Map<String, dynamic> json) {
    return RecentActivity(
      title: (json['title'] as String?) ?? 'Document',
      subtitle: (json['subtitle'] as String?) ?? '',
      timeLabel: _relativeTime(json['submittedAt'] as String?),
      status: FacultyDocument.statusFromWeb(json['status'] as String?),
    );
  }

  static ReviewerFeedbackPreview reviewerFeedbackFromApi(Map<String, dynamic> json) {
    return ReviewerFeedbackPreview(
      documentTitle: (json['documentTitle'] as String?) ?? 'Document',
      message: (json['message'] as String?) ?? '',
      timeLabel: _relativeTime(json['reviewedAt'] as String?),
    );
  }

  static PreparationPeriodStatus _prepStatus(String? raw) {
    switch (raw) {
      case 'closing_soon':
        return PreparationPeriodStatus.closingSoon;
      case 'closed':
        return PreparationPeriodStatus.closed;
      default:
        return PreparationPeriodStatus.open;
    }
  }

  static DateTime? _parseDate(String? raw) {
    if (raw == null || raw.isEmpty) return null;
    return DateTime.tryParse(raw);
  }

  static String _relativeTime(String? iso) {
    if (iso == null || iso.isEmpty) return '';
    final parsed = DateTime.tryParse(iso);
    if (parsed == null) return '';
    final diff = DateTime.now().difference(parsed.toLocal());
    if (diff.inDays > 0) return '${diff.inDays}d ago';
    if (diff.inHours > 0) return '${diff.inHours}h ago';
    if (diff.inMinutes > 0) return '${diff.inMinutes}m ago';
    return 'Just now';
  }
}
