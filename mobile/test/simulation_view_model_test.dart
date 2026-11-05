import 'package:facultylink_app/models/models.dart';
import 'package:facultylink_app/simulation/simulation_view_model.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('does not qualify when subrank increment is zero', () {
    const sim = RankSimulation(
      currentRank: 'Instructor I',
      targetRank: 'Instructor I',
      possibleRank: 'Instructor I',
      currentPoints: 10,
      requiredPoints: 100,
      eligibilityLabel: 'Under assessment',
      areasToImprove: [],
      subrankIncrement: 0,
      weightedEstimatedScore: 25,
      estimatedWeightedContributions: {'kra1': 25},
    );
    final vm = SimulationViewModel(
      simulation: sim,
      kraScores: const [],
      mode: SimulationScoreMode.estimated,
    );
    expect(vm.qualifiesForHigherRank, isFalse);
    expect(vm.rankHeadlineExplanation, contains('Not yet qualified'));
  });
}
