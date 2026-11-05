import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../simulation/simulation_friendly_requirements.dart';
import '../../simulation/simulation_view_model.dart';
import '../../theme/app_colors.dart';

class SimulationRankProgressCard extends StatelessWidget {
  const SimulationRankProgressCard({super.key, required this.viewModel});

  final SimulationViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    final sim = viewModel.simulation;
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: AppColors.forest.withValues(alpha: 0.35)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.emoji_events_outlined, color: AppColors.forest, size: 22),
                const SizedBox(width: 8),
                const Text(
                  'Your rank progress',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    color: AppColors.navy,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _RankBox(
                    label: 'Your current rank',
                    value: sim.currentRank,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 6),
                  child: Icon(
                    Icons.arrow_forward_rounded,
                    color: AppColors.forest.withValues(alpha: 0.9),
                    size: 20,
                  ),
                ),
                Expanded(
                  child: _RankBox(
                    label: 'Possible rank',
                    value: viewModel.possibleRankDisplay,
                    alignEnd: true,
                    highlight: viewModel.qualifiesForHigherRank,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.forest.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                viewModel.rankHeadlineExplanation,
                style: const TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  color: AppColors.navy,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RankBox extends StatelessWidget {
  const _RankBox({
    required this.label,
    required this.value,
    this.alignEnd = false,
    this.highlight = false,
  });

  final String label;
  final String value;
  final bool alignEnd;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            height: 1.2,
            color: highlight ? AppColors.forest : AppColors.navy,
          ),
        ),
      ],
    );
  }
}

class SimulationScoreModeToggle extends StatelessWidget {
  const SimulationScoreModeToggle({
    super.key,
    required this.mode,
    required this.onChanged,
  });

  final SimulationScoreMode mode;
  final ValueChanged<SimulationScoreMode> onChanged;

