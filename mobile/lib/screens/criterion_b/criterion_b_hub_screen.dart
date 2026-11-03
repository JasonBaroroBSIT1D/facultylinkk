import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_b_catalog.dart';
import '../../data/criterion_b_ux.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';
import '../../widgets/tappable_card.dart';
import 'criterion_b_add_work_screen.dart';
import 'criterion_b_track_screen.dart';

/// Screen 1 — Criterion B home (no indicator folders).
class CriterionBHubScreen extends StatelessWidget {
  const CriterionBHubScreen({super.key});

  static List<FacultyDocument> _savedWork() {
    return AppState.instance.documents
        .where(
          (d) =>
              d.kra == KraType.instruction &&
              d.criterionId == CriterionBCatalog.criterionId &&
              d.isCriterionBPrimaryClaim,
        )
        .toList()
      ..sort((a, b) => b.submittedAt.compareTo(a.submittedAt));
  }

  @override
  Widget build(BuildContext context) {
    final saved = _savedWork();
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Teaching Materials & Programs'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: RefreshIndicator(
        onRefresh: () => AppState.instance.refreshData(label: 'Refreshing…'),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          children: [
            const Text(
              'Add teaching materials or academic programs you created or helped develop.',
              style: TextStyle(fontSize: 16, height: 1.45, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 20),
            _HomeChoice(
              title: 'Teaching Material',
              subtitle: 'Books, modules, manuals, and multimedia.',
              icon: Icons.menu_book_outlined,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const CriterionBAddWorkScreen(kind: CriterionBWorkKind.teaching),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            _HomeChoice(
              title: 'Academic Program',
              subtitle: 'Programs you developed or helped create.',
              icon: Icons.school_outlined,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => const CriterionBAddWorkScreen(kind: CriterionBWorkKind.program),
                  ),
                );
              },
            ),
            const SizedBox(height: 28),
            const Text(
              'My saved work',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.navy),
            ),
            const SizedBox(height: 10),
            if (saved.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text(
                  'Nothing saved yet. Tap Teaching Material or Academic Program above to start.',
                  style: TextStyle(color: AppColors.textSecondary, height: 1.45),
                ),
              )
            else
              for (final doc in saved) _SavedWorkTile(document: doc),
          ],
        ),
      ),
    );
  }
}

class _HomeChoice extends StatelessWidget {
  const _HomeChoice({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return TappableCard(
      onTap: onTap,
      padding: const EdgeInsets.all(22),
      child: Row(
        children: [
          Icon(icon, size: 40, color: AppColors.navy),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                const SizedBox(height: 4),
                Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, height: 1.35)),
              ],
            ),
          ),
          const Icon(Icons.arrow_forward_ios, size: 18, color: AppColors.textSecondary),
        ],
      ),
    );
  }
}

class _SavedWorkTile extends StatelessWidget {
  const _SavedWorkTile({required this.document});

  final FacultyDocument document;

  @override
  Widget build(BuildContext context) {
    final bundle = document.criterionBEvidence?.bundle;
    final validation = document.criterionBEvidence?.validation;
    final subtitle = CriterionBUx.accomplishmentTypeSubtitle(
      bundle: bundle,
      indicatorId: document.indicatorId,
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TappableCard(
        borderRadius: BorderRadius.circular(14),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => CriterionBTrackScreen(primaryDocumentId: document.id),
            ),
          );
        },
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    CriterionBUx.submissionSummaryTitle(bundle),
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                  ),
                  Text(subtitle, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
                  const SizedBox(height: 6),
                  Text(
                    CriterionBUx.facultyWorkStatus(validation),
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),
            const Text('Open', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.forestLight)),
          ],
        ),
      ),
    );
  }
}
