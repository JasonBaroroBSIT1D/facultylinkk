import 'package:flutter/material.dart';

import '../data/app_state.dart';
import '../data/criterion_b_catalog.dart';
import '../data/criterion_b_evidence.dart';
import '../data/criterion_b_ux.dart';
import '../widgets/criterion_b_workflow_header.dart';
import '../models/enums.dart';
import '../models/models.dart';
import '../navigation/app_routes.dart';
import '../screens/documents/document_flow_args.dart';
import '../theme/app_colors.dart';

/// Faculty Criterion B bundle checklist (data from backend APIs only).
class CriterionBEvidencePanel extends StatefulWidget {
  const CriterionBEvidencePanel({super.key, required this.document});

  final FacultyDocument document;

  @override
  State<CriterionBEvidencePanel> createState() => _CriterionBEvidencePanelState();
}

class _CriterionBEvidencePanelState extends State<CriterionBEvidencePanel> {
  CriterionBEvidencePayload? _payload;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _linkExistingDocument(String slotId) async {
    final candidates = AppState.instance.documents.where((d) {
      if (d.id == widget.document.id) return false;
      if (d.isCriterionBSupportingDocument) return false;
      return d.criterionId == CriterionBCatalog.criterionId;
    }).toList();
    if (candidates.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No other Criterion B uploads available to link.')),
      );
      return;
    }
    final picked = await showModalBottomSheet<FacultyDocument>(
      context: context,
      builder: (ctx) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const ListTile(title: Text('Link existing document')),
            for (final d in candidates)
              ListTile(
                title: Text(d.title),
                subtitle: Text(d.fileName),
                onTap: () => Navigator.pop(ctx, d),
              ),
          ],
        ),
      ),
    );
    if (picked == null) return;
    try {
      await AppState.instance.linkCriterionBSupporting(
        primaryDocumentId: widget.document.id,
        supportingDocumentId: picked.id,
        evidenceSlot: slotId,
      );
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _load() async {
    if (AppState.instance.usesMockAuth) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final payload = await AppState.instance.fetchCriterionBEvidenceBundle(
        widget.document.id,
        quiet: true,
      );
      if (!mounted) return;
      setState(() {
        _payload = payload ?? widget.document.criterionBEvidence;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _payload = widget.document.criterionBEvidence;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final doc = AppState.instance.documentById(widget.document.id) ?? widget.document;

    if (doc.isCriterionBSupportingDocument) {
      final link = doc.criterionBEvidence;
      final primaryId = link?.primaryDocumentIdFromLink;
      final primaryDoc = primaryId != null ? AppState.instance.documentById(primaryId) : null;
      return _SectionShell(
        title: 'Supporting document',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'This file supports a main accomplishment and does not earn separate points.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
            ),
            if (primaryId != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: () {
                  Navigator.pushNamed(context, AppRoutes.documentDetails, arguments: primaryId);
                },
                child: Text(
                  primaryDoc != null
                      ? 'Open main submission: ${primaryDoc.title}'
                      : 'Open main submission',
                ),
              ),
            ],
          ],
        ),
      );
    }

    if (!doc.isCriterionBPrimaryClaim) return const SizedBox.shrink();

    final payload = _payload ?? doc.criterionBEvidence;
    final bundle = payload?.bundle;
    final validation = payload?.validation;
    final rows = CriterionBChecklistRow.fromBundle(bundle);

    final phase = CriterionBUx.phaseForPrimary(
      bundle: bundle,
      validation: validation,
      hasPrimaryFile: true,
    );
    final claimType = bundle?['claimType']?.toString();

    return _SectionShell(
      title: CriterionBUx.submissionSummaryTitle(bundle),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_loading) const LinearProgressIndicator(minHeight: 2),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                'Could not refresh checklist. Showing last saved data.',
                style: const TextStyle(color: AppColors.warning, fontSize: 12),
              ),
            ),
          CriterionBWorkflowHeader(current: phase),
          const SizedBox(height: 12),
          if (validation != null) _ValidationBanner(validation: validation),
          if (bundle != null) ...[
            const SizedBox(height: 10),
            _ClaimSummary(
              bundle: bundle,
              validation: validation,
              contributionVerification: _payload?.contributionVerification,
            ),
          ],
          if (payload?.crossKraWarnings.isNotEmpty == true) ...[
            const SizedBox(height: 12),
            const Text('Cross-KRA notices', style: TextStyle(fontWeight: FontWeight.w700)),
            for (final w in payload!.crossKraWarnings)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  w['message']?.toString() ?? w['code']?.toString() ?? 'Review notice',
                  style: const TextStyle(fontSize: 12, height: 1.35),
                ),
              ),
          ],
          if ((bundle?['reviewerRemarks'] as String?)?.trim().isNotEmpty == true) ...[
            const SizedBox(height: 12),
            const Text('Feedback from your reviewer', style: TextStyle(fontWeight: FontWeight.w700)),
            Text(
              bundle!['reviewerRemarks'].toString(),
              style: const TextStyle(fontSize: 13, height: 1.4),
            ),
          ],
          const SizedBox(height: 14),
          const Text('Required documents', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy)),
          const SizedBox(height: 4),
          const Text(
            'Upload each item below. Text extraction (OCR) helps reviewers but does not approve your files.',
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
          ),
          const SizedBox(height: 8),
          if (rows.isEmpty)
            const Text('Your checklist will appear after the main file finishes uploading.')
          else
            for (final row in rows)
              if (CriterionBUx.requirementForSlot(
                    row.slotId,
                    claimType: claimType,
                    indicatorId: doc.indicatorId,
                    bundle: bundle,
                  ) !=
                  EvidenceRequirement.notRequired)
                _ChecklistTile(
                  row: row,
                  primaryDocumentId: doc.id,
                  indicatorId: doc.indicatorId,
                  claimType: claimType,
                  bundle: bundle,
                  onChanged: _load,
                  onLinkExisting: () => _linkExistingDocument(row.slotId),
                ),
          if (validation != null && validation.flags.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text('What you still need', style: TextStyle(fontWeight: FontWeight.w700)),
            for (final flag in validation.flags)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '• ${CriterionBUx.humanizeFlag(flag)}',
                  style: const TextStyle(fontSize: 12, height: 1.35),
                ),
              ),
          ],
          const SizedBox(height: 12),
          _AssessmentPreview(
            validation: validation,
            simulationScore: doc.effectiveSimulationScore,
          ),
        ],
      ),
    );
  }
}

