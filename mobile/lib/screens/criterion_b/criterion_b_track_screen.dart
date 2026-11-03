import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_b_evidence.dart';
import '../../data/criterion_b_ux.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import 'criterion_b_upload_requirements_screen.dart';

/// Screen 4 — save and track progress.
class CriterionBTrackScreen extends StatefulWidget {
  const CriterionBTrackScreen({super.key, required this.primaryDocumentId});

  final String primaryDocumentId;

  @override
  State<CriterionBTrackScreen> createState() => _CriterionBTrackScreenState();
}

class _CriterionBTrackScreenState extends State<CriterionBTrackScreen> {
  CriterionBEvidencePayload? _payload;
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      await AppState.instance.refreshData(label: 'Updating…', soft: true);
      final p = await AppState.instance.fetchCriterionBEvidenceBundle(widget.primaryDocumentId);
      if (!mounted) return;
      setState(() {
        _payload = p;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Future<void> _saveMyWork() async {
    setState(() => _saving = true);
    await AppState.instance.refreshData(label: 'Saving…');
    if (!mounted) return;
    setState(() => _saving = false);
    await _load();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Your work is saved. You can come back anytime to finish uploading.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final doc = AppState.instance.documentById(widget.primaryDocumentId);
    final bundle = _payload?.bundle;
    final validation = _payload?.validation;
    final title = CriterionBUx.submissionSummaryTitle(bundle);
    final rows = CriterionBChecklistRow.fromBundle(bundle);
    final missing = rows.where((r) => r.status == 'missing').toList();
    final remarks = bundle?['reviewerRemarks']?.toString().trim();
    final scoring = _payload?.scoring;

    String nextStep;
    if (validation?.isHardInvalid == true) {
      nextStep = 'Review reviewer feedback and update your documents.';
    } else if (validation?.validationStatus == 'incomplete' || missing.isNotEmpty) {
      nextStep = 'Upload the documents still listed as missing.';
    } else if (validation?.readyForScoring == true) {
      nextStep = 'Your reviewer verified your evidence. Watch for official scoring in your evaluation.';
    } else {
      nextStep = 'Your reviewer is checking your files. OCR text reading does not mean approval yet.';
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Save & track'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy)),
                const SizedBox(height: 6),
                Text(
                  CriterionBUx.facultyWorkStatus(validation),
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                ),
                const SizedBox(height: 20),
                _section('What to do next', nextStep),
                _section(
                  'Current score',
                  [
                    '${scoring?.currentScoreLabel ?? 'Estimated'}: ${scoring?.currentScoreDisplay ?? 'Not available yet'}',
                    if (scoring?.currentScoreLabel == 'Reviewer Assessed')
                      'Your reviewer completed an assessment for this accomplishment.'
                    else
                      'This is an automated estimate from published rules. It may change after reviewer assessment.',
                  ].join('\n'),
                ),
                if (remarks != null && remarks.isNotEmpty)
                  _section('Reviewer feedback', remarks),
                if (scoring?.reviewerProposedJustification != null &&
                    scoring!.reviewerProposedJustification!.trim().isNotEmpty)
                  _section('Reviewer score explanation', scoring.reviewerProposedJustification!.trim()),
                if (missing.isNotEmpty)
                  _section(
                    'Still missing',
                    missing.map((r) => '• ${r.label}').join('\n'),
                  ),
                _section(
                  'Uploaded items',
                  rows
                      .where((r) => r.status != 'missing')
                      .map((r) => '• ${r.label}: ${CriterionBUx.facultyDocumentStatus(r.status)}')
                      .join('\n'),
                ),
                const SizedBox(height: 24),
                PrimaryButton(
                  label: _saving ? 'Saving…' : 'Save my work',
                  loading: _saving,
                  onPressed: _saving ? null : _saveMyWork,
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) =>
                            CriterionBUploadRequirementsScreen(primaryDocumentId: widget.primaryDocumentId),
                      ),
                    ).then((_) => _load());
                  },
                  child: const Text('Add or replace documents'),
                ),
                if (doc != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Submitted ${doc.submittedAt.toLocal().toString().split('.').first}',
                    style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ],
              ],
            ),
    );
  }

  Widget _section(String heading, String body) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(heading, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 6),
          Text(body, style: const TextStyle(height: 1.45, fontSize: 15)),
        ],
      ),
    );
  }
}
