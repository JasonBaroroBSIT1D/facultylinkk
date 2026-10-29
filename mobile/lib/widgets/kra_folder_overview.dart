import 'package:flutter/material.dart';

import '../models/enums.dart';
import '../models/models.dart';
import '../navigation/app_routes.dart';
import '../theme/app_colors.dart';
import 'compact_folder_card.dart';
import '../screens/documents/document_flow_args.dart';

/// KRA folder grid on My Documents — height follows content (no fixed aspect ratio).
class KraFolderOverview extends StatelessWidget {
  const KraFolderOverview({super.key, required this.documents});

  final List<FacultyDocument> documents;

  /// Two columns only when each column is wide enough for full KRA labels.
  static bool useTwoColumns(double maxWidth, TextScaler textScaler) {
    final scale = textScaler.scale(14) / 14;
    if (scale > 1.12) return false;
    const minColumnWidth = 168.0;
    const spacing = 8.0;
    return maxWidth >= (minColumnWidth * 2 + spacing + 32);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Browse by KRA',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            color: AppColors.navy,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Open a folder to view criteria, indicators, and evidence.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 10),
        LayoutBuilder(
          builder: (context, constraints) {
            const spacing = 8.0;
            final twoCol = useTwoColumns(
              constraints.maxWidth,
              MediaQuery.textScalerOf(context),
            );
            final itemWidth = twoCol
                ? (constraints.maxWidth - spacing) / 2
                : constraints.maxWidth;

            return Wrap(
              spacing: spacing,
              runSpacing: spacing,
              children: [
                for (final kra in KraType.values)
                  SizedBox(
                    width: itemWidth,
                    child: _KraFolderCard(
                      kra: kra,
                      stats: _statsForKra(documents, kra),
                      onTap: () {
                        Navigator.pushNamed(
                          context,
                          AppRoutes.kraExplorer,
                          arguments: KraExplorerLaunch(kra: kra),
                        );
                      },
                    ),
                  ),
              ],
            );
          },
        ),
      ],
    );
  }

  static _KraFolderStats _statsForKra(List<FacultyDocument> docs, KraType kra) {
    final rows = docs.where((d) => d.kra == kra).toList();
    var pending = 0;
    var approved = 0;
    var revision = 0;
    for (final doc in rows) {
      switch (doc.status) {
        case DocumentStatus.validated:
        case DocumentStatus.systemApproved:
          approved += 1;
        case DocumentStatus.needsRevision:
          revision += 1;
        case DocumentStatus.pendingReview:
        case DocumentStatus.processing:
          pending += 1;
        case DocumentStatus.draft:
        case DocumentStatus.invalid:
          break;
      }
    }
    return _KraFolderStats(
      total: rows.length,
      pending: pending,
      approved: approved,
      revision: revision,
    );
  }
}

class _KraFolderStats {
  const _KraFolderStats({
    required this.total,
    required this.pending,
    required this.approved,
    required this.revision,
  });

  final int total;
  final int pending;
  final int approved;
  final int revision;
}

class _KraFolderCard extends StatelessWidget {
  const _KraFolderCard({
    required this.kra,
    required this.stats,
    required this.onTap,
  });

  final KraType kra;
  final _KraFolderStats stats;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final statsLine = [
      '${stats.total} file${stats.total == 1 ? '' : 's'}',
      if (stats.pending > 0) '${stats.pending} pending',
      if (stats.revision > 0) '${stats.revision} revise',
    ].join(' · ');

    return CompactFolderCard(
      icon: kra.icon,
      iconColor: AppColors.kra(kra),
      title: kra.code,
      subtitle: kra.label,
      subtitleMaxLines: 3,
      trailingLine: statsLine.isEmpty ? 'No uploads yet' : statsLine,
      onTap: onTap,
    );
  }
}
