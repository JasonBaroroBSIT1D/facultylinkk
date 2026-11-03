import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/kra2_a_catalog.dart';
import '../../data/kra2_a_ux.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';

class Kra2AReviewSubmitScreen extends StatefulWidget {
  const Kra2AReviewSubmitScreen({
    super.key,
    required this.primaryDocumentId,
    this.onBackToUpload,
    this.onFinished,
  });

  final String primaryDocumentId;
  final VoidCallback? onBackToUpload;
  final VoidCallback? onFinished;

  @override
  State<Kra2AReviewSubmitScreen> createState() => _Kra2AReviewSubmitScreenState();
}

class _Kra2AReviewSubmitScreenState extends State<Kra2AReviewSubmitScreen> {
  final _titleCtrl = TextEditingController();
  final _authorsCtrl = TextEditingController();
  final _journalCtrl = TextEditingController();
  final _dateCtrl = TextEditingController();
  final _doiCtrl = TextEditingController();
  final _percentCtrl = TextEditingController();

  Map<String, dynamic>? _bundle;
  Map<String, dynamic>? _validation;
  Map<String, dynamic>? _scoring;
  String? _ocrStatus;
  bool _loading = true;
  bool _saving = false;
  bool _submitting = false;
  String? _error;

  bool get _isCoAuthor {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    return ind == Kra2AJournalCatalog.coIndicatorId;
  }

  @override
  void initState() {
    super.initState();
    _load(pollOcr: true);
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _authorsCtrl.dispose();
    _journalCtrl.dispose();
    _dateCtrl.dispose();
    _doiCtrl.dispose();
    _percentCtrl.dispose();
    super.dispose();
  }

