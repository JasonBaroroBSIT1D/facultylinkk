import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/progress_ring.dart';
import '../../widgets/simulation_result_card.dart';

class SimulationScreen extends StatelessWidget {
  const SimulationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final sim = state.simulation;
        final kraScores = state.kraScores;

        return Scaffold(
          appBar: AppBar(title: const Text('Rank simulation')),
          body: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              const InfoBanner(
                message:
                    'This preview helps you see a possible rank path and point standing. It is for preparation only and does not replace the official DBM–CHED evaluation.',
                icon: Icons.privacy_tip_outlined,
                color: AppColors.navy,
                background: AppColors.goldSoft,
              ),
              if (sim.weightBand.isNotEmpty || sim.kraConfigVersion > 0) ...[
                const SizedBox(height: 10),
                Text(
                  [
                    if (sim.weightBand.isNotEmpty)
                      'Table 2.2 weight band: ${sim.weightBand}.',
                    if (sim.kraConfigVersion > 0)
                      'KRA config v${sim.kraConfigVersion}.',
                    sim.scoringFormula,
                  ].join(' '),
                  style: const TextStyle(
                    fontSize: 12,
                    height: 1.35,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
              const SizedBox(height: 16),
              SimulationResultCard(
                simulation: sim,
                play: state.mainTabIndex == 2,
              ),
              if (state.criterionA != null) ...[
                const SizedBox(height: 18),
                _CriterionAOverview(data: state.criterionA!),
              ],
              const SizedBox(height: 18),
              const SectionHeader(title: 'Ranking and possible points'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _ScoreCompareRow(
                    earned: sim.currentPoints,
                    possible: sim.requiredPoints,
                  ),
                  const SizedBox(height: 16),
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Points by Key Result Area',
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        fontSize: 13,
                        color: AppColors.navy,
                      ),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Earned points compared with the possible points in this preparation preview.',
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.35,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  for (final kra in kraScores) ...[
                    _KraBar(score: kra),
                    if (kra != kraScores.last) const SizedBox(height: 14),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),
          const SectionHeader(title: 'Where extra points can still be earned'),
          for (final area in sim.areasToImprove)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: AppColors.kraSoft(area.kra),
                  child: Icon(area.kra.icon, color: AppColors.kra(area.kra)),
                ),
                title: Text(
                  '${area.kra.shortLabel}: +${area.recommendedPoints} possible points',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                ),
                subtitle: Text(area.guidance),
              ),
            ),
          const SizedBox(height: 8),
          PrimaryButton(
            label: 'View Improvement Opportunities',
            icon: Icons.auto_awesome_outlined,
            onPressed: () {
              Navigator.pushNamed(context, AppRoutes.improvementOpportunities);
            },
          ),
        ],
          ),
        );
      },
    );
  }
}

class _ScoreCompareRow extends StatelessWidget {
  const _ScoreCompareRow({required this.earned, required this.possible});

  final int earned;
  final int possible;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _PointStat(
            value: '$earned',
            label: 'Earned points',
            color: AppColors.navy,
            background: AppColors.navy.withValues(alpha: 0.06),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _PointStat(
            value: '$possible',
            label: 'Possible points',
            color: AppColors.gold,
            foreground: AppColors.navyDark,
            background: AppColors.goldSoft,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _PointStat(
            value: '${(possible - earned).clamp(0, possible)}',
            label: 'Still needed',
            color: AppColors.warning,
            background: AppColors.warningSoft,
          ),
        ),
      ],
    );
  }
}

class _PointStat extends StatelessWidget {
  const _PointStat({
    required this.value,
    required this.label,
    required this.color,
    required this.background,
    this.foreground,
  });

  final String value;
  final String label;
  final Color color;
  final Color background;
  final Color? foreground;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: foreground ?? color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 11,
              height: 1.2,
              fontWeight: FontWeight.w600,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _KraBar extends StatelessWidget {
  const _KraBar({required this.score});

  final KraScore score;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.kra(score.type);
    final remaining = (score.targetPoints - score.currentPoints).clamp(0, score.targetPoints);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(score.type.icon, size: 18, color: color),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                score.type.label,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
              ),
            ),
            Text(
              '${score.currentPoints} / ${score.targetPoints}',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          remaining == 0
              ? 'Possible points in this KRA are filled in this preview.'
              : '$remaining more possible ${remaining == 1 ? 'point' : 'points'} in this KRA',
          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 6),
        LinearProgressLabeled(progress: score.progress, color: color),
      ],
    );
  }
}

class _CriterionAOverview extends StatelessWidget {
  const _CriterionAOverview({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final set = data['set'] as Map<String, dynamic>? ?? {};
    final sef = data['sef'] as Map<String, dynamic>? ?? {};
    final total = data['criterionPoints'];
    final max = data['criterionMax'] ?? 60;
    String block(String title, Map<String, dynamic> block) {
      final filled = block['filledCount'] ?? 0;
      final required = block['requiredSemesters'] ?? 6;
      final avg = block['averageRating'];
      final pts = block['points'];
      final maxPts = block['maxPoints'];
      return '$title · coverage $filled/$required'
          '${avg != null ? ' · avg $avg' : ''}'
          '${pts != null && (block['finalized'] == true) ? ' · ${pts.toString()} / $maxPts pts' : ''}';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'KRA I — Criterion A (Teaching Effectiveness)',
              style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
            ),
            const SizedBox(height: 8),
            Text(block('SET (60%)', set), style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 4),
            Text(block('SEF (40%)', sef), style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 8),
            Text(
              'Combined: ${total ?? '—'} / $max (rank simulation; not official approval)',
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}

class ImprovementOpportunitiesScreen extends StatelessWidget {
  const ImprovementOpportunitiesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final sim = AppState.instance.simulation;
    return Scaffold(
      appBar: AppBar(title: const Text('Improvement opportunities')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const InfoBanner(
            message:
                'These suggestions are based on mock gaps in your current self-assessment preview.',
          ),
          const SizedBox(height: 16),
          for (final area in sim.areasToImprove)
            Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      area.kra.label,
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        color: AppColors.kra(area.kra),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Possible additional points: +${area.recommendedPoints}',
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      area.guidance,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 12),
                    SecondaryButton(
                      label: 'Upload evidence',
                      icon: Icons.upload_file_outlined,
                      onPressed: () {
                        Navigator.pushNamed(
                          context,
                          AppRoutes.uploadDocument,
                          arguments: area.kra,
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
