import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../data/app_auth_exception.dart';
import '../../data/app_state.dart';
import '../../data/kra2_catalog.dart';
import '../../data/kra2_submit_readiness.dart';
import '../../data/kra2_a_ux.dart';
import '../../data/kra2_ocr_sync.dart';
import '../../models/enums.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../documents/document_viewer_screen.dart';

class Kra2ReviewSubmitScreen extends StatefulWidget {
  const Kra2ReviewSubmitScreen({
    super.key,
    required this.primaryDocumentId,
    this.onBackToUpload,
    this.onFinished,
  });

  final String primaryDocumentId;
  final VoidCallback? onBackToUpload;
  final VoidCallback? onFinished;

  @override
  State<Kra2ReviewSubmitScreen> createState() => _Kra2ReviewSubmitScreenState();
}

class _Kra2ReviewSubmitScreenState extends State<Kra2ReviewSubmitScreen> {
  final _controllers = <String, TextEditingController>{};
  Map<String, dynamic>? _bundle;
  Map<String, dynamic>? _validation;
  Map<String, dynamic>? _scoring;
  String? _ocrStatus;
  bool _loading = true;
  bool _saving = false;
  bool _submitting = false;
  String? _error;
  List<String> _fieldIds = const [];
  List<String> _requiredSlotIds = const [];
  Map<String, String> _slotLabels = const {};
  bool _ocrPolling = false;
  Map<String, Map<String, dynamic>> _ocrFields = const {};
  List<String> _ocrReviewFlags = const [];
  final Set<String> _userEditedFields = {};
  bool _ocrRetrying = false;

