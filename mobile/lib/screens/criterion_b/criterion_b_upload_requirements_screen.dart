import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_b_catalog.dart';
import '../../data/criterion_b_evidence.dart';
import '../../data/criterion_b_ux.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import 'criterion_b_track_screen.dart';

/// Screen 3 — upload supporting documents (automatic linking).
class CriterionBUploadRequirementsScreen extends StatefulWidget {
  const CriterionBUploadRequirementsScreen({super.key, required this.primaryDocumentId});

  final String primaryDocumentId;

  @override
  State<CriterionBUploadRequirementsScreen> createState() =>
      _CriterionBUploadRequirementsScreenState();
}

class _CriterionBUploadRequirementsScreenState extends State<CriterionBUploadRequirementsScreen> {
  CriterionBEvidencePayload? _payload;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
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

  @override
  Widget build(BuildContext context) {
    final doc = AppState.instance.documentById(widget.primaryDocumentId);
    final bundle = _payload?.bundle;
    final claimType = bundle?['claimType']?.toString();
    final rows = CriterionBChecklistRow.fromBundle(bundle)
        .where(
          (r) =>
              r.slotId != 'primary_material' &&
              r.slotId != 'primary_contribution_document' &&
              CriterionBUx.requirementForSlot(
                    r.slotId,
                    claimType: claimType,
                    indicatorId: doc?.indicatorId,
                    bundle: bundle,
                  ) !=
                  EvidenceRequirement.notRequired,
        )
        .toList();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Upload files'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const Text(
                  'Here are the documents you need',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Tap Upload for each item. Files link automatically—you do not need to pick technical categories.',
                  style: TextStyle(color: AppColors.textSecondary, height: 1.45, fontSize: 15),
                ),
                const SizedBox(height: 20),
                for (final row in rows) _RequirementRow(
                  row: row,
                  primaryId: widget.primaryDocumentId,
                  indicatorId: doc?.indicatorId,
                  claimType: claimType,
                  bundle: bundle,
                  onChanged: _load,
                ),
                const SizedBox(height: 24),
                PrimaryButton(
                  label: 'Continue to save & track',
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => CriterionBTrackScreen(primaryDocumentId: widget.primaryDocumentId),
                      ),
                    );
                  },
                ),
              ],
            ),
    );
  }
}

class _RequirementRow extends StatelessWidget {
  const _RequirementRow({
    required this.row,
    required this.primaryId,
    required this.indicatorId,
    required this.claimType,
    required this.bundle,
    required this.onChanged,
  });

  final CriterionBChecklistRow row;
  final String primaryId;
  final String? indicatorId;
  final String? claimType;
  final Map<String, dynamic>? bundle;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final req = CriterionBUx.requirementForSlot(
      row.slotId,
      claimType: claimType,
      indicatorId: indicatorId,
      bundle: bundle,
    );
    final status = CriterionBUx.facultyDocumentStatus(row.status);
    final linked = row.documentId != null ? AppState.instance.documentById(row.documentId!) : null;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(row.label, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              ),
              Text(
                CriterionBUx.requirementLabel(req),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textSecondary),
              ),
            ],
          ),
          if (CriterionBUx.slotPurpose(row.slotId) != null) ...[
            const SizedBox(height: 6),
            Text(
              CriterionBUx.slotPurpose(row.slotId)!,
              style: const TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.35),
            ),
          ],
          const SizedBox(height: 10),
          Text(status, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
          if (linked != null)
            Text('File: ${linked.title}', style: const TextStyle(fontSize: 13)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              ElevatedButton.icon(
                onPressed: () async {
                  await Navigator.pushNamed(
                    context,
                    AppRoutes.uploadDocument,
                    arguments: UploadDocumentLaunch(
                      kra: KraType.instruction,
                      criterionId: CriterionBCatalog.criterionId,
                      indicatorId: indicatorId,
                      bundlePrimaryDocumentId: primaryId,
                      evidenceSlot: row.slotId,
                    ),
                  );
                  onChanged();
                },
                icon: const Icon(Icons.upload_file),
                label: Text(row.isMissing ? 'Upload file' : 'Replace file'),
              ),
              if (linked != null)
                TextButton(
                  onPressed: () {
                    Navigator.pushNamed(context, AppRoutes.documentDetails, arguments: row.documentId);
                  },
                  child: const Text('View'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
