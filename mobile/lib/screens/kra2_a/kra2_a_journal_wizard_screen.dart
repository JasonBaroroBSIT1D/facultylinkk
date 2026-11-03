import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../data/kra2_a_catalog.dart';
import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/tappable_card.dart';
import 'kra2_a_review_submit_screen.dart';

/// Three-step faculty flow: Choose → Upload → Review & Submit.
class Kra2AJournalWizardScreen extends StatefulWidget {
  const Kra2AJournalWizardScreen({super.key, this.initialDocumentId});

  /// When set, opens directly on step 3 (existing draft).
  final String? initialDocumentId;

  @override
  State<Kra2AJournalWizardScreen> createState() => _Kra2AJournalWizardScreenState();
}

class _Kra2AJournalWizardScreenState extends State<Kra2AJournalWizardScreen> {
  int _step = 0;
  JournalArticleType? _selectedType;
  String? _documentId;
  bool _uploading = false;
  String? _uploadError;

  @override
  void initState() {
    super.initState();
    if (widget.initialDocumentId != null && widget.initialDocumentId!.isNotEmpty) {
      _documentId = widget.initialDocumentId;
      _step = 2;
    }
  }

  String get _stepTitle {
    switch (_step) {
      case 0:
        return 'Step 1 of 3 — Choose';
      case 1:
        return 'Step 2 of 3 — Upload';
      default:
        return 'Step 3 of 3 — Review & Submit';
    }
  }

  Future<void> _pickAndUpload() async {
    final type = _selectedType;
    if (type == null) return;
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
        throw StateError('Could not read the file. Try again.');
      }
      final name = file.name.isNotEmpty ? file.name : 'journal-article.pdf';
      final id = await AppState.instance.uploadDocument(
        title: 'Journal article',
        category: DocumentCategory.researchPublications,
        kra: KraType.research,
        kraWebId: 'kra2',
        criterionId: Kra2AJournalCatalog.criterionId,
        indicatorId: type.indicatorId,
        fileName: name,
        fileBytes: bytes,
      );
      if (id == null || id.isEmpty) {
        throw StateError('Upload did not complete. Please try again.');
      }
      if (!mounted) return;
      setState(() {
        _documentId = id;
        _step = 2;
        _uploading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _uploadError = 'Upload failed. Please try again.';
        _uploading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_step == 2 && _documentId != null) {
      return Kra2AReviewSubmitScreen(
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
    return [
      const Text(
        'What kind of journal article is this?',
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
      const SizedBox(height: 8),
      const Text(
        'Pick the option that best matches your published work. You can change this only before uploading.',
      ),
      const SizedBox(height: 16),
      ...Kra2AJournalCatalog.journalTypes.map((type) {
        final selected = _selectedType?.indicatorId == type.indicatorId;
        return Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: TappableCard(
            selected: selected,
            onTap: () => setState(() => _selectedType = type),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(type.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
                const SizedBox(height: 6),
                Text(type.summary, style: TextStyle(color: Colors.grey.shade800)),
              ],
            ),
          ),
        );
      }),
      const SizedBox(height: 24),
      PrimaryButton(
        label: 'Continue',
        icon: Icons.arrow_forward,
        onPressed: _selectedType == null ? null : () => setState(() => _step = 1),
      ),
    ];
  }

  List<Widget> _uploadStep() {
    final type = _selectedType;
    return [
      Text(
        type?.title ?? 'Journal article',
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
      const SizedBox(height: 12),
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.navy.withValues(alpha: 0.15)),
        ),
        child: Column(
          children: [
            Icon(Icons.picture_as_pdf, size: 48, color: AppColors.navy.withValues(alpha: 0.8)),
            const SizedBox(height: 12),
            const Text(
              'Upload your journal article',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            const Text(
              'Use a PDF copy of the published article. We will read what we can from the file—you can fix anything on the next screen.',
              textAlign: TextAlign.center,
            ),
            if (type?.requiresContributionForm == true) ...[
              const SizedBox(height: 12),
              Text(
                'If you are a co-author, you will add your Certificate of Contribution on the next step—not here.',
                style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
      if (_uploadError != null) ...[
        const SizedBox(height: 12),
        Text(_uploadError!, style: const TextStyle(color: Colors.red)),
      ],
      const SizedBox(height: 20),
      PrimaryButton(
        label: _uploading ? 'Uploading…' : 'Choose PDF file',
        icon: Icons.upload_file,
        loading: _uploading,
        onPressed: _uploading ? null : _pickAndUpload,
      ),
      const SizedBox(height: 12),
      TextButton(
        onPressed: _uploading ? null : () => setState(() => _step = 0),
        child: const Text('Back to article type'),
      ),
    ];
  }
}
