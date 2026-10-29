import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/mock_kra_catalog.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/common.dart';
import '../../widgets/compact_folder_card.dart';
import '../../widgets/document_card.dart';
import 'document_flow_args.dart';

/// Faculty KRA → criterion → indicator document explorer.
class KraExplorerScreen extends StatefulWidget {
  const KraExplorerScreen({
    super.key,
    required this.kra,
    this.initialCriterionId,
    this.initialIndicatorId,
  });

  factory KraExplorerScreen.fromLaunch(KraExplorerLaunch launch) {
    return KraExplorerScreen(
      kra: launch.kra,
      initialCriterionId: launch.criterionId,
      initialIndicatorId: launch.indicatorId,
    );
  }

  final KraType kra;
  final String? initialCriterionId;
  final String? initialIndicatorId;

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
    _criterionId = widget.initialCriterionId;
    _indicatorId = widget.initialIndicatorId;
    _load();
  }

  Future<void> _load() async {
    try {
      final catalog = await MockKraCatalog.load();
      final kras = catalog['kras'];
      if (kras is List) {
        for (final entry in kras.whereType<Map>()) {
          if (entry['mobileKey'] == widget.kra.name || entry['id'] == _webKraId(widget.kra)) {
            if (mounted) {
              setState(() {
                _kraNode = Map<String, dynamic>.from(entry);
                _loading = false;
              });
            }
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

  int _docCountForCriterion(String criterionId) {
    final indicators = _indicatorsForCriterion(criterionId);
    final ids = indicators.map((i) => i['id']?.toString()).whereType<String>().toSet();
    return AppState.instance.documents
        .where((d) => d.kra == widget.kra && d.indicatorId != null && ids.contains(d.indicatorId))
        .length;
  }

  List<Map<String, dynamic>> _indicatorsForCriterion(String criterionId) {
    final criterion = _findCriterion(criterionId);
    if (criterion == null) return [];
    return (criterion['indicators'] as List? ?? []).whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
  }

  Map<String, dynamic>? _findCriterion(String? id) {
    if (id == null || _kraNode == null) return null;
    for (final c in (_kraNode!['criteria'] as List? ?? []).whereType<Map>()) {
      if (c['id']?.toString() == id) return Map<String, dynamic>.from(c);
    }
    return null;
  }

  Map<String, dynamic>? _findIndicator(String? id) {
    if (id == null) return null;
    for (final c in (_kraNode!['criteria'] as List? ?? []).whereType<Map>()) {
      for (final i in (c['indicators'] as List? ?? []).whereType<Map>()) {
        if (i['id']?.toString() == id) return Map<String, dynamic>.from(i);
      }
    }
    return null;
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

  void _handleBack() {
    if (_indicatorId != null) {
      _openIndicator(null);
    } else if (_criterionId != null) {
      _openCriterion(null);
    } else {
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppState.instance,
      builder: (context, _) {
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: Text(_appBarTitle),
            leading: IconButton(
              icon: const Icon(Icons.arrow_back_rounded),
              onPressed: _handleBack,
            ),
          ),
          floatingActionButton: _indicatorId != null ? _uploadFab() : null,
          body: _loading
              ? const LoadingState(message: 'Loading KRA structure…')
              : _kraNode == null
                  ? const EmptyState(
                      icon: Icons.folder_off_outlined,
                      title: 'KRA unavailable',
                      message: 'Official criteria could not be loaded.',
                    )
                  : Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _BreadcrumbBar(
                          kra: widget.kra,
                          criterionName: _findCriterion(_criterionId)?['name']?.toString(),
                          indicatorName: _findIndicator(_indicatorId)?['name']?.toString(),
                          onTapKra: () {
                            _openCriterion(null);
                          },
                          onTapCriterion: _criterionId != null && _indicatorId != null
                              ? () => _openIndicator(null)
                              : null,
                        ),
                        Expanded(child: _buildBody()),
                      ],
                    ),
        );
      },
    );
  }

  String get _appBarTitle {
    if (_indicatorId != null) return 'Evidence';
    if (_criterionId != null) return 'Indicators';
    return widget.kra.code;
  }

  Widget _uploadFab() {
    return FloatingActionButton.extended(
      backgroundColor: AppColors.navy,
      foregroundColor: Colors.white,
      onPressed: () {
        Navigator.pushNamed(
          context,
          AppRoutes.uploadDocument,
          arguments: UploadDocumentLaunch(
            kra: widget.kra,
            criterionId: _criterionId,
            indicatorId: _indicatorId,
          ),
        );
      },
      icon: const Icon(Icons.upload_file_rounded),
      label: const Text('Upload'),
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
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        _KraHeader(kra: widget.kra, subtitle: widget.kra.label),
        const SizedBox(height: 16),
        for (final criterion in criteria)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: CompactFolderCard(
              icon: Icons.folder_outlined,
              iconColor: AppColors.kra(widget.kra),
              title: criterion['name']?.toString() ?? 'Criterion',
              subtitle:
                  '${(criterion['indicators'] as List? ?? []).length} indicators · '
                  '${_docCountForCriterion(criterion['id']?.toString() ?? '')} uploads',
              onTap: () => _openCriterion(criterion['id']?.toString()),
            ),
          ),
      ],
    );
  }

  Widget _buildIndicators() {
    final criterion = _findCriterion(_criterionId);
    if (criterion == null) {
      return const EmptyState(
        icon: Icons.folder_off_outlined,
        title: 'Criterion not found',
        message: 'This criterion is not in the official KRA catalog.',
      );
    }
    final indicators = _indicatorsForCriterion(_criterionId!);
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      children: [
        Text(
          criterion['name']?.toString() ?? '',
          style: const TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 16,
            color: AppColors.navy,
            height: 1.35,
          ),
        ),
        const SizedBox(height: 12),
        for (final indicator in indicators)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: CompactFolderCard(
              icon: Icons.description_outlined,
              iconColor: AppColors.kra(widget.kra),
              title: indicator['name']?.toString() ?? 'Indicator',
              subtitle: '${_docsForIndicator(indicator['id']?.toString() ?? '').length} documents',
              onTap: () => _openIndicator(indicator['id']?.toString()),
            ),
          ),
      ],
    );
  }

  Widget _buildIndicatorDocs() {
    final indicatorId = _indicatorId ?? '';
    final docs = _docsForIndicator(indicatorId);
    final indicator = _findIndicator(_indicatorId);
    final evidence = indicator?['evidence'];

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
      children: [
        if (indicator != null) ...[
          Text(
            indicator['name']?.toString() ?? '',
            style: const TextStyle(
              fontWeight: FontWeight.w800,
              fontSize: 17,
              color: AppColors.navy,
              height: 1.35,
            ),
          ),
          if (indicator['description'] != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                indicator['description'].toString(),
                style: const TextStyle(color: AppColors.textSecondary, height: 1.45),
              ),
            ),
          if (evidence is List && evidence.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Required supporting evidence',
              style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.divider),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final item in evidence)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• ', style: TextStyle(color: AppColors.navy)),
                          Expanded(
                            child: Text(
                              item.toString(),
                              style: const TextStyle(fontSize: 13, height: 1.4),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 16),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Your uploads',
                  style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
                ),
              ),
              Text(
                '${docs.length} file${docs.length == 1 ? '' : 's'}',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
            ],
          ),
          const SizedBox(height: 8),
        ],
        if (docs.isEmpty)
          const EmptyState(
            icon: Icons.upload_file_outlined,
            title: 'No uploads yet',
            message: 'Tap Upload to attach PDF or image evidence for this indicator.',
          )
        else
          for (final doc in docs)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: DocumentCard(
                showOcr: true,
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
            ),
      ],
    );
  }
}

