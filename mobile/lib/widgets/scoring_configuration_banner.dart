import 'package:flutter/material.dart';

import '../data/app_state.dart';
import '../theme/app_colors.dart';

/// Shows applicable official scoring configuration version (informational).
class ScoringConfigurationBanner extends StatelessWidget {
  const ScoringConfigurationBanner({super.key, this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppState.instance,
      builder: (context, _) {
        final state = AppState.instance;
        if (state.usesMockAuth) return const SizedBox.shrink();

        if (state.scoringConfigurationLoading) {
          return const Padding(
            padding: EdgeInsets.only(bottom: 12),
            child: LinearProgressIndicator(minHeight: 2),
          );
        }

        if (state.scoringConfigurationError != null) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Material(
              color: AppColors.warningSoft,
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  'Official scoring configuration could not be loaded. '
                  'Point previews may be unavailable until you retry.',
                  style: TextStyle(color: AppColors.warning, fontSize: compact ? 12 : 13),
                ),
              ),
            ),
          );
        }

        final cfg = state.scoringConfiguration;
        if (cfg == null) return const SizedBox.shrink();

        if (!cfg.hasApplicableConfiguration) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Material(
              color: AppColors.warningSoft,
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  cfg.message ?? 'No applicable official scoring configuration.',
                  style: TextStyle(color: AppColors.warning, fontSize: compact ? 12 : 13),
                ),
              ),
            ),
          );
        }

        final meta = cfg.metadata;
        final guideline = cfg.configuration?.guidelineLabel ?? meta.guidelineLabel;
        final parts = <String>[
          'Scoring config v${meta.versionLabel}',
          if (meta.effectiveFrom != null) 'effective ${meta.effectiveFrom}',
        ];
        if (guideline != null && guideline.isNotEmpty && !compact) {
          parts.add(guideline);
        }

        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text(
            parts.join(' · '),
            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.35),
          ),
        );
      },
    );
  }
}
