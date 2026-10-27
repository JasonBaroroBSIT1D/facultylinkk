import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/mock_kra_catalog.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/common.dart';
import '../../widgets/document_card.dart';

/// Faculty KRA → criterion → indicator document explorer.
class KraExplorerScreen extends StatefulWidget {
  const KraExplorerScreen({super.key, required this.kra});

  final KraType kra;

  @override
  State<KraExplorerScreen> createState() => _KraExplorerScreenState();
}

class _KraExplorerScreenState extends State<KraExplorerScreen> {
  bool _loading = true;
  Map<String, dynamic>? _kraNode;
  String? _criterionId;
  String? _indicatorId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final catalog = await MockKraCatalog.load();
      final kras = catalog['kras'];
      if (kras is List) {
        for (final entry in kras.whereType<Map>()) {
          if (entry['mobileKey'] == widget.kra.name || entry['id'] == _webKraId(widget.kra)) {
            setState(() {
              _kraNode = Map<String, dynamic>.from(entry);
              _loading = false;
            });
            return;
          }
        }
      }
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  static String _webKraId(KraType kra) {
    switch (kra) {
      case KraType.instruction:
        return 'kra1';
      case KraType.research:
        return 'kra2';
      case KraType.extension:
        return 'kra3';
      case KraType.professionalDevelopment:
        return 'kra4';
    }
  }

  List<FacultyDocument> _docsForIndicator(String indicatorId) {
    return AppState.instance.documents
        .where((d) => d.kra == widget.kra && d.indicatorId == indicatorId)
        .toList();
  }

  void _openCriterion(String? id) {
    setState(() {
      _criterionId = id;
      _indicatorId = null;
    });
  }

  void _openIndicator(String? id) {
    setState(() => _indicatorId = id);
  }

  String get _title {
    if (_indicatorId != null) return 'Indicator evidence';
    if (_criterionId != null) return 'Indicators';
    return '${widget.kra.code} — ${widget.kra.shortLabel}';
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppState.instance,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: Text(_title),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded),
              onPressed: () {
                if (_indicatorId != null) {
                  _openIndicator(null);
                } else if (_criterionId != null) {
                  _openCriterion(null);
                } else {
                  Navigator.pop(context);
                }
              },
            ),
          ),
          floatingActionButton: _indicatorId != null
              ? FloatingActionButton.extended(
                  onPressed: () {
                    Navigator.pushNamed(
                      context,
                      AppRoutes.uploadDocument,
                      arguments: widget.kra,
                    );
                  },
                  icon: const Icon(Icons.upload_file_rounded),
                  label: const Text('Upload'),
                )
              : null,
          body: _loading
              ? const LoadingState(message: 'Loading KRA structure…')
              : _kraNode == null
                  ? const EmptyState(
                      title: 'KRA unavailable',
                      message: 'Official criteria could not be loaded.',
                    )
                  : _buildBody(),
        );
      },
    );
  }

  Widget _buildBody() {
    if (_indicatorId != null) return _buildIndicatorDocs();
    if (_criterionId != null) return _buildIndicators();
    return _buildCriteria();
  }

  Widget _buildCriteria() {
    final criteria = (_kraNode!['criteria'] as List? ?? []).whereType<Map>().toList();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          widget.kra.label,
          style: const TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 16,
            color: AppColors.navy,
          ),
        ),
        const SizedBox(height: 12),
        for (final criterion in criteria)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              leading: Icon(Icons.folder_outlined, color: AppColors.kra(widget.kra)),
              title: Text(criterion['name']?.toString() ?? 'Criterion'),
              subtitle: Text(
                '${(criterion['indicators'] as List? ?? []).length} indicators',
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => _openCriterion(criterion['id']?.toString()),
            ),
          ),
      ],
    );
  }

  Widget _buildIndicators() {
    final criteria = (_kraNode!['criteria'] as List? ?? []).whereType<Map>();
    final criterion = criteria.cast<Map<String, dynamic>?>().firstWhere(
          (c) => c?['id'] == _criterionId,
          orElse: () => null,
        );
    if (criterion == null) {
      return const EmptyState(title: 'Criterion not found', message: '');
    }
    final indicators = (criterion['indicators'] as List? ?? []).whereType<Map>().toList();
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          criterion['name']?.toString() ?? '',
          style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
        ),
        const SizedBox(height: 12),
        for (final indicator in indicators)
          Card(
            margin: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              leading: const Icon(Icons.description_outlined),
              title: Text(indicator['name']?.toString() ?? 'Indicator'),
              subtitle: Text(
                '${_docsForIndicator(indicator['id']?.toString() ?? '').length} documents',
              ),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => _openIndicator(indicator['id']?.toString()),
            ),
          ),
      ],
    );
  }

  Widget _buildIndicatorDocs() {
    final docs = _docsForIndicator(_indicatorId ?? '');
    final indicators = (_kraNode!['criteria'] as List? ?? [])
        .expand((c) => (c as Map?)?['indicators'] as List? ?? [])
        .whereType<Map>();
    final indicator = indicators.cast<Map<String, dynamic>?>().firstWhere(
          (i) => i?['id'] == _indicatorId,
          orElse: () => null,
        );
    final evidence = indicator?['evidence'];
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
      children: [
        if (indicator != null) ...[
          Text(
            indicator['name']?.toString() ?? '',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 17,
              color: AppColors.navy,
            ),
          ),
          if (indicator['description'] != null)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text(
                indicator['description'].toString(),
                style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
              ),
            ),
          if (evidence is List && evidence.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Text(
              'Required supporting evidence',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 6),
            for (final item in evidence)
              Text('• ${item.toString()}', style: const TextStyle(fontSize: 13)),
          ],
          const SizedBox(height: 16),
        ],
        if (docs.isEmpty)
          const EmptyState(
            title: 'No uploads yet',
            message: 'Upload PDF or image evidence for this indicator.',
          )
        else
          for (final doc in docs)
            DocumentCard(
              document: doc,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  AppRoutes.documentDetails,
                  arguments: doc.id,
                );
              },
              onView: () {
                Navigator.pushNamed(
                  context,
                  AppRoutes.documentDetails,
                  arguments: doc.id,
                );
              },
            ),
      ],
    );
  }
}