class _SectionShell extends StatelessWidget {
  const _SectionShell({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy)),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }
}

class _ValidationBanner extends StatelessWidget {
  const _ValidationBanner({required this.validation});

  final CriterionBValidation validation;

  @override
  Widget build(BuildContext context) {
    final color = validation.isHardInvalid
        ? AppColors.brick
        : validation.validationStatus == 'incomplete'
            ? AppColors.warning
            : validation.readyForScoring
                ? AppColors.success
                : AppColors.info;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.35)),
      ),
      child: Text(
        validation.statusLabel,
        style: TextStyle(fontWeight: FontWeight.w700, color: color, fontSize: 13),
      ),
    );
  }
}

class _ClaimSummary extends StatelessWidget {
  const _ClaimSummary({
    required this.bundle,
    this.validation,
    this.contributionVerification,
  });

  final Map<String, dynamic> bundle;
  final CriterionBValidation? validation;
  final CriterionBContributionVerification? contributionVerification;

  @override
  Widget build(BuildContext context) {
    final isProgram = bundle['claimType'] == 'academic_program';
    if (isProgram) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _kv('Program', bundle['programName']),
          _kv('Type', _programKind(bundle['programDevelopmentKind'])),
          _kv('Role', bundle['facultyRole']),
          _kv('Contribution', bundle['contributionDescription']),
          if ((bundle['committeeName'] as String?)?.isNotEmpty == true)
            _kv('Committee', bundle['committeeName']),
          if (_rrpaLabel(bundle, validation) != null)
            _kv('RRPA/COPC applicability', _rrpaLabel(bundle, validation)),
          if (_rrpaNote(bundle, validation)?.isNotEmpty == true)
            _kv('RRPA/COPC note', _rrpaNote(bundle, validation)),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _kv('Material title', bundle['materialTitle']),
        _kv('Material type', bundle['materialType']),
        _kv('Authorship', bundle['authorship']),
        if (bundle['authorship'] == 'co') _kv('Contribution %', bundle['contributionPercent']),
        if (bundle['authorship'] == 'co' && contributionVerification != null) ...[
          _kv('Contribution status', contributionVerification!.facultyStatusLabel),
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              contributionVerification!.facultyStatusDetail,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.35),
            ),
          ),
        ],
        if (bundle['completeSetDeclared'] != null)
          _kv('Complete set declared', bundle['completeSetDeclared'] == true ? 'Yes' : 'No'),
      ],
    );
  }

  static String _programKind(Object? kind) {
    if (kind == 'new_program') return 'New program';
    if (kind == 'substantial_revision') return 'Substantial revision';
    return 'Not specified';
  }

  static String? _rrpaLabel(Map<String, dynamic> bundle, CriterionBValidation? validation) {
    final key = validation?.rrpaCopcApplicability ??
        bundle['rrpaCopcApplicability']?.toString() ??
        (bundle['rrpaCopcApplicabilityDecision'] is Map
            ? (bundle['rrpaCopcApplicabilityDecision'] as Map)['status']?.toString()
            : null);
    if (key == null || key.isEmpty || key == 'unknown') {
      return key == 'unknown' ? 'Undetermined — reviewer must decide' : null;
    }
    switch (key) {
      case 'applicable':
        return 'Applicable — RRPA or COPC required when verified';
      case 'not_applicable':
        return 'Not applicable — documented exemption';
      default:
        return key;
    }
  }

  static String? _rrpaNote(Map<String, dynamic> bundle, CriterionBValidation? validation) {
    return validation?.rrpaCopcApplicabilityNote ??
        bundle['rrpaCopcApplicabilityNote']?.toString();
  }

  Widget _kv(String label, Object? value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: RichText(
        text: TextSpan(
          style: const TextStyle(fontSize: 12, color: AppColors.textPrimary, height: 1.35),
          children: [
            TextSpan(text: '$label: ', style: const TextStyle(fontWeight: FontWeight.w700)),
            TextSpan(text: value?.toString() ?? '—'),
          ],
        ),
      ),
    );
  }
}

