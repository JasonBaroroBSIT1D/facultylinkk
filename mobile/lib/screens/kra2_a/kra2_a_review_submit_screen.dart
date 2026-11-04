import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/kra2_a_catalog.dart';
import '../../data/kra2_a_ux.dart';
import '../../data/kra2_catalog.dart';
import '../../data/kra2_ocr_sync.dart';
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
  Map<String, Map<String, dynamic>> _ocrFields = {};
  List<String> _ocrReviewFlags = const [];
  final Set<String> _userEditedFields = {};
  bool _loading = true;
  bool _saving = false;
  bool _submitting = false;
  bool _ocrPolling = false;
  bool _ocrRetrying = false;
  String? _error;

  static const _fieldIds = [
    'outputTitle',
    'authorsLine',
    'outputVenue',
    'publicationDate',
    'publicationReference',
  ];

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
      final ocrExtraction = payload['ocrExtraction'] is Map
          ? Map<String, dynamic>.from(payload['ocrExtraction'] as Map)
          : null;
      _ocrFields = Kra2OcrSync.parseExtractionFields(ocrExtraction);
      final flags = payload['ocrReviewFlags'];
      _ocrReviewFlags = flags is List ? flags.map((e) => e.toString()).toList() : const [];
      _syncControllers(bundle);
      final ocr = payload['ocrStatus']?.toString();
      setState(() {
        _bundle = bundle;
        _validation = payload['validation'] is Map ? Map<String, dynamic>.from(payload['validation'] as Map) : null;
        _scoring = payload['scoring'] is Map ? Map<String, dynamic>.from(payload['scoring'] as Map) : null;
        _ocrStatus = ocr;
        _loading = false;
      });
      if (pollOcr) {
        unawaited(_startOcrPollIfNeeded(ocr));
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'We could not load your submission. Pull to refresh or try again later.';
        _loading = false;
      });
    }
  }

  Future<void> _startOcrPollIfNeeded(String? currentStatus) async {
    final st = (currentStatus ?? '').toLowerCase();
    if (st == 'completed' || st == 'failed' || st == 'complete') return;
    if (_ocrPolling) return;
    _ocrPolling = true;
    if (mounted) setState(() {});
    await AppState.instance.pollKra2OcrInBackground(
      widget.primaryDocumentId,
      onUpdate: (status) {
        if (!mounted) return;
        setState(() => _ocrStatus = status);
        final s = (status ?? '').toLowerCase();
        if (s == 'completed' || s == 'complete') {
          unawaited(_load());
        }
      },
    );
    if (!mounted) return;
    _ocrPolling = false;
    await _load();
  }

  Future<void> _retryOcr() async {
    setState(() => _ocrRetrying = true);
    try {
      await AppState.instance.retryFacultyDocumentOcr(widget.primaryDocumentId);
      await _startOcrPollIfNeeded('pending');
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not restart reading. Try again later.')),
      );
    } finally {
      if (mounted) setState(() => _ocrRetrying = false);
    }
  }

  TextEditingController _ctrlFor(String fieldId) {
    switch (fieldId) {
      case 'outputTitle':
        return _titleCtrl;
      case 'authorsLine':
        return _authorsCtrl;
      case 'outputVenue':
        return _journalCtrl;
      case 'publicationDate':
        return _dateCtrl;
      case 'publicationReference':
        return _doiCtrl;
      default:
        return _titleCtrl;
    }
  }

  void _syncControllers(Map<String, dynamic>? bundle) {
    if (bundle == null) return;
    for (final fieldId in _fieldIds) {
      Kra2OcrSync.syncController(
        controller: _ctrlFor(fieldId),
        fieldId: fieldId,
        bundle: bundle,
        ocrFields: _ocrFields,
        userEditedFields: _userEditedFields,
      );
    }
    final pct = bundle['declaredContributionPercent'];
    if (_percentCtrl.text.isEmpty && pct != null) {
      _percentCtrl.text = pct.toString();
    }
  }

  bool _ocrFieldsIncomplete() {
    for (final fieldId in _fieldIds) {
      if (fieldId == 'publicationReference') continue;
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: _ctrlFor(fieldId).text,
        bundle: _bundle,
        ocrFields: _ocrFields,
      )) {
        return true;
      }
    }
    return false;
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
    for (final fieldId in _fieldIds) {
      if (fieldId == 'publicationReference') continue;
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: _ctrlFor(fieldId).text,
        bundle: _bundle,
        ocrFields: _ocrFields,
      )) {
        if (!mounted) return;
        final ind = (_bundle?['indicatorId'] ?? '').toString();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Please complete ${Kra2Catalog.metadataLabel(fieldId, ind)} before submitting.',
            ),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }
    }
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
    final submission = _validation?['submissionBlockers'];
    final blockers = submission is List && submission.isNotEmpty
        ? submission
        : _validation?['userBlockers'] ?? _validation?['blockers'];
    if (blockers is! List) return const [];
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    return blockers
        .whereType<String>()
        .map((e) => Kra2AUx.humanizeBlocker(e, indicatorId: ind))
        .where((s) => s.isNotEmpty && !s.toLowerCase().contains('verify supporting evidence'))
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
                  Text(
                    Kra2AUx.readingFileLabel(
                      _ocrStatus,
                      extractionIncomplete: canEdit && _ocrFieldsIncomplete(),
                    ),
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  if (_ocrPolling)
                    const Padding(
                      padding: EdgeInsets.only(top: 6),
                      child: LinearProgressIndicator(minHeight: 2),
                    ),
                  if (canEdit &&
                      (_ocrFieldsIncomplete() ||
                          (_ocrStatus ?? '').toLowerCase() == 'failed'))
                    TextButton(
                      onPressed: _ocrRetrying ? null : _retryOcr,
                      child: Text(_ocrRetrying ? 'Reading…' : 'Read my file again'),
                    ),
                  const SizedBox(height: 16),
                  const Text('Publication details', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  const Text('Check each field against your PDF. You can edit anything that looks wrong.'),
                  const SizedBox(height: 12),
                  _field(
                    'Article title',
                    _titleCtrl,
                    enabled: canEdit,
                    helperText: Kra2OcrSync.fieldHelper(
                      fieldId: 'outputTitle',
                      controllerText: _titleCtrl.text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    ),
                    onChanged: canEdit ? (_) => setState(() => _userEditedFields.add('outputTitle')) : null,
                  ),
                  _field(
                    'Author names',
                    _authorsCtrl,
                    enabled: canEdit,
                    helperText: Kra2OcrSync.fieldHelper(
                      fieldId: 'authorsLine',
                      controllerText: _authorsCtrl.text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    ),
                    onChanged: canEdit ? (_) => setState(() => _userEditedFields.add('authorsLine')) : null,
                  ),
                  _field(
                    'Journal or publication name',
                    _journalCtrl,
                    enabled: canEdit,
                    helperText: Kra2OcrSync.fieldHelper(
                      fieldId: 'outputVenue',
                      controllerText: _journalCtrl.text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    ),
                    onChanged: canEdit ? (_) => setState(() => _userEditedFields.add('outputVenue')) : null,
                  ),
                  _field(
                    'Publication date',
                    _dateCtrl,
                    enabled: canEdit,
                    hint: 'e.g. 2025-06-01 or June 2025',
                    helperText: Kra2OcrSync.fieldHelper(
                      fieldId: 'publicationDate',
                      controllerText: _dateCtrl.text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    ),
                    onChanged: canEdit ? (_) => setState(() => _userEditedFields.add('publicationDate')) : null,
                  ),
                  _field(
                    'DOI or reference (optional)',
                    _doiCtrl,
                    enabled: canEdit,
                    helperText: Kra2OcrSync.fieldHelper(
                      fieldId: 'publicationReference',
                      controllerText: _doiCtrl.text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    ),
                    onChanged: canEdit ? (_) => setState(() => _userEditedFields.add('publicationReference')) : null,
                  ),
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
    String? helperText,
    TextInputType? keyboard,
    ValueChanged<String>? onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        enabled: enabled,
        keyboardType: keyboard,
        onChanged: onChanged,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          helperText: helperText,
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
