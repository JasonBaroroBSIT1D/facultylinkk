import 'package:flutter/material.dart';

import '../data/teaching_effectiveness_mapper.dart';
import '../theme/app_colors.dart';

/// Criterion A SET/SEF summary from backend teaching-effectiveness API (read-only).
class TeachingEffectivenessSummaryCard extends StatelessWidget {
  const TeachingEffectivenessSummaryCard({super.key, required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final set = data['set'] as Map<String, dynamic>? ?? {};
    final sef = data['sef'] as Map<String, dynamic>? ?? {};
    final note = data['summaryNote'] as String?;
    final criterionLine = TeachingEffectivenessMapper.criterionEstimatedLabel(data);
    final disp = TeachingEffectivenessMapper.criterionDisplay(data);
    final criterionExplanation = disp?['explanation'] as String?;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Teaching effectiveness (SET + SEF)',
              style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
            ),
            if (note != null && note.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(note, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
            ],
            const SizedBox(height: 12),
            _IndicatorBlock(title: 'SET (Student Evaluation)', block: set),
            const SizedBox(height: 10),
            _IndicatorBlock(title: 'SEF (Supervisor Evaluation)', block: sef),
            const Divider(height: 24),
            Text(
              criterionLine,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
            if (criterionExplanation != null && criterionExplanation.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                criterionExplanation,
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.35),
              ),
            ],
            const SizedBox(height: 6),
            const Text(
              'Combined Criterion A uses SET + SEF per published rules. Component lines may show estimates before reviewer validation.',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.35),
            ),
          ],
        ),
      ),
    );
  }
}

class _IndicatorBlock extends StatelessWidget {
  const _IndicatorBlock({required this.title, required this.block});

  final String title;
  final Map<String, dynamic> block;

  @override
  Widget build(BuildContext context) {
    final counts = TeachingEffectivenessMapper.recordCounts(block);
    final line = TeachingEffectivenessMapper.componentLine(block);
    final comp = block['componentDisplay'];
    final compExplanation =
        comp is Map ? comp['explanation'] as String? : null;
    final scoringNote = block['scoringNote'] as String?;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
        const SizedBox(height: 4),
        Text(line, style: const TextStyle(fontSize: 12)),
        if (compExplanation != null && compExplanation.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(
              compExplanation,
              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
          ),
        if (counts.isNotEmpty) ...[
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 4,
            children: [
              _CountChip('Detected', counts['detected'] ?? 0),
              _CountChip('Verified', counts['verified'] ?? 0),
              _CountChip('Pending', counts['pending'] ?? 0),
              _CountChip('Rejected/revision', counts['rejectedOrRevision'] ?? 0),
              if ((counts['incomplete'] ?? 0) > 0)
                _CountChip('Incomplete', counts['incomplete']!),
              if ((counts['excludedDuplicates'] ?? 0) > 0)
                _CountChip('Duplicates excluded', counts['excludedDuplicates']!),
            ],
          ),
        ],
        if (scoringNote != null && scoringNote.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              scoringNote,
              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
          ),
      ],
    );
  }
}

class _CountChip extends StatelessWidget {
  const _CountChip(this.label, this.count);

  final String label;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Text(
      '$label: $count',
      style: const TextStyle(fontSize: 10, color: AppColors.textTertiary),
    );
  }
}