  Future<void> _load({bool pollOcr = false}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      if (pollOcr) {
        await AppState.instance.pollDocumentAfterUpload(widget.primaryDocumentId);
      } else {
        await AppState.instance.refreshFacultyDocument(widget.primaryDocumentId, quiet: true);
      }
      final payload = await AppState.instance.fetchKra2EvidenceBundle(widget.primaryDocumentId);
      if (!mounted) return;
      final bundle = payload['bundle'] is Map ? Map<String, dynamic>.from(payload['bundle'] as Map) : null;
      _syncControllers(bundle);
      setState(() {
        _bundle = bundle;
        _validation = payload['validation'] is Map ? Map<String, dynamic>.from(payload['validation'] as Map) : null;
        _scoring = payload['scoring'] is Map ? Map<String, dynamic>.from(payload['scoring'] as Map) : null;
        _ocrStatus = payload['ocrStatus']?.toString();
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'We could not load your submission. Pull to refresh or try again later.';
        _loading = false;
      });
    }
  }

  void _syncControllers(Map<String, dynamic>? bundle) {
    if (bundle == null) return;
    void set(TextEditingController c, String key) {
      final v = (bundle[key] ?? '').toString().trim();
      if (c.text.isEmpty && v.isNotEmpty) c.text = v;
    }

    set(_titleCtrl, 'outputTitle');
    set(_authorsCtrl, 'authorsLine');
    set(_journalCtrl, 'journalTitle');
    set(_dateCtrl, 'publicationDate');
    set(_doiCtrl, 'publicationReference');
    final pct = bundle['declaredContributionPercent'];
    if (_percentCtrl.text.isEmpty && pct != null) {
      _percentCtrl.text = pct.toString();
    }
  }

  Map<String, dynamic> _metadataBody({required bool submit}) {
    final body = <String, dynamic>{
      'outputTitle': _titleCtrl.text.trim(),
      'authorsLine': _authorsCtrl.text.trim(),
      'journalTitle': _journalCtrl.text.trim(),
      'publicationDate': _dateCtrl.text.trim(),
      'publicationReference': _doiCtrl.text.trim(),
      'confirmMetadata': true,
    };
    if (_isCoAuthor) {
      final raw = _percentCtrl.text.trim();
      if (raw.isNotEmpty) {
        body['declaredContributionPercent'] = double.tryParse(raw) ?? raw;
      }
    }
    if (submit) body['submitAccomplishment'] = true;
    return body;
  }

  Future<void> _saveDraft() async {
    setState(() => _saving = true);
    try {
      await AppState.instance.patchKra2EvidenceBundle(
        widget.primaryDocumentId,
        _metadataBody(submit: false),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Draft saved.')),
      );
      await _load();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not save. Check your connection and try again.'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      await AppState.instance.patchKra2EvidenceBundle(
        widget.primaryDocumentId,
        _metadataBody(submit: true),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Submitted for review. We will notify you when a reviewer decides.')),
      );
      widget.onFinished?.call();
      if (widget.onFinished == null) Navigator.of(context).pop(true);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please complete all required fields and evidence before submitting.'),
          backgroundColor: Colors.red,
        ),
      );
      await _load();
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _uploadAnnexD() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.first;
    final bytes = file.bytes;
    if (bytes == null) return;
    try {
      await AppState.instance.uploadDocument(
        title: 'Certificate of Contribution',
        category: DocumentCategory.researchPublications,
        kra: KraType.research,
        kraWebId: 'kra2',
        criterionId: Kra2AJournalCatalog.criterionId,
        indicatorId: (_bundle?['indicatorId'] ?? Kra2AJournalCatalog.coIndicatorId).toString(),
        fileName: file.name,
        fileBytes: bytes,
        bundlePrimaryDocumentId: widget.primaryDocumentId,
        evidenceSlot: 'contribution_certificate',
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Contribution form uploaded.')),
      );
      await _load();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Upload failed. Try again.'), backgroundColor: Colors.red),
      );
    }
  }

  List<String> _friendlyBlockers() {
    final blockers = _validation?['blockers'];
    if (blockers is! List) return const [];
    return blockers
        .whereType<String>()
        .map(Kra2AUx.humanizeBlocker)
        .where((s) => s.isNotEmpty)
        .toList();
  }

  bool _slotMissing(String slotId) {
    final checklist = _bundle?['checklist'];
    if (checklist is! Map) return true;
    final entry = checklist[slotId];
    if (entry is! Map) return true;
    final status = (entry['status'] ?? '').toString();
    return status == 'missing' || entry['documentId'] == null;
  }

  @override
  Widget build(BuildContext context) {
    final submitted = (_bundle?['submittedForReviewAt'] ?? '').toString().isNotEmpty;
    final facultyStatus = Kra2AUx.facultyStatus(
      reviewStatus: _bundle?['reviewStatus']?.toString(),
      validationStatus: _validation?['validationStatus']?.toString(),
      submittedForReview: submitted,
    );
    final est = (_scoring?['estimatedPoints'] as num?)?.toDouble();
    final assessed = (_scoring?['reviewerAssessedPoints'] as num?)?.toDouble();
    final canEdit = facultyStatus == Kra2FacultyStatus.draft ||
        facultyStatus == Kra2FacultyStatus.needsChanges;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Step 3 of 3 — Review & Submit'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () => _load(),
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                  _StatusChip(
                    label: Kra2AUx.statusLabel(facultyStatus),
                    explanation: Kra2AUx.statusExplanation(facultyStatus),
                    points: Kra2AUx.pointsLine(
                      status: facultyStatus,
                      estimatedPoints: est,
                      reviewerAssessedPoints: assessed,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(Kra2AUx.ocrStatusLabel(_ocrStatus), style: TextStyle(color: Colors.grey.shade700)),
                  const SizedBox(height: 16),
                  const Text('Publication details', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  const Text('Check each field against your PDF. You can edit anything that looks wrong.'),
                  const SizedBox(height: 12),
                  _field('Article title', _titleCtrl, enabled: canEdit),
                  _field('Author names', _authorsCtrl, enabled: canEdit),
                  _field('Journal or publication name', _journalCtrl, enabled: canEdit),
                  _field('Publication date', _dateCtrl, enabled: canEdit, hint: 'e.g. 2025-06-01 or June 2025'),
                  _field('DOI or reference (optional)', _doiCtrl, enabled: canEdit),
                  if (_isCoAuthor)
                    _field('Your contribution (%)', _percentCtrl, enabled: canEdit, keyboard: TextInputType.number),
                  const SizedBox(height: 16),
                  const Text('Your documents', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.picture_as_pdf),
                    title: const Text('Published journal article'),
                    subtitle: const Text('Uploaded'),
                    trailing: TextButton(
                      onPressed: () => Navigator.pushNamed(
                        context,
                        AppRoutes.documentDetails,
                        arguments: widget.primaryDocumentId,
                      ),
                      child: const Text('View'),
                    ),
                  ),
                  if (_isCoAuthor) ...[
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(
                        Icons.description,
                        color: _slotMissing('contribution_certificate') ? Colors.orange : AppColors.navy,
                      ),
                      title: const Text('Certificate of Contribution (Annex D)'),
                      subtitle: Text(
                        _slotMissing('contribution_certificate')
                            ? 'Required for co-authored articles'
                            : 'Uploaded',
                      ),
                      trailing: canEdit
                          ? TextButton(onPressed: _uploadAnnexD, child: const Text('Upload'))
                          : null,
                    ),
                  ],
                  if (_friendlyBlockers().isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Before you submit', style: TextStyle(fontWeight: FontWeight.w600)),
                          ..._friendlyBlockers().map((b) => Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text('• $b'),
                              )),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  if (canEdit) ...[
                    PrimaryButton(
                      label: _submitting ? 'Submitting…' : 'Submit for Review',
                      icon: Icons.send,
                      loading: _submitting,
                      onPressed: _submitting ? null : _submit,
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton(
                      onPressed: _saving ? null : _saveDraft,
                      child: Text(_saving ? 'Saving…' : 'Save draft'),
                    ),
                    if (widget.onBackToUpload != null) ...[
                      const SizedBox(height: 8),
                      TextButton(onPressed: widget.onBackToUpload, child: const Text('Back to upload')),
                    ],
                  ] else
                    PrimaryButton(
                      label: 'Done',
                      onPressed: () {
                        widget.onFinished?.call();
                        Navigator.of(context).pop(true);
                      },
                    ),
                ],
              ),
            ),
    );
  }

  Widget _field(
    String label,
    TextEditingController controller, {
    bool enabled = true,
    String? hint,
    TextInputType? keyboard,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        enabled: enabled,
        keyboardType: keyboard,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: const OutlineInputBorder(),
          filled: true,
          fillColor: Colors.white,
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.label,
    required this.explanation,
    required this.points,
  });

  final String label;
  final String explanation;
  final String points;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Text(explanation),
            if (points.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(points, style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ],
        ),
      ),
    );
  }
}
