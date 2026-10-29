import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';
import 'progress_ring.dart';

/// Primary rank-upgrade simulation summary (live API data only).
class RankUpgradeSimulationCard extends StatelessWidget {
  const RankUpgradeSimulationCard({
    super.key,
    required this.simulation,
  });

  final RankSimulation simulation;

  @override
  Widget build(BuildContext context) {
    if (simulation.isPlaceholder) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Text(
            simulation.eligibilityLabel,
            style: const TextStyle(
              fontSize: 13,
              height: 1.45,
              color: AppColors.textSecondary,
            ),
          ),
        ),
      );
    }

    final target = simulation.targetRank.trim().isEmpty
        ? 'Pathway under assessment'
        : simulation.targetRank;
    final progress = simulation.progressPercent;
    final showProgress = progress != null && simulation.requiredPoints > 0;

    return Card(
      elevation: 0,
      color: AppColors.navy,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Faculty Rank Upgrade Simulation',
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.92),
                fontWeight: FontWeight.w700,
                fontSize: 13,
                letterSpacing: 0.3,
              ),
            ),
            const SizedBox(height: 12),
            _EligibilityChip(label: simulation.eligibilityBadgeLabel),
            const SizedBox(height: 16),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: _RankColumn(
                    caption: 'Current faculty rank',
                    value: simulation.currentRank,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 22),
                  child: Icon(
                    Icons.arrow_downward_rounded,
                    color: AppColors.forestLight.withValues(alpha: 0.95),
                    size: 22,
                  ),
                ),
                Expanded(
                  child: _RankColumn(
                    caption: 'Possible rank upgrade',
                    value: target,
                    alignEnd: true,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 18),
            Divider(color: Colors.white.withValues(alpha: 0.15), height: 1),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _Metric(
                    label: 'Teaching effectiveness',
                    value: _fmt(simulation.teachingEffectivenessScore),
                  ),
                ),
                Expanded(
                  child: _Metric(
                    label: 'Validated KRA pts',
                    value: _fmt(simulation.validatedKraPoints),
                  ),
                ),
                Expanded(
                  child: _Metric(
                    label: 'Projected KRA pts',
                    value: _fmt(simulation.provisionalKraPoints),
                  ),
                ),
              ],
            ),
            if (simulation.weightedProvisionalScore != null ||
                simulation.weightedValidatedScore != null) ...[
              const SizedBox(height: 12),
              Text(
                'Weighted score (Table 2.2${simulation.weightBand.isNotEmpty ? ': ${simulation.weightBand}' : ''}): '
                '${_fmt(simulation.weightedValidatedScore ?? simulation.weightedProvisionalScore)} / 100',
                style: TextStyle(
                  color: AppColors.mint.withValues(alpha: 0.9),
                  fontSize: 11,
                  height: 1.35,
                ),
              ),
            ],
            const SizedBox(height: 16),
            if (showProgress) ...[
              Row(
                children: [
                  ProgressRing(
                    progress: (progress / 100).clamp(0, 1),
                    size: 52,
                    strokeWidth: 6,
                    color: AppColors.forestLight,
                    backgroundColor: Colors.white.withValues(alpha: 0.12),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${progress.toStringAsFixed(1)}% toward configured threshold',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          simulation.progressLabel,
                          style: TextStyle(
                            color: AppColors.mint.withValues(alpha: 0.88),
                            fontSize: 11,
                            height: 1.35,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ] else
              Text(
                simulation.progressLabel.isNotEmpty
                    ? simulation.progressLabel
                    : 'Assessment incomplete — configure rank thresholds or upload evidence.',
                style: TextStyle(
                  color: AppColors.mint.withValues(alpha: 0.88),
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            const SizedBox(height: 10),
            Text(
              simulation.eligibilityLabel,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.78),
                fontSize: 11,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  static String _fmt(num? v) {
    if (v == null) return '—';
    if (v == v.roundToDouble()) return v.round().toString();
    return v.toStringAsFixed(1);
  }
}

class _EligibilityChip extends StatelessWidget {
  const _EligibilityChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.forestLight.withValues(alpha: 0.22),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.forestLight.withValues(alpha: 0.45)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
          fontSize: 11,
        ),
      ),
    );
  }
}

class _RankColumn extends StatelessWidget {
  const _RankColumn({
    required this.caption,
    required this.value,
    this.alignEnd = false,
  });

  final String caption;
  final String value;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Text(
          caption,
          style: TextStyle(
            color: AppColors.mint.withValues(alpha: 0.85),
            fontSize: 10,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 15,
            height: 1.25,
          ),
        ),
      ],
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 16,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.mint.withValues(alpha: 0.85),
            fontSize: 10,
            height: 1.2,
          ),
        ),
      ],
    );
  }
}
