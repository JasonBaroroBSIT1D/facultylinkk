import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

/// Excel-style weighted KRA breakdown (estimated vs verified rows from API).
class WeightedKraBreakdownTable extends StatelessWidget {
  const WeightedKraBreakdownTable({
    super.key,
    required this.title,
    required this.rows,
    required this.total,
  });

  final String title;
  final List<Map<String, dynamic>> rows;
  final double? total;

  static String _fmt(num? v) {
    if (v == null) return '—';
    return v.toStringAsFixed(2);
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 14,
                color: AppColors.navy,
              ),
            ),
            const SizedBox(height: 12),
            Table(
              columnWidths: const {
                0: FlexColumnWidth(2.2),
                1: FlexColumnWidth(1.2),
                2: FlexColumnWidth(1),
                3: FlexColumnWidth(1.3),
              },
              defaultVerticalAlignment: TableCellVerticalAlignment.middle,
              children: [
                const TableRow(
                  decoration: BoxDecoration(
                    border: Border(bottom: BorderSide(color: AppColors.divider)),
                  ),
                  children: [
                    _Head('KRA'),
                    _Head('Raw score'),
                    _Head('Weight'),
                    _Head('Weighted'),
                  ],
                ),
                for (final row in rows)
                  TableRow(
                    children: [
                      _Cell((row['label'] as String?) ?? ''),
                      _Cell(_fmt(row['rawScore'] as num?)),
                      _Cell(
                        row['weightPercent'] != null
                            ? '${(row['weightPercent'] as num).round()}%'
                            : '—',
                      ),
                      _Cell(_fmt(row['weightedContribution'] as num?)),
                    ],
                  ),
                TableRow(
                  children: [
                    const _Cell('TOTAL', bold: true),
                    const _Cell('—'),
                    const _Cell('100%', bold: true),
                    _Cell(_fmt(total), bold: true),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Head extends StatelessWidget {
  const _Head(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}

class _Cell extends StatelessWidget {
  const _Cell(this.text, {this.bold = false});

  final String text;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: bold ? FontWeight.w800 : FontWeight.w500,
          color: AppColors.navy,
        ),
      ),
    );
  }
}
