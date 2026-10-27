import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../data/mock_kra_catalog.dart';
import '../../theme/app_colors.dart';
import '../../utils/title_from_filename.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';

class UploadDocumentScreen extends StatefulWidget {
  const UploadDocumentScreen({super.key, this.initialKra});

  final KraType? initialKra;

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

  @override
  void initState() {
    super.initState();
    _loadCatalog();
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
    final result = await FilePicker.platform.pickFiles(
      withData: true,
      allowMultiple: true,
      type: FileType.custom,
      allowedExtensions: _allowedExtensions,
    );
    if (result == null || result.files.isEmpty) return;
    final pending = <_PendingUpload>[];
    for (final file in result.files) {
      final bytes = file.bytes;
      if (bytes == null) continue;
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
  }

  void _addFiles(List<_PendingUpload> incoming) {
    if (incoming.isEmpty) return;
    final rejected = <String>[];
    final accepted = <_PendingUpload>[];
    final existing = {for (final f in _files) f.fileName.toLowerCase()};

    for (final file in incoming) {
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

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_files.isEmpty) {
      showAppSnackBar(context, 'Select or scan at least one file first.', error: true);
      return;
    }
    if (_webKraId == null || _criterionId == null || _indicatorId == null) {
      showAppSnackBar(context, 'Select a KRA, criterion, and indicator.', error: true);
      return;
    }
    final total = _files.length;
    setState(() {
      _phase = _UploadPhase.processing;
      _progress = 0.05;
      _progressLabel = 'Uploading 1 of $total…';
      _uploadedCount = 0;
    });

    try {
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
          indicatorId: _indicatorId,
          packageId: evidencePackageId,
          requirementIndex: total > 1 ? i : null,
          fileBytes: file.bytes,
        );
        _uploadedCount = i + 1;
      }
      if (!mounted) return;
      setState(() {
        _progress = 1;
        _phase = _UploadPhase.success;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _phase = _UploadPhase.form);
      final prefix = _uploadedCount > 0
          ? 'Uploaded $_uploadedCount of $total, then failed: '
          : '';
      showAppSnackBar(context, '$prefix$error', error: true);
    }
  }

  String _sizeLabel(int bytes) {
    if (bytes < 1024) return '$bytes B';
    return '${(bytes / 1024).toStringAsFixed(1)} KB';
  }

  void _resetFormKeepSelection() {
    setState(() {
      _phase = _UploadPhase.form;
      _files.clear();
      _progress = 0;
      _progressLabel = '';
      _uploadedCount = 0;
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
                  'Each file is saved under the selected KRA and criterion. OCR and validation run automatically; some documents may be system-approved or queued for review.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textSecondary, height: 1.45),
                ),
              ],
            ),
          ),
        _UploadPhase.success => _SuccessView(
            count: _uploadedCount,
            onDone: () => Navigator.pop(context),
            onUploadAnother: _resetFormKeepSelection,
          ),
      },
    );
  }

  Widget _buildForm() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
        children: [
          const InfoBanner(
            message:
                'Choose the KRA, criterion, and indicator that match your evidence, then attach files. Uploads are saved as drafts until you submit them for reviewer validation.',
          ),
          const SizedBox(height: 18),
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
            onChanged: _webKraId == null
                ? null
                : (value) => setState(() {
                      _criterionId = value;
                      _indicatorId = null;
                    }),
            validator: (value) => value == null ? 'Select a criterion' : null,
          ),
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
            onChanged: _criterionId == null
                ? null
                : (value) => setState(() => _indicatorId = value),
            validator: (value) => value == null ? 'Select an indicator' : null,
          ),
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
            label: _files.length > 1
                ? 'Upload ${_files.length} documents'
                : 'Upload document',
            icon: Icons.cloud_upload_outlined,
            onPressed: _submit,
          ),
        ],
      ),
    );
  }
}

enum _UploadPhase { form, processing, success }

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
                ? 'Your original file was saved under the selected KRA and criterion with Pending Review status. A reviewer still confirms the score.'
                : '$count files were saved under the selected KRA and criterion with Pending Review status. A reviewer still confirms the scores.',
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
