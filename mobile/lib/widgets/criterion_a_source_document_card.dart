import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';

/// One Criterion A source PDF row in the unified Supporting Documents workspace.
class CriterionASourceDocumentCard extends StatelessWidget {
  const CriterionASourceDocumentCard({
    super.key,
    required this.document,
    required this.workspaceMeta,
    required this.onTap,
  });

  final FacultyDocument document;
  final Map<String, dynamic>? workspaceMeta;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final meta = workspaceMeta ?? {};
    final composition = meta['compositionDisplay']?.toString() ??
        document.extractedInfo['Document evaluation composition'] ??
        '—';
    final ocr = meta['ocrStatus']?.toString() ?? document.ocrStatusLabel;
    final completeness = meta['completenessStatus']?.toString() ?? '—';
    final setCount = meta['setRecordCount'];
    final sefCount = meta['sefRecordCount'];
    final progress = meta['validationProgressLabel']?.toString();

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      document.fileName,
                      style: const TextStyle(
                        fontWeight: FontWeight.w800,
                        color: AppColors.navy,
                      ),
                    ),
                  ),
                  const Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
                ],
              ),
              const SizedBox(height: 6),
              Text(
                [
                  if (document.submittedAt != null)
                    'Uploaded ${document.submittedAt!.toLocal().toString().split(' ').first}',
                  'OCR: $ocr',
                ].join(' · '),
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  _Chip(label: composition.toString()),
                  _Chip(label: 'Completeness: $completeness'),
                  if (setCount != null || sefCount != null)
                    _Chip(label: 'SET ${setCount ?? 0} · SEF ${sefCount ?? 0}'),
                  if (progress != null && progress.isNotEmpty) _Chip(label: progress),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.infoSoft,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.navy),
      ),
    );
  }
}
