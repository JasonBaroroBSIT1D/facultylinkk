import '../models/enums.dart';
import '../models/models.dart';
import 'simulation_display_rules.dart';

enum SimulationScoreMode { estimated, verified }

extension SimulationScoreModeLabel on SimulationScoreMode {
  String get shortLabel =>
      this == SimulationScoreMode.estimated ? 'Estimated' : 'Reviewer-Verified';
}

class KraTileModel {
  const KraTileModel({
    required this.type,
    required this.title,
    required this.weightPercent,
    required this.state,
    this.weightedContribution,
    this.rawScore,
    this.maxPoints,
  });

  final KraType type;
  final String title;
  final int? weightPercent;
  final KraScoreDisplayState state;
  final double? weightedContribution;
  final double? rawScore;
  final double? maxPoints;
}

enum KraScoreDisplayState {
  notAssessed,
  scored,
  awaitingVerification,
  notApplicable,
}

class SimulationViewModel {
  SimulationViewModel({
    required this.simulation,
    required this.kraScores,
    required this.mode,
  });

  final RankSimulation simulation;
  final List<KraScore> kraScores;
  final SimulationScoreMode mode;

  bool get isEstimated => mode == SimulationScoreMode.estimated;

  List<Map<String, dynamic>> get _breakdownRows => isEstimated
      ? simulation.weightedContributionBreakdownEstimated
      : simulation.weightedContributionBreakdownVerified;

  Map<String, double> get _contributions => isEstimated
      ? simulation.estimatedWeightedContributions
      : simulation.verifiedWeightedContributions;

  double? get weightedTotal => isEstimated
      ? simulation.weightedEstimatedScore
      : simulation.weightedValidatedScore;

  bool get hasAnyVerifiedWeightedData {
    if (simulation.weightedValidatedScore != null) return true;
    for (final row in simulation.weightedContributionBreakdownVerified) {
      if (row['weightedContribution'] != null) return true;
    }
    return false;
  }

  bool get verifiedModeBlocked => !isEstimated && !hasAnyVerifiedWeightedData;

  int get subrankIncrement {
    if (isEstimated) return simulation.subrankIncrement ?? 0;
    return SimulationDisplayRules.subrankIncrementForScore(weightedTotal);
  }

  String? get possibleRankLabel {
    if (verifiedModeBlocked) return null;
    if (isEstimated) {
      final p = simulation.displayPossibleRank;
      if (p == '—') return null;
      return p;
    }
    return SimulationDisplayRules.possibleRankAfterIncrement(
      simulation.currentRank,
      subrankIncrement,
    );
  }

  bool get qualifiesForHigherRank {
    if (verifiedModeBlocked) return false;
    if (subrankIncrement <= 0) return false;
    final possible = possibleRankLabel?.trim() ?? '';
    if (possible.isEmpty || possible == '—') return false;
    return possible.toLowerCase() != simulation.currentRank.trim().toLowerCase();
  }

  bool get hasEssentialGaps => simulation.missingRequirements.any(
        (item) =>
            (item['category'] as String?) != 'configuration' &&
            (item['category'] as String?) != 'profile',
      );

  String get rankHeadlineExplanation {
    if (simulation.isPlaceholder) {
      return simulation.eligibilityLabel;
    }
    if (verifiedModeBlocked) {
      return 'Your documents are waiting for reviewer verification. '
          'Switch to Estimated to preview your self-assessment scores.';
    }
    if (!qualifiesForHigherRank) {
      return 'Not yet qualified for a higher rank.';
    }
    if (hasEssentialGaps) {
      return 'Your score suggests progress, but some preparation items are still incomplete.';
    }
    return 'Nice work! Your ${mode.shortLabel.toLowerCase()} scores support a possible move to $possibleRankLabel.';
  }

  String get possibleRankDisplay {
    if (verifiedModeBlocked) return 'Waiting for review';
    if (!qualifiesForHigherRank) return simulation.currentRank;
    return possibleRankLabel ?? simulation.currentRank;
  }

  (int completed, int total)? get readinessCounts {
    final applicable = simulation.readinessChecklist
        .where((e) => e['applicable'] == true)
        .toList();
    if (applicable.isEmpty) return null;
    final done = applicable.where((e) => e['completed'] == true).length;
    return (done, applicable.length);
  }

  List<KraTileModel> get kraTiles {
    const order = [
      ('kra1', KraType.instruction, 'Instruction'),
      ('kra2', KraType.research, 'Research'),
      ('kra3', KraType.extension, 'Extension'),
      ('kra4', KraType.professionalDevelopment, 'Prof. Development'),
    ];
    return order.map((entry) {
      final kraId = entry.$1;
      final type = entry.$2;
      final title = entry.$3;
      final kraScore = kraScores.where((k) => k.type == type).cast<KraScore?>().firstOrNull;
      final assessed = kraScore?.assessed ?? false;
      final row = _breakdownRows.cast<Map<String, dynamic>?>().firstWhere(
            (r) => r?['kraId'] == kraId,
            orElse: () => null,
          );
      final raw = _asDouble(row?['rawScore']) ?? _asDouble(kraScore?.estimatedPoints);
      final max = _asDouble(row?['maxPoints']) ?? _asDouble(kraScore?.targetPoints);
      final weight = simulation.appliedWeights[kraId]?.round();
      final contrib = _contributions[kraId] ?? _asDouble(row?['weightedContribution']);

      KraScoreDisplayState state;
      if (!assessed) {
        state = KraScoreDisplayState.notAssessed;
      } else if (!isEstimated && contrib == null && raw == null) {
        state = KraScoreDisplayState.awaitingVerification;
      } else if (contrib != null || (isEstimated && raw != null)) {
        state = KraScoreDisplayState.scored;
      } else {
        state = KraScoreDisplayState.notAssessed;
      }

      return KraTileModel(
        type: type,
        title: title,
        weightPercent: weight,
        state: state,
        weightedContribution: contrib,
        rawScore: raw,
        maxPoints: max,
      );
    }).toList();
  }

  static double? _asDouble(Object? value) {
    if (value is num) return value.toDouble();
    return null;
  }
}

extension _FirstOrNull<E> on Iterable<E> {
  E? get firstOrNull {
    final it = iterator;
    if (!it.moveNext()) return null;
    return it.current;
  }
}
