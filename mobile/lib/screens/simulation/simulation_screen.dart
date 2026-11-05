import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../navigation/app_routes.dart';
import '../../simulation/simulation_friendly_requirements.dart';
import '../../simulation/simulation_view_model.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/simulation/simulation_ui_sections.dart';

class SimulationScreen extends StatefulWidget {
  const SimulationScreen({super.key});

  @override
  State<SimulationScreen> createState() => _SimulationScreenState();
}

class _SimulationScreenState extends State<SimulationScreen> {
  bool _loading = false;
  String? _error;
  SimulationScoreMode _mode = SimulationScoreMode.estimated;

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
      await state.refreshScoringConfiguration(force: true, quiet: true);
      await state.refreshRankSimulationFromApi();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _runRequirementAction(SimulationRequirementAction action) {
    final state = AppState.instance;
    switch (action) {
      case SimulationRequirementAction.documents:
        state.openDocuments();
        break;
      case SimulationRequirementAction.assessment:
        state.openAssessment(innerTab: 0);
        Navigator.pushNamed(context, AppRoutes.assessment);
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final sim = state.simulation;
        final viewModel = SimulationViewModel(
          simulation: sim,
          kraScores: state.kraScores,
          mode: _mode,
        );
        final needs = SimulationFriendlyRequirements.fromSimulation(sim, state);

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Rank upgrade'),
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
                tooltip: 'Refresh',
              ),
            ],
          ),
          body: RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Text(_error!, style: const TextStyle(color: AppColors.error, fontSize: 12)),
                  ),
                SimulationRankProgressCard(viewModel: viewModel),
                const SizedBox(height: 16),
                SimulationScoreModeToggle(
                  mode: _mode,
                  onChanged: (m) => setState(() => _mode = m),
                ),
                const SizedBox(height: 14),
                SimulationKraScoreGrid(viewModel: viewModel),
                const SizedBox(height: 16),
                SimulationReadinessCard(viewModel: viewModel),
                const SizedBox(height: 16),
                const Text(
                  'What you still need',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    color: AppColors.navy,
                  ),
                ),
                const SizedBox(height: 8),
                SimulationNeedsChecklist(
                  items: needs,
                  onAction: _runRequirementAction,
                ),
                const SizedBox(height: 12),
                PrimaryButton(
                  label: needs.isEmpty ? 'Review my documents' : 'Continue preparing',
                  icon: Icons.folder_open_outlined,
                  onPressed: () => state.openDocuments(),
                ),
                const SizedBox(height: 16),
                SimulationTechnicalDetails(viewModel: viewModel),
                const SizedBox(height: 12),
                Text(
                  sim.disclaimer.isNotEmpty
                      ? sim.disclaimer
                      : 'This preview helps you prepare. It is not an official promotion decision.',
                  style: const TextStyle(fontSize: 11, height: 1.4, color: AppColors.textTertiary),
                ),
              ],
            ),
          ),
        );
      },
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
