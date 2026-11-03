import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_c_catalog.dart';
import '../../data/criterion_c_evidence.dart';
import '../../data/criterion_c_ux.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';

class CriterionCUploadRequirementsScreen extends StatefulWidget {
  const CriterionCUploadRequirementsScreen({super.key, required this.primaryDocumentId});

  final String primaryDocumentId;

  @override
  State<CriterionCUploadRequirementsScreen> createState() =>
      _CriterionCUploadRequirementsScreenState();
}

class _CriterionCUploadRequirementsScreenState extends State<CriterionCUploadRequirementsScreen> {
  CriterionCEvidencePayload? _payload;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final p = await AppState.instance.fetchCriterionCEvidenceBundle(widget.primaryDocumentId);
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

  void _uploadSlot(String slotId) {
    final doc = AppState.instance.documentById(widget.primaryDocumentId);
    Navigator.pushNamed(
      context,
      AppRoutes.uploadDocument,
      arguments: UploadDocumentLaunch(
        kra: KraType.instruction,
        criterionId: CriterionCCatalog.criterionId,
        indicatorId: doc?.indicatorId,
        bundlePrimaryDocumentId: widget.primaryDocumentId,
        evidenceSlot: slotId,
      ),
    ).then((_) => _load());
  }

  @override
  Widget build(BuildContext context) {
    final bundle = _payload?.bundle;
    final mentorship = (bundle?['serviceCategory'] ?? '').toString() == 'mentorship';
    final rows = CriterionCChecklistRow.fromBundle(bundle);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Evidence checklist'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                const Text(
                  'Required evidence (Annex A)',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy),
                ),
                const SizedBox(height: 8),
                Text(
                  mentorship
                      ? 'Mentorship: designation, major award, mechanics, and organization profile.'
                      : 'Research: signed approval sheet and RRPA/COPC for the program.',
                  style: const TextStyle(color: AppColors.textSecondary, height: 1.45),
                ),
                const SizedBox(height: 20),
                for (final row in rows)
                  Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      title: Text(row.label),
                      subtitle: Text(CriterionCUx.checklistStatusLabel(row.status)),
                      trailing: TextButton(
                        onPressed: () => _uploadSlot(row.slotId),
                        child: Text(row.status == 'missing' ? 'Upload' : 'Replace'),
                      ),
                    ),
                  ),
              ],
            ),
    );
  }
}