class _KraHeader extends StatelessWidget {
  const _KraHeader({required this.kra, required this.subtitle});

  final KraType kra;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.kraSoft(kra),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(kra.icon, color: AppColors.kra(kra), size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${kra.code} — ${kra.shortLabel}',
                  style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.navy),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BreadcrumbBar extends StatelessWidget {
  const _BreadcrumbBar({
    required this.kra,
    required this.criterionName,
    required this.indicatorName,
    required this.onTapKra,
    this.onTapCriterion,
  });

  final KraType kra;
  final String? criterionName;
  final String? indicatorName;
  final VoidCallback onTapKra;
  final VoidCallback? onTapCriterion;

  @override
  Widget build(BuildContext context) {
    final crumbs = <Widget>[
      _Crumb(label: 'Documents', onTap: () => Navigator.pop(context)),
      _Crumb(label: kra.code, onTap: onTapKra, active: criterionName == null && indicatorName == null),
    ];
    if (criterionName != null) {
      crumbs.add(const _CrumbSep());
      crumbs.add(
        _Crumb(
          label: _shorten(criterionName!, 28),
          onTap: onTapCriterion,
          active: indicatorName == null,
        ),
      );
    }
    if (indicatorName != null) {
      crumbs.add(const _CrumbSep());
      crumbs.add(_Crumb(label: _shorten(indicatorName!, 24), active: true));
    }

    return Material(
      color: Colors.white,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        child: Row(children: crumbs),
      ),
    );
  }

  static String _shorten(String value, int max) {
    if (value.length <= max) return value;
    return '${value.substring(0, max - 1)}…';
  }
}

class _CrumbSep extends StatelessWidget {
  const _CrumbSep();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 4),
      child: Icon(Icons.chevron_right_rounded, size: 18, color: AppColors.textSecondary),
    );
  }
}

class _Crumb extends StatelessWidget {
  const _Crumb({required this.label, this.onTap, this.active = false});

  final String label;
  final VoidCallback? onTap;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontSize: 12,
      fontWeight: active ? FontWeight.w800 : FontWeight.w600,
      color: active ? AppColors.navy : AppColors.textSecondary,
    );
    if (onTap == null || active) {
      return Text(label, style: style);
    }
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        child: Text(label, style: style.copyWith(color: AppColors.navy)),
      ),
    );
  }
}
