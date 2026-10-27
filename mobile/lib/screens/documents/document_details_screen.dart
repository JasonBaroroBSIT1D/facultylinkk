import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../utils/formatters.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/status_badge.dart';
import 'document_viewer_screen.dart';

class DocumentDetailsScreen extends StatelessWidget {
  const DocumentDetailsScreen({super.key, required this.documentId});

  final String documentId;

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppState.instance,
      builder: (context, _) {
        final document = AppState.instance.documentById(documentId);
        if (document == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Document')),
            body: const ErrorState(
              message: 'This document is no longer available.',
            ),
          );
        }
        return _DocumentDetailsBody(document: document);
      },
    );
  }
}

class _DocumentDetailsBody extends StatefulWidget {
  const _DocumentDetailsBody({required this.document});

  final FacultyDocument document;

  @override
  State<_DocumentDetailsBody> createState() => _DocumentDetailsBodyState();
}

class _DocumentDetailsBodyState extends State<_DocumentDetailsBody> {
  FacultyDocument get document => widget.document;
  String? _localError;
  bool _working = false;

  static const _scoringKeys = [
    'Assigned KRA',
    'Author count',
    'Base points',
    'Contribution percent',
    'Contribution score',
    'Document type',
    'Scoring formula',
  ];

  Map<String, String> get _scoringInfo {
    final out = <String, String>{};
    for (final key in _scoringKeys) {
      final value = document.extractedInfo[key];
      if (value != null && value.trim().isNotEmpty) {
        out[key] = value;
      }
    }
    return out;
  }

