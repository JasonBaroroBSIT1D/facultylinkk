import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/models.dart';
import '../../theme/app_colors.dart';
import '../../utils/open_document_bytes.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';

class DocumentViewerScreen extends StatefulWidget {
  const DocumentViewerScreen({super.key, required this.document});

  final FacultyDocument document;

  @override
  State<DocumentViewerScreen> createState() => _DocumentViewerScreenState();
}

class _DocumentViewerScreenState extends State<DocumentViewerScreen> {
  bool _loading = true;
  String? _error;
  Uint8List? _bytes;
  String? _localPath;
  bool _openedExternally = false;

  bool get _isImage {
    final mime = (widget.document.mimeType ?? '').toLowerCase();
    final name = widget.document.fileName.toLowerCase();
    return mime.startsWith('image/') ||
        name.endsWith('.png') ||
        name.endsWith('.jpg') ||
        name.endsWith('.jpeg') ||
        name.endsWith('.webp') ||
        name.endsWith('.gif') ||
        name.endsWith('.bmp');
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
      _openedExternally = false;
    });
    try {
      if (!widget.document.hasFile) {
        throw StateError(
          'Original file is not stored for this demo record. Upload a new document to preview a local copy.',
        );
      }
      var stored = AppState.instance.bytesForDocument(widget.document.id);
      stored ??= await AppState.instance.loadDocumentBytes(widget.document.id);
      if (stored == null) {
        throw StateError(
          'The file could not be loaded. Check your connection and try again.',
        );
      }
      final bytes = Uint8List.fromList(stored);
      String? localPath;
      if (!kIsWeb) {
        localPath = await saveDocumentBytes(
          bytes,
          '${widget.document.id}_${widget.document.fileName}',
        );
      }
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _localPath = localPath;
        _loading = false;
        _error = null;
      });
      if (!_isImage) {
        await _openExternal(auto: true);
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = error.toString().replaceFirst('StateError: ', '');
      });
    }
  }

  Future<void> _openExternal({bool auto = false}) async {
    if (_bytes == null) return;
    try {
      final opened = kIsWeb
          ? await openDocumentBytesInBrowser(
              _bytes!,
              fileName: widget.document.fileName,
              mimeType: widget.document.mimeType,
            )
          : (_localPath != null && await openSavedDocument(_localPath!));
      if (!mounted) return;
      if (opened) {
        setState(() => _openedExternally = true);
        return;
      }
      if (!auto) {
        showAppSnackBar(
          context,
          'Could not open this file with an external app.',
          error: true,
        );
      }
    } catch (_) {
      if (!mounted || auto) return;
      showAppSnackBar(context, 'Could not open this file.', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.document.title, maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
      body: _loading
          ? const LoadingState(message: 'Loading local preview…')
          : _error != null
              ? ErrorState(message: _error!, onRetry: _load)
              : _buildPreview(),
    );
  }

  Widget _buildPreview() {
    if (_bytes == null) {
      return const ErrorState(message: 'No preview available.');
    }
    if (_isImage) {
      return Column(
        children: [
          Expanded(
            child: InteractiveViewer(
              child: Center(
                child: Image.memory(_bytes!, fit: BoxFit.contain),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              'Local preview only (simulated workflow — not verified by a reviewer).',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: AppColors.textTertiary),
            ),
          ),
        ],
      );
    }
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Icon(Icons.picture_as_pdf_outlined, size: 64, color: AppColors.navy),
          const SizedBox(height: 16),
          Text(
            widget.document.fileName,
            textAlign: TextAlign.center,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
          ),
          const SizedBox(height: 8),
          Text(
            _openedExternally
                ? 'Opened in your default viewer.'
                : 'Tap below to open this local copy.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textTertiary),
          ),
          const Spacer(),
          PrimaryButton(
            label: 'Open file',
            onPressed: () => _openExternal(),
          ),
        ],
      ),
    );
  }
}
