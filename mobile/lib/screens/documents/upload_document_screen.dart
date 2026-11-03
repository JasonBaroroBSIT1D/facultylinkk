import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../data/app_state.dart';
import '../../data/criterion_b_bulk_upload.dart';
import '../../data/criterion_b_catalog.dart';
import '../../data/criterion_c_bulk_upload.dart';
import '../../data/criterion_c_catalog.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../data/mock_kra_catalog.dart';
import '../../theme/app_colors.dart';
import '../../utils/title_from_filename.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';

import '../criterion_b/criterion_b_track_screen.dart';
import '../criterion_b/criterion_b_upload_requirements_screen.dart';
import '../criterion_c/criterion_c_track_screen.dart';
import '../criterion_c/criterion_c_upload_requirements_screen.dart';
import 'document_flow_args.dart';

class UploadDocumentScreen extends StatefulWidget {
  const UploadDocumentScreen({
    super.key,
    this.initialKra,
    this.initialCriterionId,
    this.initialIndicatorId,
    this.bundlePrimaryDocumentId,
    this.evidenceSlot,
    this.criterionBPrimaryFlow = false,
    this.criterionBDraft,
    this.criterionCPrimaryFlow = false,
    this.criterionCOcrFirstResearch = false,
    this.criterionCDraft,
  });

  factory UploadDocumentScreen.fromArguments(Object? arguments) {
    if (arguments is UploadDocumentLaunch) {
      return UploadDocumentScreen(
        initialKra: arguments.kra,
        initialCriterionId: arguments.criterionId,
        initialIndicatorId: arguments.indicatorId,
        bundlePrimaryDocumentId: arguments.bundlePrimaryDocumentId,
        evidenceSlot: arguments.evidenceSlot,
        criterionBPrimaryFlow: arguments.criterionBPrimaryFlow,
        criterionBDraft: arguments.criterionBDraft,
        criterionCPrimaryFlow: arguments.criterionCPrimaryFlow,
        criterionCOcrFirstResearch: arguments.criterionCOcrFirstResearch,
        criterionCDraft: arguments.criterionCDraft,
      );
    }
    if (arguments is KraType) {
      return UploadDocumentScreen(initialKra: arguments);
    }
    return const UploadDocumentScreen();
  }

  final KraType? initialKra;
  final String? initialCriterionId;
  final String? initialIndicatorId;
  final String? bundlePrimaryDocumentId;
  final String? evidenceSlot;
  final bool criterionBPrimaryFlow;
  final CriterionBAddWorkDraft? criterionBDraft;
  final bool criterionCPrimaryFlow;
  final bool criterionCOcrFirstResearch;
  final CriterionCAddWorkDraft? criterionCDraft;

  @override
  State<UploadDocumentScreen> createState() => _UploadDocumentScreenState();
}

class _PendingUpload {
  const _PendingUpload({
    required this.fileName,
    required this.bytes,
    required this.fromCamera,
  });

  final String fileName;
  final List<int> bytes;
  final bool fromCamera;

  int get size => bytes.length;

  String get title => titleFromFilename(fileName);
}

class _UploadDocumentScreenState extends State<UploadDocumentScreen> {
  final _formKey = GlobalKey<FormState>();
  List<Map<String, dynamic>> _kras = [];
  String? _webKraId;
  String? _criterionId;
  String? _indicatorId;
  final List<_PendingUpload> _files = [];
  bool _loadingCatalog = true;
  double _progress = 0;
  String _progressLabel = '';
  _UploadPhase _phase = _UploadPhase.form;
  int _uploadedCount = 0;
  List<String?> _slotAssignments = [];
  bool _savedAllBulkSlots = false;
  String? _contributionPercentText;
  bool? _completeSetDeclared;
  bool _completeSetDeclaredTouched = false;
  String? _programDevelopmentKind;
  String? _contributionDescription;
  String? _committeeName;
  String? _materialTitleOverride;
  String? _programNameOverride;
  String? _createdPrimaryDocumentId;

  bool get _isSupportingUpload =>
      widget.bundlePrimaryDocumentId != null && widget.evidenceSlot != null;

  bool get _isCriterionBPrimary =>
      !_isSupportingUpload &&
      _criterionId == CriterionBCatalog.criterionId &&
      _indicatorId != null;

  bool get _isCriterionCPrimary =>
      !_isSupportingUpload &&
      _criterionId == CriterionCCatalog.criterionId &&
      _indicatorId != null;

  bool get _guidedCriterionBPrimaryUpload =>
      widget.criterionBPrimaryFlow && _isCriterionBPrimary;

  bool get _guidedCriterionCPrimaryUpload =>
      widget.criterionCPrimaryFlow && _isCriterionCPrimary;

  bool get _guidedPrimaryUpload =>
      _guidedCriterionBPrimaryUpload || _guidedCriterionCPrimaryUpload;

  bool get _criterionCMentorshipPrimary =>
      _guidedCriterionCPrimaryUpload && (widget.criterionCDraft?.isMentorship == true);

