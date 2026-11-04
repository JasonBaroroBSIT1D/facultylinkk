import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/kra2_catalog.dart';
import '../../models/enums.dart';
import '../../theme/app_colors.dart';
import '../../widgets/tappable_card.dart';
import 'kra2_hub_widgets.dart';
import 'kra2_review_submit_screen.dart';

/// Three-step flow: Choose accomplishment → Upload → Review & Submit.
class Kra2WizardScreen extends StatefulWidget {
  const Kra2WizardScreen({
    super.key,
    required this.criterionId,
    this.groupKey,
    this.initialIndicatorId,
    this.initialDocumentId,
  });

  final String criterionId;
  final String? groupKey;
  final String? initialIndicatorId;
  final String? initialDocumentId;

  @override
  State<Kra2WizardScreen> createState() => _Kra2WizardScreenState();
}

class _Kra2WizardScreenState extends State<Kra2WizardScreen> {
  int _step = 0;
  String? _selectedIndicatorId;
  String? _documentId;
  bool _uploading = false;
  String? _uploadError;
  String? _pickedFileName;
  Kra2AccomplishmentGroup? _group;
  List<Kra2AccomplishmentGroup> _allGroups = const [];
  bool _pickAuthorship = false;

  @override
  void initState() {
    super.initState();
    _allGroups = Kra2Catalog.accomplishmentGroups(widget.criterionId);
    if (widget.initialDocumentId != null && widget.initialDocumentId!.isNotEmpty) {
      _documentId = widget.initialDocumentId;
      _step = 2;
    }
    final gk = (widget.groupKey ?? '').trim();
    if (gk.isNotEmpty) {
      _group = Kra2Catalog.groupByKey(widget.criterionId, gk);
    }
    final pre = (widget.initialIndicatorId ?? '').trim();
    if (pre.isNotEmpty) {
      _selectedIndicatorId = pre;
      if (_documentId == null) _step = 1;
    } else if (_group != null) {
      if (_group!.needsAuthorshipChoice) {
        _pickAuthorship = true;
        _step = 0;
      } else {
        _selectedIndicatorId = _group!.indicatorIds.first;
        if (_documentId == null) _step = 1;
      }
    }
  }

  String get _stepTitle {
    switch (_step) {
      case 0:
        return 'Choose your work';
      case 1:
        return 'Add your document';
      default:
        return 'Check your work';
    }
  }