  @override
  Widget build(BuildContext context) {
    final narrow = MediaQuery.sizeOf(context).width < 360;
    return SegmentedButton<SimulationScoreMode>(
      segments: [
        const ButtonSegment(
          value: SimulationScoreMode.estimated,
          label: Text('Estimated', style: TextStyle(fontSize: 12)),
        ),
        ButtonSegment(
          value: SimulationScoreMode.verified,
          label: Text(
            narrow ? 'Verified' : 'Reviewer-Verified',
            style: const TextStyle(fontSize: 12),
          ),
        ),
      ],
      selected: {mode},
      onSelectionChanged: (set) => onChanged(set.first),
      style: ButtonStyle(
        visualDensity: VisualDensity.compact,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}

class SimulationKraScoreGrid extends StatelessWidget {
  const SimulationKraScoreGrid({super.key, required this.viewModel});

  final SimulationViewModel viewModel;

  static String _contribLabel(KraTileModel tile) {
    switch (tile.state) {
      case KraScoreDisplayState.notAssessed:
        return 'No score yet';
      case KraScoreDisplayState.awaitingVerification:
        return 'Awaiting review';
      case KraScoreDisplayState.notApplicable:
        return 'Not applicable';
      case KraScoreDisplayState.scored:
        final v = tile.weightedContribution;
        if (v == null) return 'Pending';
        return v.toStringAsFixed(2);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tiles = viewModel.kraTiles;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Your KRA points',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 16,
            color: AppColors.navy,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          viewModel.isEstimated
              ? 'Numbers below are weighted points (not raw scores).'
              : 'Reviewer-approved weighted points only.',
          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (context, constraints) {
            const spacing = 10.0;
            final width = (constraints.maxWidth - spacing) / 2;
            return Wrap(
              spacing: spacing,
              runSpacing: spacing,
              children: tiles
                  .map(
                    (tile) => SizedBox(
                      width: width,
                      child: _KraTile(
                        tile: tile,
                        valueLabel: _contribLabel(tile),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
        const SizedBox(height: 14),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: AppColors.navy,
            borderRadius: BorderRadius.circular(14),
          ),
          child: Row(
            children: [
              const Expanded(
                child: Text(
                  'Your Weighted Score',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
              ),
              Text(
                _totalLabel(viewModel),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                  fontSize: 20,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  static String _totalLabel(SimulationViewModel vm) {
    if (vm.verifiedModeBlocked) return 'Not available';
    final total = vm.weightedTotal;
    if (total == null) return 'Not scored yet';
    return '${total.toStringAsFixed(2)} / 100';
  }
}

class _KraTile extends StatelessWidget {
  const _KraTile({required this.tile, required this.valueLabel});

  final KraTileModel tile;
  final String valueLabel;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.kra(tile.type);
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(tile.type.icon, size: 18, color: color),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    tile.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                      color: AppColors.navy,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              valueLabel,
              style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 18,
                color: color,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              tile.weightPercent != null ? 'Weight ${tile.weightPercent}%' : 'Weight —',
              style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class SimulationReadinessCard extends StatelessWidget {
  const SimulationReadinessCard({super.key, required this.viewModel});

  final SimulationViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    final pct = viewModel.simulation.preparationReadinessPercentage;
    final counts = viewModel.readinessCounts;

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Preparation readiness',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 16,
                color: AppColors.navy,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'This counts finished preparation steps — not your promotion approval.',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.35),
            ),
            const SizedBox(height: 12),
            if (pct == null || counts == null) ...[
              const Text(
                'Not available',
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                viewModel.simulation.preparationReadinessLabel.isNotEmpty
                    ? viewModel.simulation.preparationReadinessLabel
                    : 'We could not build a preparation checklist yet.',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ] else ...[
              Text(
                '${pct.round()}% Ready',
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 22,
                  color: AppColors.forest,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${counts.$1} of ${counts.$2} preparation items completed',
                style: const TextStyle(fontSize: 13, color: AppColors.navy),
              ),
              const SizedBox(height: 10),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: (pct / 100).clamp(0, 1),
                  minHeight: 10,
                  backgroundColor: AppColors.forest.withValues(alpha: 0.12),
                  color: AppColors.forest,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class SimulationNeedsChecklist extends StatelessWidget {
  const SimulationNeedsChecklist({
    super.key,
    required this.items,
    required this.onAction,
  });

  final List<FriendlyRequirementItem> items;
  final void Function(SimulationRequirementAction action) onAction;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(Icons.check_circle, color: AppColors.forest),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  'You have no open preparation items right now. Keep your documents up to date!',
                  style: TextStyle(fontSize: 13, color: AppColors.navy.withValues(alpha: 0.85)),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      children: items
          .map(
            (item) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
                leading: Icon(
                  item.isComplete ? Icons.check_circle : Icons.circle_outlined,
                  color: item.isComplete ? AppColors.forest : AppColors.textTertiary,
                ),
                title: Text(
                  item.title,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                ),
                subtitle: Text(
                  item.subtitle,
                  style: const TextStyle(fontSize: 12, height: 1.35),
                ),
                trailing: item.isComplete || item.actionLabel == null
                    ? null
                    : TextButton(
                        onPressed: () => onAction(item.action),
                        child: Text(item.actionLabel!),
                      ),
              ),
            ),
          )
          .toList(),
    );
  }
}

class SimulationTechnicalDetails extends StatelessWidget {
  const SimulationTechnicalDetails({
    super.key,
    required this.viewModel,
  });

  final SimulationViewModel viewModel;

  @override
  Widget build(BuildContext context) {
    final sim = viewModel.simulation;
    final config = AppState.instance.scoringConfiguration;
    final header = config?.configuration;

    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text(
        'How was my score calculated?',
        style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
      ),
      children: [
        Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (sim.weightBand.isNotEmpty)
                  _line('Rank weight band', sim.weightBand),
                _line('Table 2.2 weights', _weightsText(sim)),
                if (sim.scoreBracket != null)
                  _line('Table 3.1 bracket (estimated)', sim.scoreBracket!),
                if (sim.subrankIncrement != null)
                  _line('Sub-rank increment (estimated)', '+${sim.subrankIncrement}'),
                _line('Configuration version', '${sim.kraConfigVersion}'),
                if (header?.publishedAt != null)
                  _line('Published', header!.publishedAt!),
                if (sim.calculationReference.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    sim.calculationReference,
                    style: const TextStyle(fontSize: 11, height: 1.4, color: AppColors.textSecondary),
                  ),
                ],
                const SizedBox(height: 12),
                const Text(
                  'KRA detail (selected view)',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                ),
                const SizedBox(height: 6),
                for (final tile in viewModel.kraTiles)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Text(
                      '${tile.title}: raw ${_fmt(tile.rawScore)} / max ${_fmt(tile.maxPoints)} '
                      '→ weighted ${_fmt(tile.weightedContribution)}',
                      style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                    ),
                  ),
                if (sim.disclaimer.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text(
                    sim.disclaimer,
                    style: const TextStyle(fontSize: 10, height: 1.35, color: AppColors.textTertiary),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  static String _weightsText(RankSimulation sim) {
    final w = sim.appliedWeights;
    if (w.isEmpty) return '—';
    return 'I ${w['kra1'] ?? '—'}%, II ${w['kra2'] ?? '—'}%, '
        'III ${w['kra3'] ?? '—'}%, IV ${w['kra4'] ?? '—'}%';
  }

  static String _fmt(double? v) => v == null ? '—' : v.toStringAsFixed(2);

  static Widget _line(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 150,
            child: Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