  bool get _needsCompleteSetForIndicator =>
      _indicatorId != null &&
      (_indicatorId!.contains('module') || _indicatorId!.contains('manual'));

  /// Hide when the add-work wizard already captured the faculty declaration.
  bool get _showCompleteSetOnUploadForm =>
      _isCriterionBPrimary &&
      _needsCompleteSetForIndicator &&
      !(_guidedPrimaryUpload && widget.criterionBDraft?.completeSetDeclared != null);

  @override
  void initState() {
    super.initState();
    _criterionId = widget.initialCriterionId;
    _indicatorId = widget.initialCriterionId == FacultyDocument.criterionAId
        ? null
        : widget.initialIndicatorId;
    final draft = widget.criterionBDraft;
    if (draft != null) {
      _materialTitleOverride = draft.materialTitle;
      _programNameOverride = draft.programName;
      _programDevelopmentKind = draft.programDevelopmentKind;
      _contributionDescription = draft.contributionDescription;
      _committeeName = draft.committeeName;
      _completeSetDeclared = draft.completeSetDeclared;
      if (draft.contributionPercent != null) {
        _contributionPercentText = '${draft.contributionPercent}';
      }
    }
    _loadCatalog();
  }

  static const _maxBytes = 16 * 1024 * 1024;
  static const _allowedExtensions = [
    'pdf',
    'png',
    'jpg',
    'jpeg',
    'webp',
    'doc',
    'docx',
    'tif',
    'tiff',
    'bmp',
  ];

  KraType get _mobileKra {
    final match = _kras.cast<Map<String, dynamic>?>().firstWhere(
          (k) => k?['id'] == _webKraId,
          orElse: () => null,
        );
    final key = match?['mobileKey']?.toString();
    return KraType.values.firstWhere(
      (k) => k.name == key,
      orElse: () => widget.initialKra ?? KraType.instruction,
    );
  }