  Future<void> _confirmDelete() async {
    final ok = await showConfirmDialog(
      context: context,
      title: 'Delete document?',
      message:
          'This removes the upload from your active list. The record is kept for audit purposes.',
      confirmLabel: 'Delete',
      destructive: true,
    );
    if (ok != true || !mounted) return;
    setState(() {
      _working = true;
      _localError = null;
    });
    try {
      await AppState.instance.deleteDocument(document.id);
      if (!mounted) return;
      showAppSnackBar(context, 'Document deleted.');
      Navigator.pop(context);
    } catch (error) {
      setState(() => _localError = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _replaceFile() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'png', 'jpg', 'jpeg'],
      withData: true,
    );
    final file = picked?.files.single;
    if (file == null || file.bytes == null) return;
    setState(() {
      _working = true;
      _localError = null;
    });
    try {
      await AppState.instance.replaceDocument(
        documentId: document.id,
        fileName: file.name,
        fileBytes: file.bytes!,
        title: document.title,
      );
      if (!mounted) return;
      showAppSnackBar(context, 'Document replaced and sent for review.');
      Navigator.pop(context);
    } catch (error) {
      setState(() => _localError = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _requestWithdrawal() async {
    final ok = await showConfirmDialog(
      context: context,
      title: 'Request withdrawal?',
      message:
          'Ask an administrator to withdraw credited points for this approved document.',
      confirmLabel: 'Submit request',
    );
    if (ok != true || !mounted) return;
    setState(() {
      _working = true;
      _localError = null;
    });
    try {
      await AppState.instance.requestDocumentWithdrawal(document.id);
      if (!mounted) return;
      showAppSnackBar(context, 'Withdrawal request submitted.');
    } catch (error) {
      setState(() => _localError = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  void _openOriginal(BuildContext context) {
    if (!document.hasFile) {
      showAppSnackBar(
        context,
        'Original file is not available for this record.',
        error: true,
      );
      return;
    }
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => DocumentViewerScreen(document: document),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scoring = _scoringInfo;
    final author = (document.author ?? '').trim().isEmpty
        ? '—'
        : document.author!.trim();
    final color = AppColors.kra(document.kra);

    final actionsEnabled = !_working && !AppState.instance.refreshInProgress;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Document details'),
        actions: [
          PopupMenuButton<String>(
            enabled: actionsEnabled,
            onSelected: (value) {
              switch (value) {
                case 'view':
                  _openOriginal(context);
                case 'replace':
                  _replaceFile();
                case 'delete':
                  _confirmDelete();
                case 'withdraw':
                  _requestWithdrawal();
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'view', child: Text('View document')),
              PopupMenuItem(
                value: 'replace',
                enabled: document.canReplace,
                child: const Text('Replace document'),
              ),
              PopupMenuItem(
                value: 'delete',
                enabled: document.canDelete,
                child: const Text('Delete document'),
              ),
              PopupMenuItem(
                value: 'withdraw',
                enabled: document.canRequestWithdrawal,
                child: const Text('Request withdrawal'),
              ),
            ],
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: PrimaryButton(
            label: 'View document',
            icon: Icons.visibility_outlined,
            onPressed: actionsEnabled ? () => _openOriginal(context) : null,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => AppState.instance.refreshData(label: 'Refreshing documents...'),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
          if (_localError != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ErrorState(
                message: _localError!,
                onRetry: () => AppState.instance.refreshData(),
              ),
            ),
          if (!document.canDelete && !document.canReplace && !document.canRequestWithdrawal)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(
                document.creditsPoints
                    ? 'Approved documents stay on record. Use Request withdrawal if points must be reversed.'
                    : 'This document cannot be deleted or replaced while a reviewer decision or credited score applies.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.divider),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: AppColors.kraSoft(document.kra),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(Icons.description_outlined, color: color),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        document.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppColors.textPrimary,
                          height: 1.25,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        document.fileName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          StatusBadge(status: document.status, compact: true),
                          _Pill(
                            icon: Icons.stars_outlined,
                            label: 'Credited: ${document.creditedLabel}',
                            color: AppColors.navy,
                            soft: AppColors.infoSoft,
                          ),
                          _Pill(
                            icon: document.kra.icon,
                            label: document.kra.shortLabel,
                            color: color,
                            soft: AppColors.kraSoft(document.kra),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          _SectionCard(
            title: 'Overview',
            child: Column(
              children: [
                _FactRow(label: 'Author(s)', value: author),
                _FactRow(
                  label: 'Submitted',
                  value: formatDisplayDate(document.submittedAt),
                ),
                _FactRow(label: 'KRA', value: document.kra.label),
                if (document.criterionId != null)
                  _FactRow(label: 'Criterion', value: document.criterionId!),
                if (document.extractedInfo['Automatically identified indicator']?.isNotEmpty == true)
                  _FactRow(
                    label: 'Identified indicator',
                    value: document.extractedInfo['Automatically identified indicator']!,
                  )
                else if (document.indicatorId != null)
                  _FactRow(label: 'Indicator', value: document.indicatorId!),
                if (document.extractedInfo['Verification tier']?.isNotEmpty == true)
                  _FactRow(
                    label: 'Verification',
                    value: document.extractedInfo['Verification tier']!,
                  ),
                _FactRow(
                  label: 'Simulation score',
                  value: document.simulationScoreLabel,
                ),
                _FactRow(
                  label: 'Score source',
                  value: document.simulationSourceLabel,
                ),
                if (document.reviewerOversightStatus?.isNotEmpty == true)
                  _FactRow(
                    label: 'Reviewer oversight',
                    value: document.reviewerOversightStatus!,
                  ),
                _FactRow(
                  label: 'Provisional Score',
                  value: document.provisionalLabel,
                ),
                _FactRow(
                  label: 'Credited Points',
                  value: document.creditedLabel,
                ),
                _FactRow(
                  label: 'File',
                  value: document.hasFile ? 'On file' : 'Unavailable',
                  last: true,
                ),
              ],
            ),
          ),
          if (scoring.isNotEmpty) ...[
            const SizedBox(height: 12),
            _SectionCard(
              title: 'Scoring snapshot',
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final entry in scoring.entries)
                    if (entry.key != 'Scoring formula' &&
                        entry.key != 'Document type' &&
                        entry.key != 'Contribution score' &&
                        entry.key != 'Provisional score')
                      _ScoreChip(label: entry.key, value: entry.value),
                ],
              ),
            ),
          ],
          if (document.requiresAction) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.errorSoft,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.error.withValues(alpha: 0.25)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Action required',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: AppColors.error,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    document.reviewerFeedback ??
                        'This document needs revision before it can be validated.',
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      height: 1.35,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ] else if (document.reviewerFeedback != null) ...[
            const SizedBox(height: 12),
            InfoBanner(
              message: document.reviewerFeedback!,
              icon: Icons.chat_bubble_outline_rounded,
              color: AppColors.navy,
              background: AppColors.infoSoft,
            ),
          ],
          if (document.validationResult != null &&
              document.validationResult!.trim().isNotEmpty) ...[
            const SizedBox(height: 12),
            _SectionCard(
              title: 'Validation',
              child: Text(
                document.validationResult!,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  height: 1.4,
                  fontSize: 13,
                ),
              ),
            ),
          ],
          if (document.status == DocumentStatus.draft) ...[
            const SizedBox(height: 12),
            PrimaryButton(
              label: 'Submit for review',
              icon: Icons.send_rounded,
              onPressed: () async {
                try {
                  await AppState.instance.submitDocumentForReview(document.id);
                  if (!context.mounted) return;
                  showAppSnackBar(context, 'Submitted for reviewer validation.');
                  Navigator.pop(context);
                } catch (error) {
                  if (!context.mounted) return;
                  showAppSnackBar(context, '$error', error: true);
                }
              },
            ),
          ],
          if (document.canResubmit) ...[
            const SizedBox(height: 12),
            SecondaryButton(
              label: 'Edit / resubmit',
              icon: Icons.upload_file_outlined,
              onPressed: () {
                Navigator.pushNamed(
                  context,
                  AppRoutes.uploadDocument,
                  arguments: document.kra,
                );
              },
            ),
          ],
        ],
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 13,
              color: AppColors.navy,
              letterSpacing: 0.2,
            ),
          ),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }
}

class _FactRow extends StatelessWidget {
  const _FactRow({
    required this.label,
    required this.value,
    this.last = false,
  });

  final String label;
  final String value;
  final bool last;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(bottom: last ? 0 : 10, top: 0),
      decoration: BoxDecoration(
        border: last
            ? null
            : const Border(
                bottom: BorderSide(color: AppColors.divider),
              ),
      ),
      margin: EdgeInsets.only(bottom: last ? 0 : 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 96,
            child: Text(
              label,
              style: const TextStyle(
                color: AppColors.textTertiary,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 13,
                color: AppColors.textPrimary,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ScoreChip extends StatelessWidget {
  const _ScoreChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140,
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: AppColors.textTertiary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: AppColors.navy,
            ),
          ),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({
    required this.icon,
    required this.label,
    required this.color,
    required this.soft,
  });

  final IconData icon;
  final String label;
  final Color color;
  final Color soft;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: soft,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
