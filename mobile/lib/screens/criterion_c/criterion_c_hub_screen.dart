import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_c_catalog.dart';
import '../../data/criterion_c_evidence.dart';
import '../../data/criterion_c_ux.dart';
import '../../theme/app_colors.dart';
import '../../widgets/scoring_configuration_banner.dart';
import '../../widgets/tappable_card.dart';
import 'criterion_c_add_work_screen.dart';
import 'criterion_c_track_screen.dart';

/// Criterion C home — accomplishments, scoring summary, add flow.
class CriterionCHubScreen extends StatefulWidget {
  const CriterionCHubScreen({super.key});

  @override
  State<CriterionCHubScreen> createState() => _CriterionCHubScreenState();
}

class _CriterionCHubScreenState extends State<CriterionCHubScreen> {
  CriterionCSummary? _summary;
  List<CriterionCAccomplishmentRow> _rows = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await AppState.instance.refreshData(label: 'Updating…', soft: true);
      if (!AppState.instance.usesMockAuth) {
        await AppState.instance.refreshScoringConfiguration(force: true, quiet: true);
      }
      final results = await Future.wait([
        AppState.instance.fetchCriterionCSummary(quiet: true),
        AppState.instance.fetchCriterionCAccomplishments(quiet: true),
      ]);
      if (!mounted) return;
      setState(() {
        _summary = results[0] as CriterionCSummary?;
        _rows = results[1] as List<CriterionCAccomplishmentRow>;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  /// Pending accomplishments only — verified approved points stay in summary.validatedPoints.
  double _pendingEstimateSum() {
    var sum = 0.0;
    for (final row in _rows) {
      final rs = (row.reviewStatus ?? 'pending').toLowerCase();
      if (rs == 'approved' || rs == 'rejected') continue;
      sum += row.estimatedPoints ?? 0;
    }
    return sum;
  }

  @override
  Widget build(BuildContext context) {
    final summary = _summary;
    final maxPts = summary?.maxPoints ?? CriterionCCatalog.maxPoints;
    final verifiedTotal = summary?.validatedPoints ?? 0.0;
    final pendingEst = _pendingEstimateSum();
    final cappedPending = pendingEst > maxPts ? maxPts : pendingEst;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Research Advising & Mentorship'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CriterionCAddWorkScreen()),
          ).then((_) => _load());
        },
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
        icon: const Icon(Icons.add),
        label: const Text('Add Accomplishment'),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 96),
                children: [
                  const ScoringConfigurationBanner(),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                  _CriterionCScoreCard(
                    verifiedPoints: verifiedTotal,
                    maxPoints: maxPts,
                    pendingEstimate: cappedPending > 0 ? cappedPending : null,
                    usesMock: AppState.instance.usesMockAuth,
                  ),
                  const SizedBox(height: 28),
                  const Text(
                    'My accomplishments',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.navy),
                  ),
                  const SizedBox(height: 10),
                  if (_rows.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: Text(
                        'No accomplishments yet. Tap Add Accomplishment to document research advising, panel service, or mentorship.',
                        style: TextStyle(color: AppColors.textSecondary, height: 1.45),
                      ),
                    )
                  else
                    for (final row in _rows) _AccomplishmentTile(row: row),
                ],
              ),
      ),
    );
  }
}

class _CriterionCScoreCard extends StatelessWidget {
  const _CriterionCScoreCard({
    required this.verifiedPoints,
    required this.maxPoints,
    required this.pendingEstimate,
    required this.usesMock,
  });

  final double verifiedPoints;
  final double maxPoints;
  final double? pendingEstimate;
  final bool usesMock;

  @override
  Widget build(BuildContext context) {
    final maxLabel = maxPoints.toStringAsFixed(maxPoints == maxPoints.roundToDouble() ? 0 : 1);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Criterion C score',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
            ),
            const SizedBox(height: 8),
            Text(
              'Reviewer-verified: ${verifiedPoints.toStringAsFixed(1)} / $maxLabel pts',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy),
            ),
            if (pendingEstimate != null) ...[
              const SizedBox(height: 8),
              Text(
                'Pending estimate: ${pendingEstimate!.toStringAsFixed(1)} pts',
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15, color: AppColors.navy),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              usesMock
                  ? 'Reference Annex A values (mock mode). Verified and pending estimates are kept separate.'
                  : 'From your published scoring configuration. Verified points count after reviewer approval; pending estimates are not verified.',
              style: const TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.35),
            ),
          ],
        ),
      ),
    );
  }
}

class _AccomplishmentTile extends StatelessWidget {
  const _AccomplishmentTile({required this.row});

  final CriterionCAccomplishmentRow row;

  String? _reviewerRemarks(Map<String, dynamic>? bundle) {
    if (bundle == null) return null;
    final assessment = bundle['reviewerAssessment'];
    if (assessment is Map) {
      final fromAssessment = assessment['remarks']?.toString();
      if (fromAssessment != null && fromAssessment.trim().isNotEmpty) {
        return fromAssessment;
      }
    }
    final remarks = bundle['reviewerRemarks']?.toString();
    if (remarks != null && remarks.trim().isNotEmpty) return remarks;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final doc = AppState.instance.documentById(row.documentId);
    final bundle = doc?.criterionCEvidence?.bundle;
    final title = CriterionCUx.accomplishmentTitle(bundle, fallback: row.projectTitle ?? row.title);
    final statusLine = CriterionCUx.accomplishmentListStatusLine(
      reviewStatus: row.reviewStatus,
      documentStatus: row.status,
      estimatedPoints: row.estimatedPoints,
      reviewerAssessedPoints: row.reviewerAssessedPoints,
      reviewerRemarks: _reviewerRemarks(bundle),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: TappableCard(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => CriterionCTrackScreen(primaryDocumentId: row.documentId),
            ),
          ).then((_) {});
        },
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  Text(
                    CriterionCUx.serviceSubtitle(indicatorId: row.indicatorId, bundle: bundle),
                    style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    statusLine,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}
