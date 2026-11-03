import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:pdfx/pdfx.dart';

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
  PdfControllerPinch? _pdfController;
  int _pdfPages = 0;
  int _pdfPage = 1;

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

  bool get _isPdf {
    final mime = (widget.document.mimeType ?? '').toLowerCase();
    final name = widget.document.fileName.toLowerCase();
    return mime.contains('pdf') || name.endsWith('.pdf');
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _pdfController?.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    _pdfController?.dispose();
    _pdfController = null;
    try {
      var stored = AppState.instance.bytesForDocument(widget.document.id);
      stored ??= await AppState.instance.loadDocumentBytes(widget.document.id);
      if (stored == null || stored.isEmpty) {
        throw StateError(
          'The file could not be loaded. Check your connection and try again.',
        );
      }
      final bytes = Uint8List.fromList(stored);
      if (_isPdf) {
        if (bytes.length < 4 ||
            bytes[0] != 0x25 ||
            bytes[1] != 0x50 ||
            bytes[2] != 0x44 ||
            bytes[3] != 0x46) {
          throw StateError('The server did not return a valid PDF.');
        }
        final controller = PdfControllerPinch(
          document: PdfDocument.openData(bytes),
        );
        if (!mounted) {
          controller.dispose();
          return;
        }
        setState(() {
          _bytes = bytes;
          _pdfController = controller;
          _pdfPages = 0;
          _pdfPage = 1;
          _loading = false;
        });
        return;
      }
      if (!mounted) return;
      setState(() {
        _bytes = bytes;
        _loading = false;
      });
      if (!_isImage && !kIsWeb) {
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
      String? localPath;
      if (!kIsWeb) {
        localPath = await saveDocumentBytes(
          _bytes!,
          '${widget.document.id}_${widget.document.fileName}',
        );
      }
      final opened = kIsWeb
          ? await openDocumentBytesInBrowser(
              _bytes!,
              fileName: widget.document.fileName,
              mimeType: widget.document.mimeType,
            )
          : (localPath != null && await openSavedDocument(localPath));
      if (!mounted) return;
      if (!opened && !auto) {
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
        actions: [
          if (_pdfController != null && _pdfPages > 1)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 12),
                child: Text(
                  'Page $_pdfPage of $_pdfPages',
                  style: const TextStyle(fontSize: 13),
                ),
              ),
            ),
        ],
      ),
      body: _loading
          ? const LoadingState(message: 'Loading document…')
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
      return InteractiveViewer(
        child: Center(child: Image.memory(_bytes!, fit: BoxFit.contain)),
      );
    }
    if (_pdfController != null) {
      return Column(
        children: [
          Expanded(
            child: PdfViewPinch(
              controller: _pdfController!,
              onPageChanged: (page) {
                if (!mounted) return;
                setState(() {
                  _pdfPage = page;
                  _pdfPages = _pdfController?.pagesCount ?? _pdfPages;
                });
              },
              scrollDirection: Axis.vertical,
            ),
          ),
          if (!kIsWeb)
            Padding(
              padding: const EdgeInsets.all(12),
              child: OutlinedButton(
                onPressed: _openExternal,
                child: const Text('Open in external app'),
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
          const Icon(Icons.insert_drive_file_outlined, size: 64, color: AppColors.navy),
          const SizedBox(height: 16),
          Text(
            widget.document.fileName,
            textAlign: TextAlign.center,
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
          ),
          const Spacer(),
          PrimaryButton(label: 'Open file', onPressed: _openExternal),
        ],
      ),
    );
  }
}
