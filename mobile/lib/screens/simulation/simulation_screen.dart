import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/rank_upgrade_simulation_card.dart';

class SimulationScreen extends StatefulWidget {
  const SimulationScreen({super.key});

  @override
  State<SimulationScreen> createState() => _SimulationScreenState();
}

class _SimulationScreenState extends State<SimulationScreen> {
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refresh());
  }

  Future<void> _refresh() async {
    final state = AppState.instance;
    if (!state.isSignedIn || state.usesMockAuth) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await state.refreshRankSimulationFromApi();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final sim = state.simulation;
        final kraScores = state.kraScores;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Rank simulation'),
            actions: [
              IconButton(
                onPressed: _loading ? null : _refresh,
                icon: _loading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.refresh_rounded),
                tooltip: 'Refresh simulation',
              ),
            ],
          ),
          body: RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                const InfoBanner(
                  message:
                      'Rank-upgrade simulation uses your uploaded evidence and published scoring rules. '
                      'It supports preparation only — not official DBM–CHED certification or board decisions.',
                  icon: Icons.privacy_tip_outlined,
                  color: AppColors.navy,
                  background: AppColors.goldSoft,
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: const TextStyle(color: AppColors.error, fontSize: 12),
                  ),
                ],
                const SizedBox(height: 16),
                RankUpgradeSimulationCard(simulation: sim),
                if (sim.missingRequirements.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  const SectionHeader(title: 'What you still need'),
                  ...sim.missingRequirements.map(
                    (item) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: const Icon(Icons.checklist_rtl_outlined, color: AppColors.navy),
                        title: Text(
                          (item['text'] as String?) ?? '',
                          style: const TextStyle(fontSize: 13, height: 1.35),
                        ),
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 18),
                const SectionHeader(title: 'KRA I–IV score breakdown'),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        for (final kra in kraScores) ...[
                          _KraBar(score: kra),
                          if (kra != kraScores.last) const SizedBox(height: 14),
                        ],
                      ],
                    ),
                  ),
                ),
                if (state.criterionA != null) ...[
                  const SizedBox(height: 18),
                  _CriterionAOverview(data: state.criterionA!),
                ],
                if (sim.areasToImprove.isNotEmpty) ...[
                  const SizedBox(height: 18),
                  const SectionHeader(title: 'Improvement opportunities'),
                  for (final area in sim.areasToImprove)
                    Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppColors.kraSoft(area.kra),
                          child: Icon(area.kra.icon, color: AppColors.kra(area.kra)),
                        ),
                        title: Text(
                          '${area.kra.shortLabel}: up to +${area.recommendedPoints} pts',
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                        ),
                        subtitle: Text(area.guidance),
                      ),
                    ),
                ],
                const SizedBox(height: 8),
                PrimaryButton(
                  label: 'View improvement opportunities',
                  icon: Icons.auto_awesome_outlined,
                  onPressed: () {
                    Navigator.pushNamed(context, AppRoutes.improvementOpportunities);
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _KraBar extends StatelessWidget {
  const _KraBar({required this.score});

  final KraScore score;

  @override
  Widget build(BuildContext context) {
    final color = AppColors.kra(score.type);
    final notAssessed = !score.assessed ||
        (score.statusLabel.toLowerCase().contains('not yet assessed'));

    if (notAssessed) {
      return Row(
        children: [
          Icon(score.type.icon, size: 18, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  score.type.label,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Not yet assessed',
                  style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ],
      );
    }

    final validated = score.validatedPoints;
    final provisional = score.provisionalPoints;
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
              style: TextStyle(fontWeight: FontWeight.w800, color: color),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          score.statusLabel,
          style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
        ),
        if (validated != null || provisional != null)
          Text(
            'Validated: ${validated?.toStringAsFixed(1) ?? '—'} · Projected: ${provisional?.toStringAsFixed(1) ?? '—'}',
            style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
          ),
        if (remaining > 0)
          Text(
            '$remaining possible ${remaining == 1 ? 'point' : 'points'} remaining in this KRA',
            style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
          ),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: score.progress,
          minHeight: 6,
          borderRadius: BorderRadius.circular(4),
          backgroundColor: color.withValues(alpha: 0.12),
          color: color,
        ),
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
    final total = data['combinedProvisionalPoints'] ?? data['criterionPoints'];
    final validated = data['combinedValidatedPoints'];

    String block(String title, Map<String, dynamic> block) {
      final cov = block['coverageSummary'] as Map<String, dynamic>? ?? {};
      final filled = cov['includedPeriods'] ?? block['filledCount'] ?? 0;
      final required = cov['requiredPeriods'] ?? block['requiredSemesters'] ?? '—';
      final prov = block['provisionalPoints'] ?? block['points'];
      final val = block['validatedPoints'];
      return '$title · periods $filled/$required'
          '${prov != null ? ' · projected $prov' : ''}'
          '${val != null ? ' · validated $val' : ''}';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Teaching effectiveness detail (SET + SEF)',
              style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
            ),
            const SizedBox(height: 8),
            Text(block('SET', set), style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 4),
            Text(block('SEF', sef), style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 8),
            Text(
              'Criterion A combined — projected: ${total ?? '—'} · validated: ${validated ?? '—'}',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}