  @override
  void initState() {
    super.initState();
    unawaited(_load(initial: true));
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  TextEditingController _ctrl(String fieldId) {
    return _controllers.putIfAbsent(fieldId, TextEditingController.new);
  }

  String _fieldLabel(String fieldId) {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    return Kra2Catalog.metadataLabel(fieldId, ind);
  }

  Future<void> _load({bool initial = false}) async {
    if (initial || _bundle == null) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      await AppState.instance.refreshFacultyDocument(widget.primaryDocumentId, quiet: true);
      final payload = await AppState.instance.fetchKra2EvidenceBundle(widget.primaryDocumentId);
      if (!mounted) return;
      final bundle = payload['bundle'] is Map ? Map<String, dynamic>.from(payload['bundle'] as Map) : null;
      final ind = bundle?['indicatorId']?.toString() ?? '';
      _fieldIds = Kra2Catalog.metadataFieldIds(ind);
      final family = Kra2Catalog.workflowFamily(ind);
      if (family == 'publication_output' &&
          !_fieldIds.contains('publicationReference')) {
        _fieldIds = [..._fieldIds, 'publicationReference'];
      }
      final apiSlots = payload['requiredEvidenceSlots'];
      if (apiSlots is List && apiSlots.isNotEmpty) {
        _requiredSlotIds = apiSlots.map((e) => e.toString()).toList();
      } else {
        _requiredSlotIds = Kra2Catalog.requiredEvidenceSlots(ind);
      }
      final labelsRaw = payload['slotLabels'];
      if (labelsRaw is Map) {
        _slotLabels = labelsRaw.map((k, v) => MapEntry(k.toString(), v.toString()));
      } else {
        _slotLabels = {};
      }
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
      if (initial) {
        unawaited(_startOcrPollIfNeeded(ocr));
      }
    } catch (_) {
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
        final st = (status ?? '').toLowerCase();
        if (st == 'completed' || st == 'complete') {
          unawaited(_load());
        }
      },
    );
    if (!mounted) return;
    _ocrPolling = false;
    await _load();
  }

  void _syncControllers(Map<String, dynamic>? bundle) {
    if (bundle == null) return;
    for (final fieldId in _fieldIds) {
      Kra2OcrSync.syncController(
        controller: _ctrl(fieldId),
        fieldId: fieldId,
        bundle: bundle,
        ocrFields: _ocrFields,
        userEditedFields: _userEditedFields,
      );
    }
  }

  String _slotLabel(String slotId, String indicatorId) {
    return _slotLabels[slotId] ?? Kra2Catalog.slotLabelForIndicator(slotId, indicatorId);
  }

  Future<void> _viewDocumentById(String documentId) async {
    if (documentId.isEmpty) return;
    try {
      await AppState.instance.refreshFacultyDocument(documentId, quiet: true);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('We could not load the document. Try again.')),
      );
      return;
    }
    if (!mounted) return;
    final doc = AppState.instance.documentById(documentId);
    if (doc == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Document record not found.')),
      );
      return;
    }
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => DocumentViewerScreen(document: doc)),
    );
  }

  Future<void> _viewPrimaryDocument() async {
    final id = widget.primaryDocumentId;
    try {
      await AppState.instance.refreshFacultyDocument(id, quiet: true);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('We could not load the document. Try again.')),
      );
      return;
    }
    if (!mounted) return;
    final doc = AppState.instance.documentById(id);
    if (doc == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Document record not found.')),
      );
      return;
    }
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => DocumentViewerScreen(document: doc)),
    );
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

  Map<String, dynamic> _metadataBody({required bool submit}) {
    final body = <String, dynamic>{'confirmMetadata': true};
    for (final fieldId in _fieldIds) {
      final raw = _ctrl(fieldId).text.trim();
      if (fieldId == 'declaredContributionPercent') {
        if (raw.isNotEmpty) {
          body[fieldId] = double.tryParse(raw) ?? raw;
        }
        continue;
      }
      if (fieldId == 'publicationReference' && raw.isEmpty) continue;
      body[fieldId] = raw;
      if (fieldId == 'outputVenue') {
        body['journalTitle'] = raw;
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
      if (fieldId == 'declaredContributionPercent' &&
          (_bundle?['contribution']?.toString() ?? '') != 'declared') {
        continue;
      }
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: _ctrl(fieldId).text,
        bundle: _bundle,
        ocrFields: _ocrFields,
      )) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Please complete ${_fieldLabel(fieldId)} before submitting.',
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
        const SnackBar(content: Text('Your work has been sent for review.')),
      );
      widget.onFinished?.call();
      if (widget.onFinished == null) Navigator.of(context).pop(true);
    } on AppAuthException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.message),
          backgroundColor: Colors.red,
        ),
      );
      await _load();
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

  Future<void> _uploadSlot(String slotId, String title) async {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    final criterionId = (_bundle?['criterionId'] ?? Kra2Catalog.criterionA).toString();
    final allowMedia = slotId == 'media_documentation';
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: allowMedia
          ? const ['pdf', 'png', 'jpg', 'jpeg', 'webp', 'mp4', 'mov']
          : const ['pdf'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.first;
    final bytes = file.bytes;
    if (bytes == null) return;
    try {
      await AppState.instance.uploadDocument(
        title: title,
        category: DocumentCategory.researchPublications,
        kra: KraType.research,
        kraWebId: 'kra2',
        criterionId: criterionId,
        indicatorId: ind,
        fileName: file.name,
        fileBytes: bytes,
        bundlePrimaryDocumentId: widget.primaryDocumentId,
        evidenceSlot: slotId,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${_slotLabel(slotId, ind)} uploaded.')),
      );
      await _load();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Upload failed. Try again.'), backgroundColor: Colors.red),
      );
    }
  }

  bool _slotMissing(String slotId) {
    if (slotId == 'primary_output') {
      final entry = _checklistEntry('primary_output');
      final docId = entry?['documentId']?.toString().trim() ?? '';
      if (docId.isNotEmpty) return false;
      return widget.primaryDocumentId.isEmpty;
    }
    final entry = _checklistEntry(slotId);
    if (entry == null) return true;
    final docId = entry['documentId']?.toString().trim() ?? '';
    final st = (entry['status'] ?? 'missing').toString().toLowerCase();
    return docId.isEmpty || st == 'missing';
  }

  bool _slotRejected(String slotId) {
    final entry = _checklistEntry(slotId);
    if (entry == null) return false;
    final st = (entry['status'] ?? '').toString().toLowerCase();
    return st.contains('reject');
  }

  String? _slotDocumentId(String slotId) {
    if (slotId == 'primary_output') {
      final entry = _checklistEntry('primary_output');
      final linked = entry?['documentId']?.toString().trim() ?? '';
      if (linked.isNotEmpty) return linked;
      return widget.primaryDocumentId;
    }
    return _checklistEntry(slotId)?['documentId']?.toString().trim();
  }

  bool get _canSubmitForReview {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    return Kra2SubmitReadiness.canSubmitForReview(
      fieldIds: _fieldIds,
      indicatorId: ind,
      requiredSlotIds: _requiredSlotIds,
      controllerText: (id) => _ctrl(id).text,
      slotMissing: _slotMissing,
      bundle: _bundle,
      ocrFields: _ocrFields,
    );
  }

  List<String> _uiBlockers({required bool canEdit}) {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    if (canEdit) {
      return Kra2SubmitReadiness.localBlockers(
        fieldIds: _fieldIds,
        indicatorId: ind,
        requiredSlotIds: _requiredSlotIds,
        controllerText: (id) => _ctrl(id).text,
        fieldLabel: _fieldLabel,
        slotLabel: (slotId) => _slotLabel(slotId, ind),
        slotMissing: _slotMissing,
        bundle: _bundle,
        ocrFields: _ocrFields,
      );
    }
    return _friendlyBlockers();
  }

  Map<String, dynamic>? _checklistEntry(String slotId) {
    final checklist = _bundle?['checklist'];
    if (checklist is! Map) return null;
    final entry = checklist[slotId];
    return entry is Map ? Map<String, dynamic>.from(entry) : null;
  }

  String? _documentMismatchHint(String indicatorId) {
    if (indicatorId.isEmpty) return null;
    final doc = AppState.instance.documentById(widget.primaryDocumentId);
    final name = doc?.fileName ?? doc?.title ?? '';
    return Kra2Catalog.documentTypeMismatchHint(indicatorId, name);
  }

  List<String> _friendlyBlockers() {
    final submission = _validation?['submissionBlockers'];
    final blockers = submission is List && submission.isNotEmpty
        ? submission
        : _validation?['userBlockers'] ?? _validation?['blockers'];
    if (blockers is! List) return const [];
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    final seen = <String>{};
    final out = <String>[];
    for (final raw in blockers) {
      final m = Kra2AUx.humanizeBlocker(raw.toString(), indicatorId: ind);
      if (m.toLowerCase().contains('verify supporting evidence')) continue;
      if (seen.add(m)) out.add(m);
    }
    return out;
  }

  bool _showOcrIncompleteBanner(bool canEdit) {
    if (!canEdit) return false;
    final st = (_ocrStatus ?? '').toLowerCase();
    if (st != 'completed' && st != 'complete' && st != 'failed') return false;
    for (final fieldId in _fieldIds) {
      if (fieldId == 'publicationReference') continue;
      if (fieldId == 'declaredContributionPercent' &&
          Kra2Catalog.contributionMode((_bundle?['indicatorId'] ?? '').toString()) != 'declared') {
        continue;
      }
      if (!Kra2OcrSync.fieldHasValue(
        fieldId: fieldId,
        controllerText: _ctrl(fieldId).text,
        bundle: _bundle,
        ocrFields: _ocrFields,
      )) {
        return true;
      }
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    final ind = (_bundle?['indicatorId'] ?? '').toString();
    final submitted = (_bundle?['submittedForReviewAt'] ?? '').toString().isNotEmpty;
    final facultyStatus = Kra2AUx.facultyStatus(
      reviewStatus: _bundle?['reviewStatus']?.toString(),
      validationStatus: _validation?['status']?.toString(),
      submittedForReview: submitted,
    );
    final est = (_scoring?['estimatedPoints'] as num?)?.toDouble();
    final assessed = (_scoring?['reviewerAssessedPoints'] as num?)?.toDouble();
    final canEdit = facultyStatus == Kra2FacultyStatus.draft ||
        facultyStatus == Kra2FacultyStatus.needsChanges;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Check your work'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: _loading && _bundle == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () => _load(),
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  const Text(
                    'Please check if these details are correct.',
                    style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                  ),
                  const SizedBox(height: 12),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(_error!, style: const TextStyle(color: Colors.red)),
                    ),
                  if (ind.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Text(
                        Kra2Catalog.accomplishmentGroupTitle(ind),
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                      ),
                    ),
                  _StatusChip(
                    label: Kra2AUx.statusLabel(facultyStatus),
                    explanation: Kra2AUx.statusExplanation(facultyStatus),
                    nextAction: Kra2AUx.statusNextAction(facultyStatus),
                    points: Kra2AUx.pointsLine(
                      status: facultyStatus,
                      estimatedPoints: est,
                      reviewerAssessedPoints: assessed,
                    ),
                    pointsFootnote: Kra2AUx.pointsFootnote(facultyStatus),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    Kra2AUx.readingFileLabel(
                      _ocrStatus,
                      extractionIncomplete: _showOcrIncompleteBanner(canEdit),
                    ),
                    style: TextStyle(color: Colors.grey.shade700),
                  ),
                  if (_documentMismatchHint(ind) != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          _documentMismatchHint(ind)!,
                          style: const TextStyle(height: 1.35),
                        ),
                      ),
                    ),
                  if (_ocrPolling)
                    const Padding(
                      padding: EdgeInsets.only(top: 6),
                      child: LinearProgressIndicator(minHeight: 2),
                    ),
                  if (_showOcrIncompleteBanner(canEdit))
                    Container(
                      margin: const EdgeInsets.only(top: 8, bottom: 4),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.blue.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'We couldn\'t read some details from your document.',
                            style: TextStyle(fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'You can try reading again or enter the missing information below.',
                            style: TextStyle(color: AppColors.textSecondary, height: 1.35),
                          ),
                          TextButton(
                            onPressed: _ocrRetrying ? null : _retryOcr,
                            child: Text(_ocrRetrying ? 'Reading…' : 'Read my file again'),
                          ),
                        ],
                      ),
                    )
                  else if ((_ocrStatus ?? '').toLowerCase() == 'failed' && canEdit)
                    TextButton(
                      onPressed: _ocrRetrying ? null : _retryOcr,
                      child: Text(_ocrRetrying ? 'Reading…' : 'Read my file again'),
                    ),
                  const SizedBox(height: 16),
                  const Text('Your details', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  ..._fieldIds.map((fieldId) {
                    TextInputType? keyboard;
                    if (fieldId == 'declaredContributionPercent') {
                      keyboard = TextInputType.number;
                    }
                    final helper = Kra2OcrSync.fieldHelper(
                      fieldId: fieldId,
                      controllerText: _ctrl(fieldId).text,
                      ocrFields: _ocrFields,
                      bundle: _bundle,
                      userEditedFields: _userEditedFields,
                      reviewFlags: _ocrReviewFlags,
                    );
                    return _field(
                      _fieldLabel(fieldId),
                      _ctrl(fieldId),
                      enabled: canEdit,
                      keyboard: keyboard,
                      hint: fieldId.contains('Date') ? 'e.g. 2025-06-01 or June 2025' : null,
                      helperText: helper,
                      onChanged: canEdit
                          ? (_) => setState(() => _userEditedFields.add(fieldId))
                          : null,
                    );
                  }),
                  const SizedBox(height: 16),
                  const Text('Required documents', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
                  const SizedBox(height: 4),
                  Text(
                    'Add each item below. Your reviewer checks them after you send for review.',
                    style: TextStyle(color: Colors.grey.shade700, height: 1.35),
                  ),
                  const SizedBox(height: 8),
                  ..._requiredSlotIds.map((slotId) {
                    final missing = _slotMissing(slotId);
                    final rejected = _slotRejected(slotId);
                    final entry = _checklistEntry(slotId);
                    final label = _slotLabel(slotId, ind);
                    final subtitle = rejected
                        ? 'Rejected — upload a corrected document'
                        : Kra2Catalog.facultySlotStatusSubtitle(slotId, entry);
                    final docId = _slotDocumentId(slotId) ?? '';
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(
                        slotId == 'media_documentation' ? Icons.perm_media : Icons.description,
                        color: missing || rejected ? Colors.orange : AppColors.navy,
                      ),
                      title: Text(label),
                      subtitle: Text(subtitle),
                      trailing: canEdit
                          ? Wrap(
                              spacing: 4,
                              children: [
                                if (!missing && docId.isNotEmpty)
                                  TextButton(
                                    onPressed: () => _viewDocumentById(docId),
                                    child: const Text('View'),
                                  ),
                                TextButton(
                                  onPressed: () => _uploadSlot(
                                    slotId,
                                    label,
                                  ),
                                  child: Text(missing ? 'Upload' : 'Replace'),
                                ),
                              ],
                            )
                          : (!missing && docId.isNotEmpty
                              ? TextButton(
                                  onPressed: () => _viewDocumentById(docId),
                                  child: const Text('View'),
                                )
                              : null),
                    );
                  }),
                  if (_uiBlockers(canEdit: canEdit).isNotEmpty) ...[
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
                          const Text('Before you send', style: TextStyle(fontWeight: FontWeight.w600)),
                          ..._uiBlockers(canEdit: canEdit).map(
                            (b) => Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text('• $b'),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  if (canEdit) ...[
                    PrimaryButton(
                      label: _submitting ? 'Sending…' : 'Send for Review',
                      icon: Icons.send,
                      loading: _submitting,
                      onPressed: (_submitting || !_canSubmitForReview) ? null : _submit,
                    ),
                    if (!_canSubmitForReview && _uiBlockers(canEdit: canEdit).isEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          'Upload each required document and complete the details above before sending.',
                          style: TextStyle(color: Colors.grey.shade700, height: 1.35),
                        ),
                      ),
                    const SizedBox(height: 10),
                    OutlinedButton(
                      onPressed: _saving ? null : _saveDraft,
                      child: Text(_saving ? 'Saving…' : 'Save for Later'),
                    ),
                    if (widget.onBackToUpload != null) ...[
                      const SizedBox(height: 8),
                      TextButton(onPressed: widget.onBackToUpload, child: const Text('Edit details')),
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
        onChanged: onChanged,
        keyboardType: keyboard,
        inputFormatters: keyboard == TextInputType.number
            ? [FilteringTextInputFormatter.allow(RegExp(r'[\d.]'))]
            : null,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          helperText: helperText,
          helperMaxLines: 2,
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
    required this.nextAction,
    required this.points,
    required this.pointsFootnote,
  });

  final String label;
  final String explanation;
  final String nextAction;
  final String points;
  final String pointsFootnote;

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
            const SizedBox(height: 4),
            Text(nextAction, style: TextStyle(color: Colors.grey.shade700, fontSize: 13)),
            if (points.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(points, style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
            if (pointsFootnote.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(pointsFootnote, style: TextStyle(color: Colors.grey.shade700, fontSize: 13)),
            ],
          ],
        ),
      ),
    );
  }
}
