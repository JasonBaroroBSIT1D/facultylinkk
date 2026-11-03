import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../data/criterion_c_evidence.dart';
import '../../data/criterion_c_ux.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import 'criterion_c_upload_requirements_screen.dart';

class CriterionCTrackScreen extends StatefulWidget {
  const CriterionCTrackScreen({super.key, required this.primaryDocumentId});

  final String primaryDocumentId;

  @override
  State<CriterionCTrackScreen> createState() => _CriterionCTrackScreenState();
}

class _CriterionCTrackScreenState extends State<CriterionCTrackScreen> {
  CriterionCEvidencePayload? _payload;
  bool _loading = true;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    if (AppState.instance.isSignedIn && !AppState.instance.usesMockAuth) {
      AppState.instance.refreshScoringConfiguration(quiet: true);
    }
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await AppState.instance.refreshData(label: 'Updating…', soft: true);
      final p = await AppState.instance.fetchCriterionCEvidenceBundle(widget.primaryDocumentId);
      if (!mounted) return;
      setState(() {
        _payload = p;
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

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      await AppState.instance.submitCriterionCAccomplishment(widget.primaryDocumentId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Submitted for reviewer assessment.')),
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Submit failed: $e'), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final doc = AppState.instance.documentById(widget.primaryDocumentId);
    final bundle = _payload?.bundle;
    final validation = _payload?.validation;
    final scoring = _payload?.scoring;
    final rows = CriterionCChecklistRow.fromBundle(bundle);
    final missing = rows.where((r) => r.status == 'missing').toList();
    final remarks = bundle?['reviewerRemarks']?.toString().trim();
    final reviewStatus = bundle?['reviewStatus']?.toString();
    final assessed = scoring?.reviewerAssessedPoints;
    final lockedCfg = bundle?['scoringConfiguration'];
    final lockedCfgLabel = _lockedConfigurationLabel(lockedCfg);
    final canSubmit = doc?.status == DocumentStatus.draft ||
        doc?.status == DocumentStatus.needsRevision;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Accomplishment'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
                  Text(
                    CriterionCUx.accomplishmentTitle(bundle, fallback: doc?.title),
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    CriterionCUx.facultyWorkStatus(validation, reviewStatus: reviewStatus),
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  if (CriterionCUx.needsPolicyReview(validation))
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text(
                        'Needs Reviewer/Policy Review — do not assume approval.',
                        style: TextStyle(color: Colors.orange, fontWeight: FontWeight.w600),
                      ),
                    ),
                  const SizedBox(height: 16),
                  if (lockedCfgLabel != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        lockedCfgLabel,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.35),
                      ),
                    ),
                  _section(
                    'Estimated points',
                    scoring?.estimatedPoints != null
                        ? '${scoring!.estimatedPoints!.toStringAsFixed(1)} pts (server estimate — pending verification)'
                        : '—',
                  ),
                  if (assessed != null)
                    _section('Reviewer-assessed points', '${assessed.toStringAsFixed(1)} pts (official)'),
                  if (validation?.blockers.isNotEmpty == true)
                    _section('Requirements', validation!.blockers.map((b) => '• $b').join('\n')),
                  if (validation?.flags.isNotEmpty == true)
                    _section(
                      'Validation',
                      validation!.flags.map((f) => '• ${CriterionCUx.humanizeFlag(f)}').join('\n'),
                    ),
                  if (remarks != null && remarks.isNotEmpty) _section('Reviewer remarks', remarks),
                  if (missing.isNotEmpty)
                    _section('Still missing', missing.map((r) => '• ${r.label}').join('\n')),
                  _section(
                    'Evidence checklist',
                    rows.map((r) => '• ${r.label}: ${CriterionCUx.checklistStatusLabel(r.status)}').join('\n'),
                  ),
                  if (doc != null)
                    Text(
                      'OCR: ${doc.ocrStatusLabel}',
                      style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                    ),
                  const SizedBox(height: 24),
                  OutlinedButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => CriterionCUploadRequirementsScreen(
                            primaryDocumentId: widget.primaryDocumentId,
                          ),
                        ),
                      ).then((_) => _load());
                    },
                    child: const Text('Upload or replace evidence'),
                  ),
                  const SizedBox(height: 12),
                  if (canSubmit)
                    PrimaryButton(
                      label: _submitting ? 'Submitting…' : 'Submit for review',
                      loading: _submitting,
                      onPressed: _submitting || validation?.readyForReviewer != true ? null : _submit,
                    ),
                ],
              ),
            ),
    );
  }

  String? _lockedConfigurationLabel(Object? raw) {
    if (raw is! Map) return null;
    final version = raw['version'];
    final effective = raw['effectiveFrom']?.toString();
    if (version == null && (effective == null || effective.isEmpty)) return null;
    final parts = <String>['This accomplishment uses scoring configuration'];
    if (version != null) parts.add('v$version');
    if (effective != null && effective.isNotEmpty) parts.add('effective $effective');
    parts.add('(may differ from the currently applicable published config).');
    return parts.join(' ');
  }

  Widget _section(String heading, String body) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(heading, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 6),
          Text(body, style: const TextStyle(height: 1.45)),
        ],
      ),
    );
  }
}