  Future<void> _pickAndUpload() async {
    final ind = _selectedIndicatorId;
    if (ind == null) return;
    setState(() {
      _uploading = true;
      _uploadError = null;
    });
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: const ['pdf'],
        withData: true,
      );
      if (result == null || result.files.isEmpty) {
        setState(() => _uploading = false);
        return;
      }
      final file = result.files.first;
      final bytes = file.bytes;
      if (bytes == null || bytes.isEmpty) {
        throw StateError('Could not read the file.');
      }
      final name = file.name.isNotEmpty ? file.name : 'kra2-evidence.pdf';
      setState(() => _pickedFileName = name);
      final title = Kra2Catalog.friendlyUploadTitle(ind);
      final id = await AppState.instance.uploadDocument(
        title: title,
        category: DocumentCategory.researchPublications,
        kra: KraType.research,
        kraWebId: 'kra2',
        criterionId: widget.criterionId,
        indicatorId: ind,
        fileName: name,
        fileBytes: bytes,
      );
      if (id == null || id.isEmpty) {
        throw StateError('Upload did not complete.');
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Your file is saved.')),
      );
      setState(() {
        _documentId = id;
        _step = 2;
        _uploading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _uploadError = 'Upload failed. Please try again.';
        _uploading = false;
      });
    }
  }

  void _selectAuthorship({required bool sole}) {
    final g = _group;
    if (g == null) return;
    final id = sole ? g.soleIndicatorId : g.coIndicatorId;
    if (id == null || id.isEmpty) return;
    setState(() {
      _selectedIndicatorId = id;
      _pickAuthorship = false;
      _step = 1;
    });
  }

  void _selectGroup(Kra2AccomplishmentGroup group) {
    setState(() {
      _group = group;
      if (group.needsAuthorshipChoice) {
        _pickAuthorship = true;
        _selectedIndicatorId = null;
      } else {
        _selectedIndicatorId = group.indicatorIds.first;
        _pickAuthorship = false;
        _step = 1;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_step == 2 && _documentId != null) {
      return Kra2ReviewSubmitScreen(
        primaryDocumentId: _documentId!,
        onBackToUpload: () => setState(() => _step = 1),
        onFinished: () => Navigator.of(context).pop(true),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(_stepTitle),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_step == 0) ..._chooseStep(),
          if (_step == 1) ..._uploadStep(),
        ],
      ),
    );
  }

  List<Widget> _chooseStep() {
    if (_pickAuthorship && _group != null) {
      return _authorshipStep(_group!);
    }
    return [
      const Text(
        'What did you accomplish?',
        style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
      ),
      const SizedBox(height: 8),
      Text(
        Kra2Catalog.mainHubCardDescription(widget.criterionId),
        style: const TextStyle(color: AppColors.textSecondary, height: 1.35),
      ),
      const SizedBox(height: 16),
      ..._allGroups.map(
        (g) => Kra2AccomplishmentTypeCard(
          title: g.title,
          subtitle: g.description,
          icon: g.icon,
          onTap: () => _selectGroup(g),
        ),
      ),
    ];
  }

  List<Widget> _authorshipStep(Kra2AccomplishmentGroup group) {
    return [
      Text(
        group.title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
      ),
      const SizedBox(height: 12),
      const Text(
        'Did you write this alone or with others?',
        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
      const SizedBox(height: 16),
      TappableCard(
        deferTap: false,
        padding: const EdgeInsets.all(16),
        onTap: () => _selectAuthorship(sole: true),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('I am the only author.', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
            SizedBox(height: 4),
            Text('You did this work without co-authors or co-inventors.'),
          ],
        ),
      ),
      const SizedBox(height: 10),
      TappableCard(
        deferTap: false,
        padding: const EdgeInsets.all(16),
        onTap: () => _selectAuthorship(sole: false),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('I worked with other authors.', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
            SizedBox(height: 4),
            Text('You will need a contribution certificate for shared credit.'),
          ],
        ),
      ),
      const SizedBox(height: 12),
      TextButton(
        onPressed: () => setState(() {
          _pickAuthorship = false;
          _group = null;
          _selectedIndicatorId = null;
        }),
        child: const Text('Choose a different type'),
      ),
    ];
  }

  List<Widget> _uploadStep() {
    final ind = _selectedIndicatorId ?? '';
    return [
      const Text(
        'Add your document',
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
      ),
      const SizedBox(height: 8),
      const Text(
        'Upload a PDF that shows your accomplishment.',
        style: TextStyle(color: AppColors.textSecondary, height: 1.35),
      ),
      const SizedBox(height: 16),
      Text(
        Kra2Catalog.accomplishmentGroupTitle(ind),
        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
      ),
      const SizedBox(height: 8),
      Text(Kra2Catalog.primaryUploadLabel(ind)),
      const SizedBox(height: 8),
      const Text('PDF files are accepted.', style: TextStyle(fontSize: 13, color: AppColors.textTertiary)),
      const SizedBox(height: 20),
      if (_uploadError != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Text(_uploadError!, style: const TextStyle(color: AppColors.error)),
        ),
      if (_pickedFileName != null && !_uploading)
        Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Row(
            children: [
              const Icon(Icons.insert_drive_file, color: AppColors.navyMid),
              const SizedBox(width: 8),
              Expanded(child: Text(_pickedFileName!, overflow: TextOverflow.ellipsis)),
            ],
          ),
        ),
      Material(
        color: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.divider),
        ),
        child: InkWell(
          onTap: _uploading ? null : _pickAndUpload,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 20),
            child: Column(
              children: [
                Icon(
                  _uploading ? Icons.hourglass_top : Icons.cloud_upload_outlined,
                  size: 48,
                  color: AppColors.navyMid,
                ),
                const SizedBox(height: 12),
                Text(
                  _uploading ? 'Uploading…' : 'Choose PDF',
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                ),
                if (_uploading)
                  const Padding(
                    padding: EdgeInsets.only(top: 16),
                    child: LinearProgressIndicator(minHeight: 3),
                  ),
              ],
            ),
          ),
        ),
      ),
      const SizedBox(height: 16),
      OutlinedButton(
        onPressed: _uploading
            ? null
            : () => setState(() {
                  _step = 0;
                  if (_group != null && _group!.needsAuthorshipChoice) {
                    _pickAuthorship = true;
                  }
                }),
        child: const Text('Back'),
      ),
    ];
  }
}
