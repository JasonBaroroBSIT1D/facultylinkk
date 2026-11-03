import 'dart:async';

import 'package:flutter/material.dart';

import '../../data/kra2_catalog.dart';
import '../../data/kra2_a_ux.dart';
import '../../data/kra2_criterion_remote.dart';
import '../../theme/app_colors.dart';
import 'kra2_hub_widgets.dart';
import 'kra2_review_submit_screen.dart';
import 'kra2_wizard_screen.dart';

class Kra2CriterionHubScreen extends StatefulWidget {
  const Kra2CriterionHubScreen({super.key, required this.criterionId});

  final String criterionId;

  @override
  State<Kra2CriterionHubScreen> createState() => _Kra2CriterionHubScreenState();
}

class _Kra2CriterionHubScreenState extends State<Kra2CriterionHubScreen> {
  bool _remoteLoading = false;
  String? _remoteError;
  Map<String, dynamic>? _summary;
  List<Map<String, dynamic>> _rows = const [];
  Timer? _slowHintTimer;
  bool _showSlowHint = false;

  List<Kra2AccomplishmentGroup> get _groups =>
      Kra2Catalog.accomplishmentGroups(widget.criterionId);

  @override
  void initState() {
    super.initState();
    final cached = Kra2CriterionRemote.cached(widget.criterionId);
    if (cached != null) {
      _applySnapshot(cached);
    }
    _refreshRemote(showInlineSpinner: cached == null);
  }

  @override
  void dispose() {
    _slowHintTimer?.cancel();
    super.dispose();
  }

  void _applySnapshot(Kra2CriterionSnapshot snap) {
    _summary = snap.summary;
    _rows = snap.accomplishments;
  }

  Future<void> _refreshRemote({bool showInlineSpinner = true}) async {
    if (showInlineSpinner) {
      setState(() {
        _remoteLoading = true;
        _remoteError = null;
        _showSlowHint = false;
      });
      _slowHintTimer?.cancel();
      _slowHintTimer = Timer(const Duration(seconds: 8), () {
        if (mounted && _remoteLoading) setState(() => _showSlowHint = true);
      });
    }
    try {
      final snap = await Kra2CriterionRemote.fetch(widget.criterionId);
      if (!mounted) return;
      setState(() {
        _applySnapshot(snap);
        _remoteLoading = false;
        _remoteError = null;
        _showSlowHint = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _remoteError = 'We couldn\'t load your submissions. Please try again.';
        _remoteLoading = false;
      });
    } finally {
      _slowHintTimer?.cancel();
    }
  }

  void _startGroup(Kra2AccomplishmentGroup group) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => Kra2WizardScreen(
          criterionId: widget.criterionId,
          groupKey: group.key,
        ),
      ),
    ).then((_) => _refreshRemote(showInlineSpinner: false));
  }

  void _openRow(Map<String, dynamic> row) {
    final docId = (row['documentId'] ?? '').toString();
    if (docId.isEmpty) return;
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => Kra2ReviewSubmitScreen(
          primaryDocumentId: docId,
          onFinished: () => Navigator.pop(context),
        ),
      ),
    ).then((_) => _refreshRemote(showInlineSpinner: false));
  }

  @override
  Widget build(BuildContext context) {
    final title = Kra2Catalog.criterionTitle(widget.criterionId);
    final verified = (_summary?['validatedPoints'] as num?)?.toDouble();
    final max = (_summary?['maxPoints'] as num?)?.toDouble() ?? 100;
    final draftEst = (_summary?['draftEstimatedSum'] as num?)?.toDouble();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(title),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: RefreshIndicator(
        onRefresh: () => _refreshRemote(showInlineSpinner: false),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
          children: [
            Text(
              Kra2Catalog.criterionHubSubtitle(widget.criterionId),
              style: const TextStyle(
                fontSize: 16,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            const Kra2StepGuide(),
            const SizedBox(height: 20),
            Text(
              'Add something new',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
            ),
            const SizedBox(height: 10),
            ..._groups.map(
              (g) => Kra2AccomplishmentTypeCard(
                title: g.title,
                subtitle: g.description,
                icon: g.icon,
                onTap: () => _startGroup(g),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Your submissions',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
            ),
            const SizedBox(height: 8),
            if (_remoteError != null)
              Kra2ErrorRetryBar(
                message: _remoteError!,
                onRetry: () => _refreshRemote(showInlineSpinner: true),
              ),
            if (_remoteLoading && _rows.isEmpty && _remoteError == null) ...[
              const Kra2InlineLoadingBanner(message: 'Loading your submissions…'),
              if (_showSlowHint)
                Padding(
                  padding: const EdgeInsets.only(top: 4, bottom: 8),
                  child: Text(
                    'This is taking longer than expected.',
                    style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                  ),
                ),
            ],
            if (!_remoteLoading && _rows.isEmpty && _remoteError == null)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text(
                  'You have not submitted anything here yet. Pick a type above to get started.',
                  style: TextStyle(color: AppColors.textSecondary, height: 1.4),
                ),
              ),
            if (_summary != null || (_rows.isNotEmpty && !_remoteLoading))
              Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Your progress',
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ),
                          if (_remoteLoading)
                            const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      if (verified != null)
                        Text(
                          'Approved so far: ${verified.toStringAsFixed(0)} of ${max.toStringAsFixed(0)} possible points',
                          style: Theme.of(context).textTheme.titleMedium,
                        )
                      else if (_remoteLoading)
                        Text(
                          'Updating points…',
                          style: TextStyle(color: Colors.grey.shade700),
                        ),
                      if (draftEst != null && verified != null && draftEst > verified)
                        Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            'Draft items may add about ${draftEst.toStringAsFixed(0)} possible points after review.',
                            style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ..._rows.map((row) {
              final submitted = (row['submittedForReviewAt'] ?? '').toString().isNotEmpty;
              final status = Kra2AUx.facultyStatus(
                reviewStatus: row['reviewStatus']?.toString(),
                validationStatus: row['validationStatus']?.toString(),
                submittedForReview: submitted,
              );
              final indId = row['indicatorId']?.toString();
              final listTitle = Kra2Catalog.submissionListTitle(
                indicatorId: indId,
                outputTitle: row['outputTitle']?.toString(),
              );
              final ptsLine = Kra2AUx.pointsLine(
                status: status,
                estimatedPoints: (row['estimatedPoints'] as num?)?.toDouble(),
                reviewerAssessedPoints: (row['reviewerAssessedPoints'] as num?)?.toDouble(),
              );
              final footnote = Kra2AUx.pointsFootnote(status);
              return Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  title: Text(
                    listTitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(Kra2AUx.statusLabel(status)),
                      Text(
                        Kra2AUx.statusNextAction(status),
                        style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                      ),
                      if (ptsLine.isNotEmpty) Text(ptsLine),
                      if (footnote.isNotEmpty)
                        Text(
                          footnote,
                          style: TextStyle(color: Colors.grey.shade700, fontSize: 12),
                        ),
                    ],
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _openRow(row),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}