  List<Map<String, dynamic>> get _indicators {
    final criterion = _criteria.cast<Map<String, dynamic>?>().firstWhere(
          (c) => c?['id'] == _criterionId,
          orElse: () => null,
        );
    final list = criterion?['indicators'];
    if (list is! List) return [];
    return list.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  List<Map<String, dynamic>> get _criteria {
    final kra = _kras.cast<Map<String, dynamic>?>().firstWhere(
          (k) => k?['id'] == _webKraId,
          orElse: () => null,
        );
    final list = kra?['criteria'];
    if (list is! List) return [];
    return list.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Future<void> _loadCatalog() async {
    try {
      final data = await MockKraCatalog.load();
      final raw = data['kras'];
      final list = raw is List
          ? raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
          : <Map<String, dynamic>>[];
      String? initialWeb;
      if (widget.initialKra != null) {
        initialWeb = list
            .cast<Map<String, dynamic>?>()
            .firstWhere(
              (k) => k?['mobileKey'] == widget.initialKra!.name,
              orElse: () => null,
            )?['id']
            ?.toString();
      }
      if (!mounted) return;
      setState(() {
        _kras = list;
        _webKraId = initialWeb ?? (list.isNotEmpty ? list.first['id']?.toString() : null);
        _criterionId = widget.initialCriterionId;
        _indicatorId = widget.initialCriterionId == FacultyDocument.criterionAId
            ? null
            : widget.initialIndicatorId;
        if (_isSupportingUpload) {
          _webKraId = 'kra1';
          final primary = AppState.instance.documentById(widget.bundlePrimaryDocumentId!);
          _criterionId = primary?.criterionId ?? CriterionBCatalog.criterionId;
          _indicatorId = primary?.indicatorId ?? _indicatorId;
        }
        _loadingCatalog = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loadingCatalog = false);
      showAppSnackBar(
        context,
        'Could not load the KRA catalog asset.',
        error: true,
      );
    }
  }

  Future<void> _pickCamera() async {
    try {
      final shot = await ImagePicker().pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
      );
      if (shot == null) return;
      final bytes = await shot.readAsBytes();
      if (!mounted) return;
      final name = shot.name.isNotEmpty
          ? shot.name
          : 'scan_${DateTime.now().millisecondsSinceEpoch}.jpg';
      _addFiles([
        _PendingUpload(fileName: name, bytes: bytes, fromCamera: true),
      ]);
    } catch (_) {
      if (!mounted) return;
      showAppSnackBar(
        context,
        'Camera is unavailable. Allow camera permission, or choose a file instead.',
        error: true,
      );
    }
  }

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        withData: true,
        allowMultiple: true,
        // Browser/Windows combinations can fail to return a file when the
        // native dialog uses a long custom-extension filter. On web, accept
        // the selection first and validate its extension below.
        type: kIsWeb ? FileType.any : FileType.custom,
        allowedExtensions: kIsWeb ? null : _allowedExtensions,
      );
      if (result == null) return;
      if (result.files.isEmpty) {
        if (!mounted) return;
        showAppSnackBar(context, 'No files were selected.', error: true);
        return;
      }

      final pending = <_PendingUpload>[];
      final unreadable = <String>[];
      for (final file in result.files) {
        final bytes = file.bytes;
        if (bytes == null) {
          unreadable.add(file.name);
          continue;
        }
        pending.add(
          _PendingUpload(
            fileName: file.name,
            bytes: bytes,
            fromCamera: false,
          ),
        );
      }
      if (!mounted) return;
      _addFiles(pending);
      if (unreadable.isNotEmpty) {
        showAppSnackBar(
          context,
          'Could not read: ${unreadable.take(3).join(', ')}. Make sure the file is available offline, then try again.',
          error: true,
        );
      }
    } catch (error) {
      if (!mounted) return;
      showAppSnackBar(
        context,
        'Could not open the selected file. Make sure it is available offline, then try again. ($error)',
        error: true,
      );
    }
  }

  void _addFiles(List<_PendingUpload> incoming) {
    if (incoming.isEmpty) return;
    final rejected = <String>[];
    final accepted = <_PendingUpload>[];
    final existing = {for (final f in _files) f.fileName.toLowerCase()};

    for (final file in incoming) {
      final dot = file.fileName.lastIndexOf('.');
      final extension = dot < 0
          ? ''
          : file.fileName.substring(dot + 1).toLowerCase();
      if (!_allowedExtensions.contains(extension)) {
        rejected.add('${file.fileName} (unsupported file type)');
        continue;
      }
      if (file.size > _maxBytes) {
        rejected.add('${file.fileName} (over 16 MB)');
        continue;
      }
      if (existing.contains(file.fileName.toLowerCase())) {
        rejected.add('${file.fileName} (already selected)');
        continue;
      }
      existing.add(file.fileName.toLowerCase());
      accepted.add(file);
    }

    setState(() => _files.addAll(accepted));
    if (rejected.isNotEmpty && mounted) {
      showAppSnackBar(
        context,
        'Skipped: ${rejected.take(3).join(', ')}${rejected.length > 3 ? '…' : ''}',
        error: true,
      );
    }
  }

  void _initSlotAssignments() {
    if (_guidedCriterionCPrimaryUpload) {
      final mentorship = _criterionCMentorshipPrimary;
      final allowed = CriterionCBulkUpload.assignableSlots(mentorship: mentorship);
      _slotAssignments = List.generate(_files.length, (i) {
        return CriterionCBulkUpload.suggestSlotFromFileName(
          _files[i].fileName,
          allowedSlots: allowed,
        );
      });
      final primary = CriterionCBulkUpload.primarySlot(mentorship: mentorship);
      if (_files.length == 1 && (_slotAssignments[0] == null || _slotAssignments[0]!.isEmpty)) {
        _slotAssignments[0] = primary;
      }
      return;
    }
    final allowed = CriterionBBulkUpload.assignableSlots(
      draft: widget.criterionBDraft,
      indicatorId: _indicatorId,
    );
    _slotAssignments = List.generate(_files.length, (i) {
      return CriterionBBulkUpload.suggestSlotFromFileName(
        _files[i].fileName,
        allowedSlots: allowed,
      );
    });
    final primary = widget.criterionBDraft?.isProgram == true
        ? CriterionBBulkUpload.primaryProgramSlot
        : CriterionBBulkUpload.primaryImSlot;
    if (_files.length == 1 && (_slotAssignments[0] == null || _slotAssignments[0]!.isEmpty)) {
      _slotAssignments[0] = primary;
    }
  }

  void _onUploadPressed() {
    if (!_formKey.currentState!.validate()) return;
    if (_files.isEmpty) {
      showAppSnackBar(context, 'Select or scan at least one file first.', error: true);
      return;
    }
    if (_guidedPrimaryUpload && _files.length > 1 && _phase == _UploadPhase.form) {
      _initSlotAssignments();
      setState(() => _phase = _UploadPhase.assign);
      return;
    }
    _submit();
  }

  Future<void> _submit() async {
    if (_phase == _UploadPhase.assign) {
      final String? err;
      if (_guidedCriterionCPrimaryUpload) {
        err = CriterionCBulkUpload.validateAssignments(
          _slotAssignments,
          mentorship: _criterionCMentorshipPrimary,
        );
      } else {
        final program = widget.criterionBDraft?.isProgram == true;
        err = CriterionBBulkUpload.validateAssignments(_slotAssignments, program: program);
      }
      if (err != null) {
        showAppSnackBar(context, err, error: true);
        return;
      }
    } else {
      if (!_formKey.currentState!.validate()) return;
      if (_files.isEmpty) {
        showAppSnackBar(context, 'Select or scan at least one file first.', error: true);
        return;
      }
    }
    if (_isSupportingUpload && _files.length > 1) {
      showAppSnackBar(context, 'Upload one supporting file at a time for an evidence slot.', error: true);
      return;
    }
    final criterionAAuto = _criterionId == FacultyDocument.criterionAId;
    if (_webKraId == null || _criterionId == null || (!criterionAAuto && _indicatorId == null)) {
      showAppSnackBar(
        context,
        criterionAAuto
            ? 'Select a KRA and criterion.'
            : 'Select a KRA, criterion, and indicator.',
        error: true,
      );
      return;
    }
    final total = _files.length;
    setState(() {
      _phase = _UploadPhase.processing;
      _progress = 0.05;
      _progressLabel = 'Uploading 1 of $total…';
      _uploadedCount = 0;
      _savedAllBulkSlots = false;
    });

    try {
      if (_guidedCriterionCPrimaryUpload && total > 1) {
        await _submitGuidedBulkCriterionC(total);
      } else if (_guidedCriterionBPrimaryUpload && total > 1) {
        await _submitGuidedBulk(total);
      } else {
        await _submitSequential(total, criterionAAuto);
      }
      if (!mounted) return;
      await AppState.instance.refreshData(label: 'Refreshing documents...', soft: true);
      if (!mounted) return;
      setState(() {
        _progress = 1;
        _phase = _UploadPhase.success;
        _savedAllBulkSlots = _guidedPrimaryUpload && total > 1;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _phase = _uploadedCount > 0 && _guidedPrimaryUpload
            ? _UploadPhase.assign
            : _UploadPhase.form;
      });
      final prefix = _uploadedCount > 0
          ? 'Uploaded $_uploadedCount of $total, then failed: '
          : '';
      showAppSnackBar(context, '$prefix$error', error: true);
    }
  }

  Future<void> _submitSequential(int total, bool criterionAAuto) async {
    String? evidencePackageId;
    for (var i = 0; i < total; i++) {
      final file = _files[i];
      if (!mounted) return;
      setState(() {
        _progress = (i / total).clamp(0.05, 0.95);
        _progressLabel = 'Uploading ${i + 1} of $total…';
      });
      evidencePackageId = await AppState.instance.uploadDocument(
        title: file.title,
        category: DocumentCategory.supportingEvidence,
        kra: _mobileKra,
        kraWebId: _webKraId,
        fileName: file.fileName,
        criterionId: _criterionId,
        indicatorId: criterionAAuto ? null : _indicatorId,
        packageId: evidencePackageId,
        requirementIndex: total > 1 && !_guidedPrimaryUpload ? i : null,
        fileBytes: file.bytes,
        bundlePrimaryDocumentId: widget.bundlePrimaryDocumentId,
        evidenceSlot: widget.evidenceSlot,
      );
      if (_isCriterionBPrimary &&
          !AppState.instance.usesMockAuth &&
          evidencePackageId != null &&
          i == 0) {
        _createdPrimaryDocumentId = evidencePackageId;
        await _patchCriterionBMetadata(evidencePackageId, file.title);
      }
      if (_isCriterionCPrimary &&
          !AppState.instance.usesMockAuth &&
          evidencePackageId != null &&
          i == 0) {
        _createdPrimaryDocumentId = evidencePackageId;
        await _patchCriterionCMetadata(evidencePackageId, file.title);
      }
      _uploadedCount = i + 1;
    }
  }

  Future<void> _submitGuidedBulkCriterionC(int total) async {
    final mentorship = _criterionCMentorshipPrimary;
    final primarySlot = CriterionCBulkUpload.primarySlot(mentorship: mentorship);
    final primaryFileIndex = mentorship
        ? _slotAssignments.indexWhere((s) => s == primarySlot)
        : _slotAssignments.indexWhere((s) => s == CriterionCBulkUpload.approvalSheetSlot);
    final order = List.generate(total, (i) => i);
    order.sort((a, b) {
      if (a == primaryFileIndex) return -1;
      if (b == primaryFileIndex) return 1;
      return a.compareTo(b);
    });
    String? primaryId;
    for (var step = 0; step < order.length; step++) {
      final i = order[step];
      final file = _files[i];
      final slot = _slotAssignments[i]!;
      if (!mounted) return;
      setState(() {
        _progress = (step / total).clamp(0.05, 0.95);
        _progressLabel = 'Uploading ${step + 1} of $total…';
      });
      final isPrimaryDoc = primaryId == null &&
          (i == primaryFileIndex || (mentorship && primaryFileIndex < 0 && step == 0));
      final docId = await AppState.instance.uploadDocument(
        title: file.title,
        category: DocumentCategory.supportingEvidence,
        kra: _mobileKra,
        kraWebId: _webKraId,
        fileName: file.fileName,
        criterionId: _criterionId,
        indicatorId: _indicatorId,
        fileBytes: file.bytes,
        bundlePrimaryDocumentId: isPrimaryDoc ? null : primaryId,
        evidenceSlot: isPrimaryDoc ? null : slot,
      );
      if (isPrimaryDoc) {
        primaryId = docId;
        _createdPrimaryDocumentId = docId;
        if (!AppState.instance.usesMockAuth && docId != null) {
          await _patchCriterionCMetadata(docId, file.title);
        }
      }
      _uploadedCount = step + 1;
    }
  }

  Future<void> _submitGuidedBulk(int total) async {
    final program = widget.criterionBDraft?.isProgram == true;
    final primarySlot = program
        ? CriterionBBulkUpload.primaryProgramSlot
        : CriterionBBulkUpload.primaryImSlot;
    final order = List.generate(total, (i) => i);
    order.sort((a, b) {
      final sa = _slotAssignments[a];
      final sb = _slotAssignments[b];
      if (sa == primarySlot) return -1;
      if (sb == primarySlot) return 1;
      return a.compareTo(b);
    });
    String? primaryId;
    for (var step = 0; step < order.length; step++) {
      final i = order[step];
      final file = _files[i];
      final slot = _slotAssignments[i]!;
      if (!mounted) return;
      setState(() {
        _progress = (step / total).clamp(0.05, 0.95);
        _progressLabel = 'Uploading ${step + 1} of $total…';
      });
      final isPrimary = slot == primarySlot;
      final docId = await AppState.instance.uploadDocument(
        title: file.title,
        category: DocumentCategory.supportingEvidence,
        kra: _mobileKra,
        kraWebId: _webKraId,
        fileName: file.fileName,
        criterionId: _criterionId,
        indicatorId: _indicatorId,
        fileBytes: file.bytes,
        bundlePrimaryDocumentId: isPrimary ? null : primaryId,
        evidenceSlot: isPrimary ? null : slot,
      );
      if (isPrimary) {
        primaryId = docId;
        _createdPrimaryDocumentId = docId;
        if (!AppState.instance.usesMockAuth && docId != null) {
          await _patchCriterionBMetadata(docId, file.title);
        }
      }
      _uploadedCount = step + 1;
    }
  }

  Future<void> _patchCriterionCMetadata(String documentId, String defaultTitle) async {
    final draft = widget.criterionCDraft;
    if (draft == null) return;
    if (draft.ocrFirstResearch && !draft.isMentorship) {
      return;
    }
    final body = <String, dynamic>{
      'projectTitle': (draft.projectTitle?.trim().isNotEmpty == true)
          ? draft.projectTitle!.trim()
          : defaultTitle,
    };
    if (draft.studentNames?.trim().isNotEmpty == true) {
      body['studentNames'] = draft.studentNames!.trim();
    }
    if (draft.studentGroupLabel?.trim().isNotEmpty == true) {
      body['studentGroupLabel'] = draft.studentGroupLabel!.trim();
    }
    if (draft.academicYear?.trim().isNotEmpty == true) {
      body['academicYear'] = draft.academicYear!.trim();
    }
    if (draft.completionDate?.trim().isNotEmpty == true) {
      body['completionDate'] = draft.completionDate!.trim();
    }
    if (draft.isMentorship) {
      body['mentorship'] = {
        if (draft.competitionName?.trim().isNotEmpty == true)
          'competitionName': draft.competitionName!.trim(),
        if (draft.prizeLevel?.trim().isNotEmpty == true) 'prizeLevel': draft.prizeLevel!.trim(),
        if (draft.prizePlacement?.trim().isNotEmpty == true)
          'prizePlacement': draft.prizePlacement!.trim(),
      };
    }
    try {
      await AppState.instance.patchCriterionCEvidenceBundle(documentId, body);
    } catch (error) {
      if (mounted) {
        showAppSnackBar(
          context,
          'Upload saved, but accomplishment details could not be updated: $error',
          error: true,
        );
      }
    }
  }

  Future<void> _patchCriterionBMetadata(String documentId, String defaultTitle) async {
    final body = <String, dynamic>{};
    final draft = widget.criterionBDraft;
    if (draft != null) {
      if (draft.isProgram) {
        body['programName'] = draft.programName?.trim().isNotEmpty == true
            ? draft.programName!.trim()
            : defaultTitle;
        if (draft.programDevelopmentKind != null) {
          body['programDevelopmentKind'] = draft.programDevelopmentKind;
        }
        if (draft.contributionDescription?.trim().isNotEmpty == true) {
          body['contributionDescription'] = draft.contributionDescription!.trim();
        }
        if (draft.committeeName?.trim().isNotEmpty == true) {
          body['committeeName'] = draft.committeeName!.trim();
        }
      } else {
        body['materialTitle'] = draft.materialTitle?.trim().isNotEmpty == true
            ? draft.materialTitle!.trim()
            : defaultTitle;
        if (draft.materialType != null) body['materialType'] = draft.materialType;
        if (draft.contributionPercent != null) {
          body['contributionPercent'] = draft.contributionPercent;
        }
        if (draft.completeSetDeclared != null) {
          body['completeSetDeclared'] = draft.completeSetDeclared;
        }
      }
    } else if (CriterionBCatalog.isProgramIndicator(_indicatorId)) {
      body['programName'] = (_programNameOverride?.trim().isNotEmpty == true)
          ? _programNameOverride!.trim()
          : defaultTitle;
      if (_programDevelopmentKind != null) {
        body['programDevelopmentKind'] = _programDevelopmentKind;
      }
      if (_contributionDescription?.trim().isNotEmpty == true) {
        body['contributionDescription'] = _contributionDescription!.trim();
      }
      if (_committeeName?.trim().isNotEmpty == true) {
        body['committeeName'] = _committeeName!.trim();
      }
    } else {
      body['materialTitle'] = (_materialTitleOverride?.trim().isNotEmpty == true)
          ? _materialTitleOverride!.trim()
          : defaultTitle;
      if (CriterionBCatalog.isCoAuthorIndicator(_indicatorId) &&
          _contributionPercentText?.trim().isNotEmpty == true) {
        body['contributionPercent'] = double.tryParse(_contributionPercentText!.trim());
      }
      if (_completeSetDeclaredTouched) {
        body['completeSetDeclared'] = _completeSetDeclared ?? false;
      }
    }
    if (body.isEmpty) return;
    try {
      await AppState.instance.patchCriterionBEvidenceBundle(documentId, body);
    } catch (error) {
      if (mounted) {
        showAppSnackBar(
          context,
          'Upload saved, but claim details could not be updated: $error',
          error: true,
        );
      }
    }
  }

  String _sizeLabel(int bytes) {
    if (bytes < 1024) return '$bytes B';
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }

  void _onUploadSuccessDone() {
    final id = _createdPrimaryDocumentId;
    if (_guidedPrimaryUpload && id != null) {
      if (widget.criterionCPrimaryFlow) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => CriterionCUploadRequirementsScreen(primaryDocumentId: id),
          ),
        );
        return;
      }
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => _savedAllBulkSlots
              ? CriterionBTrackScreen(primaryDocumentId: id)
              : CriterionBUploadRequirementsScreen(primaryDocumentId: id),
        ),
      );
      return;
    }
    Navigator.pop(context);
  }

  void _resetFormKeepSelection() {
    setState(() {
      _phase = _UploadPhase.form;
      _files.clear();
      _progress = 0;
      _progressLabel = '';
      _uploadedCount = 0;
      _slotAssignments = [];
      _savedAllBulkSlots = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_files.length > 1 ? 'Upload documents' : 'Upload document'),
      ),
      body: switch (_phase) {
        _UploadPhase.form => _loadingCatalog
            ? const LoadingState(message: 'Loading KRA catalog…')
            : _buildForm(),
        _UploadPhase.assign => _buildAssignForm(),
        _UploadPhase.processing => Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                LinearProgressIndicator(value: _progress.clamp(0.05, 1)),
                const SizedBox(height: 18),
                Text(
                  _progressLabel,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Each file is saved under the selected KRA and criterion. Successful uploads are submitted for reviewer validation automatically. Text extraction (OCR) runs on the server in the background.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary, height: 1.45),
                ),
              ],
            ),
          ),
        _UploadPhase.success => _SuccessView(
            count: _uploadedCount,
            onDone: _onUploadSuccessDone,
            onUploadAnother: _resetFormKeepSelection,
          ),
      },
    );
  }

  Widget _buildCriterionBMetadataFields() {
    if (CriterionBCatalog.isProgramIndicator(_indicatorId)) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Academic program claim details',
            style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
          ),
          const SizedBox(height: 8),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Program name (optional override)'),
            onChanged: (v) => _programNameOverride = v,
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(labelText: 'Development type'),
            items: const [
              DropdownMenuItem(value: 'new_program', child: Text('New program')),
              DropdownMenuItem(
                value: 'substantial_revision',
                child: Text('Substantial revision'),
              ),
            ],
            onChanged: (v) => setState(() => _programDevelopmentKind = v),
          ),
          const SizedBox(height: 8),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Describe your contribution *'),
            maxLines: 3,
            onChanged: (v) => _contributionDescription = v,
          ),
          const SizedBox(height: 8),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Committee name (if applicable)'),
            onChanged: (v) => _committeeName = v,
          ),
        ],
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Instructional material claim details',
          style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
        ),
        const SizedBox(height: 8),
        TextFormField(
          decoration: const InputDecoration(labelText: 'Material title (optional override)'),
          onChanged: (v) => _materialTitleOverride = v,
        ),
        if (CriterionBCatalog.isCoAuthorIndicator(_indicatorId)) ...[
          const SizedBox(height: 8),
          TextFormField(
            decoration: const InputDecoration(labelText: 'Contribution percent (0–100)'),
            keyboardType: TextInputType.number,
            onChanged: (v) => _contributionPercentText = v,
          ),
        ],
        if (_showCompleteSetOnUploadForm) ...[
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Complete Instructional Material'),
            subtitle: const Text(
              'I confirm that my module or instructional manual is a complete stand-alone material or complete set, as applicable.',
            ),
            value: _completeSetDeclared ?? false,
            onChanged: (v) => setState(() {
              _completeSetDeclaredTouched = true;
              _completeSetDeclared = v;
            }),
          ),
        ],
      ],
    );
  }

  Widget _buildForm() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          InfoBanner(
            message: _isSupportingUpload
                ? 'Attach a file for: ${_evidenceSlotLabel(widget.evidenceSlot ?? '')}. '
                    'It will link to your main accomplishment automatically.'
                : _guidedCriterionCPrimaryUpload
                    ? (_criterionCMentorshipPrimary
                        ? 'Select files for this mentorship accomplishment. Match each file to the correct Annex A evidence type before saving.'
                        : 'Upload the signed approval sheet for this research service. '
                            'OCR runs in the background while you continue with RRPA/COPC and other evidence on the checklist.')
                : _isCriterionBPrimary
                    ? 'Select all files for this one accomplishment. You will confirm what each file is before saving—supporting documents link automatically to your main work.'
                : _criterionId == FacultyDocument.criterionAId
                    ? 'Upload SET/SEF evaluation PDFs under Criterion A. The system detects Student vs Supervisor sections from the document text (OCR)—no manual indicator selection.'
                    : 'Choose the KRA, criterion, and indicator that match your evidence, then attach files. Uploads are sent to your assigned reviewer for preparation and verification.',
          ),
          const SizedBox(height: 18),
          if (_guidedCriterionCPrimaryUpload) ...[
            Text(
              _criterionCMentorshipPrimary
                  ? 'Upload mentorship evidence'
                  : 'Upload signed approval sheet',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.navy),
            ),
            const SizedBox(height: 12),
          ] else if (_guidedCriterionBPrimaryUpload) ...[
            Text(
              widget.criterionBDraft?.isProgram == true
                  ? 'Upload your main program document'
                  : 'Upload your main teaching material file',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18, color: AppColors.navy),
            ),
            const SizedBox(height: 12),
          ] else ...[
          DropdownButtonFormField<String>(
            initialValue: _webKraId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Select KRA *'),
            items: [
              for (final kra in _kras)
                DropdownMenuItem(
                  value: kra['id']?.toString(),
                  child: Text(
                    '${kra['code'] ?? ''} — ${kra['name'] ?? ''}',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: (value) {
              setState(() {
                _webKraId = value;
                _criterionId = null;
                _indicatorId = null;
              });
            },
            validator: (value) => value == null ? 'Select a KRA' : null,
          ),
          const SizedBox(height: 14),
          DropdownButtonFormField<String>(
            initialValue: _criterionId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Select Criterion *'),
            items: [
              for (final criterion in _criteria)
                DropdownMenuItem(
                  value: criterion['id']?.toString(),
                  child: Text(
                    criterion['name']?.toString() ?? '',
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: _isSupportingUpload || _webKraId == null
                ? null
                : (value) => setState(() {
                      _criterionId = value;
                      _indicatorId = null;
                    }),
            validator: (value) => value == null ? 'Select a criterion' : null,
          ),
          if (_criterionId != FacultyDocument.criterionAId) ...[
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _indicatorId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Select Indicator *'),
              items: [
                for (final indicator in _indicators)
                  DropdownMenuItem(
                    value: indicator['id']?.toString(),
                    child: Text(
                      indicator['name']?.toString() ?? '',
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
              onChanged: _isSupportingUpload || _criterionId == null
                  ? null
                  : (value) => setState(() => _indicatorId = value),
              validator: (value) => value == null ? 'Select an indicator' : null,
            ),
          ],
          ],
          if (_isCriterionBPrimary && !_guidedPrimaryUpload) ...[
            const SizedBox(height: 14),
            _buildCriterionBMetadataFields(),
          ],
          const SizedBox(height: 18),
          Text(
            _files.isEmpty ? 'Upload documents' : 'Selected files (${_files.length})',
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surfaceMuted,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                const Icon(Icons.cloud_upload_outlined, size: 36, color: AppColors.navy),
                const SizedBox(height: 8),
                const Text(
                  'Select one or more PDF, Word, or image files (max 16 MB each).',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary),
                ),
                const SizedBox(height: 14),
                SecondaryButton(
                  label: _files.isEmpty ? 'Choose files' : 'Add more files',
                  icon: Icons.attach_file_rounded,
                  onPressed: _pickFiles,
                ),
                const SizedBox(height: 8),
                SecondaryButton(
                  label: 'Camera / scan',
                  icon: Icons.photo_camera_outlined,
                  onPressed: _pickCamera,
                ),
              ],
            ),
          ),
          if (_files.isNotEmpty) ...[
            const SizedBox(height: 12),
            for (var i = 0; i < _files.length; i++) ...[
              Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: Icon(
                    _files[i].fromCamera
                        ? Icons.photo_outlined
                        : Icons.description_outlined,
                    color: AppColors.navy,
                  ),
                  title: Text(
                    _files[i].fileName,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  subtitle: Text(
                    [
                      'Title: ${_files[i].title}',
                      if (_files[i].fileName.contains('.'))
                        _files[i].fileName.split('.').last.toUpperCase(),
                      _sizeLabel(_files[i].size),
                      if (_files[i].fromCamera) 'Camera capture',
                    ].where((p) => p.isNotEmpty).join(' · '),
                  ),
                  trailing: IconButton(
                    tooltip: 'Remove file',
                    onPressed: () => setState(() => _files.removeAt(i)),
                    icon: const Icon(Icons.close_rounded),
                  ),
                ),
              ),
            ],
          ],
          const SizedBox(height: 16),
          PrimaryButton(
            label: _guidedPrimaryUpload && _files.length > 1
                ? 'Continue — match evidence types'
                : _files.length > 1
                    ? 'Upload ${_files.length} documents'
                    : 'Save my work',
            icon: Icons.cloud_upload_outlined,
            onPressed: _onUploadPressed,
          ),
        ],
      ),
    );
  }

  String _evidenceSlotLabel(String slotId) {
    if (_criterionId == CriterionCCatalog.criterionId ||
        widget.initialCriterionId == CriterionCCatalog.criterionId) {
      return CriterionCCatalog.slotLabel(slotId);
    }
    return CriterionBCatalog.slotLabel(slotId);
  }

  Widget _buildAssignForm() {
    final criterionCAssign = _guidedCriterionCPrimaryUpload;
    final allowed = criterionCAssign
        ? CriterionCBulkUpload.assignableSlots(mentorship: _criterionCMentorshipPrimary)
        : CriterionBBulkUpload.assignableSlots(
            draft: widget.criterionBDraft,
            indicatorId: _indicatorId,
          );
    final draftTitle = criterionCAssign
        ? (_criterionCMentorshipPrimary
            ? (widget.criterionCDraft?.projectTitle ?? 'Mentorship service')
            : 'Research advising / panel')
        : widget.criterionBDraft?.isProgram == true
            ? (widget.criterionBDraft?.programName ?? 'Academic program')
            : (widget.criterionBDraft?.materialTitle ?? 'Teaching material');
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        InfoBanner(
          message: criterionCAssign
              ? 'Confirm Criterion C evidence types for “$draftTitle”. '
                  'Filename hints are suggestions only—choose the correct Annex A requirement for each file.'
              : 'Confirm what each file is for “$draftTitle”. Filename hints are suggestions only—choose the correct type for each PDF.',
        ),
        const SizedBox(height: 16),
        const Text(
          'Before you save, match each file to one requirement',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17, color: AppColors.navy),
        ),
        const SizedBox(height: 12),
        for (var i = 0; i < _files.length; i++) ...[
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _files[i].fileName,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    isExpanded: true,
                    value: _slotAssignments.length > i ? _slotAssignments[i] : null,
                    decoration: InputDecoration(
                      labelText: criterionCAssign ? 'This evidence is…' : 'This file is…',
                    ),
                    items: [
                      for (final slot in allowed)
                        DropdownMenuItem(
                          value: slot,
                          child: Text(_evidenceSlotLabel(slot)),
                        ),
                    ],
                    onChanged: (value) {
                      setState(() {
                        while (_slotAssignments.length <= i) {
                          _slotAssignments.add(null);
                        }
                        _slotAssignments[i] = value;
                      });
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
        const SizedBox(height: 8),
        Row(
          children: [
            TextButton(
              onPressed: () => setState(() => _phase = _UploadPhase.form),
              child: const Text('Back'),
            ),
            const Spacer(),
            PrimaryButton(
              label: 'Save my work',
              icon: Icons.save_outlined,
              expand: false,
              onPressed: _submit,
            ),
          ],
        ),
      ],
    );
  }
}

enum _UploadPhase { form, assign, processing, success }

class _SuccessView extends StatelessWidget {
  const _SuccessView({
    required this.count,
    required this.onDone,
    required this.onUploadAnother,
  });

  final int count;
  final VoidCallback onDone;
  final VoidCallback onUploadAnother;

  @override
  Widget build(BuildContext context) {
    final plural = count == 1 ? 'Document' : 'Documents';
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 88,
            height: 88,
            decoration: const BoxDecoration(
              color: AppColors.successSoft,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check_rounded, color: AppColors.success, size: 48),
          ),
          const SizedBox(height: 20),
          Text(
            '$plural submitted',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            count == 1
                ? 'Upload completed and the document is Pending Review. Text extraction (OCR) continues on the server—you can track status on the document details screen when processing finishes.'
                : '$count files were saved with Pending Review status. Text extraction runs on the server for each file; open a document to see when processing completes.',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary, height: 1.45),
          ),
          const SizedBox(height: 28),
          PrimaryButton(label: 'Back to documents', onPressed: onDone),
          const SizedBox(height: 10),
          SecondaryButton(label: 'Upload more', onPressed: onUploadAnother),
        ],
      ),
    );
  }
}