class _ChecklistTile extends StatelessWidget {
  const _ChecklistTile({
    required this.row,
    required this.primaryDocumentId,
    required this.indicatorId,
    required this.claimType,
    required this.bundle,
    required this.onChanged,
    required this.onLinkExisting,
  });

  final CriterionBChecklistRow row;
  final String primaryDocumentId;
  final String? indicatorId;
  final String? claimType;
  final Map<String, dynamic>? bundle;
  final VoidCallback onChanged;
  final VoidCallback onLinkExisting;

  @override
  Widget build(BuildContext context) {
    final req = CriterionBUx.requirementForSlot(
      row.slotId,
      claimType: claimType,
      indicatorId: indicatorId,
      bundle: bundle,
    );
    final statusColor = row.isVerified
        ? AppColors.success
        : row.isMissing
            ? AppColors.warning
            : AppColors.textSecondary;
    final linked = row.documentId != null
        ? AppState.instance.documentById(row.documentId!)
        : null;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(row.label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
              ),
              _RequirementChip(requirement: req),
            ],
          ),
          if (CriterionBUx.slotPurpose(row.slotId) != null) ...[
            const SizedBox(height: 6),
            Text(
              CriterionBUx.slotPurpose(row.slotId)!,
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.35),
            ),
          ],
          const SizedBox(height: 8),
          Text(
            CriterionBUx.checklistStatusLabel(row.status),
            style: TextStyle(fontSize: 13, color: statusColor, fontWeight: FontWeight.w600),
          ),
          if (linked != null)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'File: ${linked.title}',
                style: const TextStyle(fontSize: 12),
              ),
            ),
          if (row.ocrHintOnly && !row.isVerified)
            const Text(
              'Text was read automatically — your reviewer still must confirm this document.',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.35),
            ),
          if (row.reviewerNote != null && row.reviewerNote!.trim().isNotEmpty)
            Text('Reviewer note: ${row.reviewerNote}', style: const TextStyle(fontSize: 11)),
          if (row.isMissing || (!row.isVerified && row.documentId != null)) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                TextButton.icon(
                  onPressed: () async {
                    await Navigator.pushNamed(
                      context,
                      AppRoutes.uploadDocument,
                      arguments: UploadDocumentLaunch(
                        kra: KraType.instruction,
                        criterionId: CriterionBCatalog.criterionId,
                        indicatorId: indicatorId,
                        bundlePrimaryDocumentId: primaryDocumentId,
                        evidenceSlot: row.slotId,
                      ),
                    );
                    onChanged();
                  },
                  icon: const Icon(Icons.upload_file_outlined, size: 20),
                  label: Text(row.isMissing ? 'Upload' : 'Replace'),
                ),
                TextButton(
                  onPressed: onLinkExisting,
                  child: const Text('Use existing file'),
                ),
                if (row.documentId != null)
                  TextButton(
                    onPressed: () {
                      Navigator.pushNamed(context, AppRoutes.documentDetails, arguments: row.documentId);
                    },
                    child: const Text('Preview'),
                  ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _RequirementChip extends StatelessWidget {
  const _RequirementChip({required this.requirement});

  final EvidenceRequirement requirement;

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    switch (requirement) {
      case EvidenceRequirement.required:
        bg = AppColors.warningSoft;
        fg = AppColors.warning;
        break;
      case EvidenceRequirement.conditional:
        bg = AppColors.infoSoft;
        fg = AppColors.info;
        break;
      case EvidenceRequirement.optional:
        bg = AppColors.surfaceMuted;
        fg = AppColors.textSecondary;
        break;
      case EvidenceRequirement.notRequired:
        bg = AppColors.surfaceMuted;
        fg = AppColors.textSecondary;
        break;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Text(
        CriterionBUx.requirementLabel(requirement),
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: fg),
      ),
    );
  }
}

class _AssessmentPreview extends StatelessWidget {
  const _AssessmentPreview({this.validation, this.simulationScore});

  final CriterionBValidation? validation;
  final double? simulationScore;

  @override
  Widget build(BuildContext context) {
    final ready = validation?.readyForScoring == true;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Assessment preview', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
          const SizedBox(height: 6),
          if (!ready)
            const Text(
              'Estimated points appear only after your reviewer verifies all required evidence. '
              'Completing OCR does not approve documents or award points.',
              style: TextStyle(fontSize: 12, height: 1.4),
            )
          else if (simulationScore != null)
            Text(
              'Informational estimate: ${simulationScore!.toStringAsFixed(1)} points (not official until published in your evaluation record).',
              style: const TextStyle(fontSize: 12, height: 1.4),
            )
          else
            const Text(
              'Your submission is ready for scoring review. Official points will appear in your evaluation when released.',
              style: TextStyle(fontSize: 12, height: 1.4),
            ),
        ],
      ),
    );
  }
}
