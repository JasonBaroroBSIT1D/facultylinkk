import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/mock_kra_catalog.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/common.dart';
import '../../widgets/kra_folder_overview.dart';
import '../../widgets/preparation_period_card.dart';
import 'document_flow_args.dart';

class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final _search = TextEditingController();
  DocumentStatus? _statusFilter;
  bool _loading = true;
  List<Map<String, dynamic>> _catalogKras = [];

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      final catalog = await MockKraCatalog.load();
      final raw = catalog['kras'];
      final list = raw is List
          ? raw.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList()
          : <Map<String, dynamic>>[];
      if (mounted) setState(() => _catalogKras = list);
    } catch (_) {
      // Folder cards still work; search labels may be limited.
    }
    if (!mounted) return;
    setState(() => _loading = false);
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  List<FacultyDocument> _filtered(List<FacultyDocument> source) {
    final query = _search.text.trim().toLowerCase();
    return source.where((doc) {
      final matchesQuery = query.isEmpty ||
          doc.title.toLowerCase().contains(query) ||
          doc.fileName.toLowerCase().contains(query) ||
          doc.category.label.toLowerCase().contains(query) ||
          doc.kra.code.toLowerCase().contains(query) ||
          doc.kra.label.toLowerCase().contains(query) ||
          doc.kra.shortLabel.toLowerCase().contains(query);
      final matchesStatus = _statusFilter == null || doc.status == _statusFilter;
      return matchesQuery && matchesStatus;
    }).toList();
  }

  List<_SearchHit> _catalogHits(String query) {
    if (query.isEmpty) return [];
    final q = query.toLowerCase();
    final hits = <_SearchHit>[];
    for (final kraEntry in _catalogKras) {
      final mobileKey = kraEntry['mobileKey']?.toString();
      KraType? resolved;
      for (final candidate in KraType.values) {
        if (candidate.name == mobileKey) {
          resolved = candidate;
          break;
        }
      }
      if (resolved == null) continue;
      final kra = resolved;
      final kraName = kraEntry['name']?.toString() ?? kra.label;
      if (kraName.toLowerCase().contains(q) ||
          kra.code.toLowerCase().contains(q) ||
          kra.shortLabel.toLowerCase().contains(q)) {
        hits.add(
          _SearchHit(
            label: '${kra.code} — $kraName',
            subtitle: 'Open KRA folder',
            icon: kra.icon,
            color: AppColors.kra(kra),
            onTap: (context) => _openExplorer(context, KraExplorerLaunch(kra: kra)),
          ),
        );
      }
      for (final criterion in (kraEntry['criteria'] as List? ?? []).whereType<Map>()) {
        final cName = criterion['name']?.toString() ?? '';
        final cId = criterion['id']?.toString();
        if (cId == null) continue;
        if (cName.toLowerCase().contains(q)) {
          hits.add(
            _SearchHit(
              label: cName,
              subtitle: '${kra.code} · Criterion',
              icon: Icons.folder_outlined,
              color: AppColors.kra(kra),
              onTap: (context) => _openExplorer(
                context,
                KraExplorerLaunch(kra: kra, criterionId: cId),
              ),
            ),
          );
        }
        for (final indicator in (criterion['indicators'] as List? ?? []).whereType<Map>()) {
          final iName = indicator['name']?.toString() ?? '';
          final iId = indicator['id']?.toString();
          if (iId == null) continue;
          if (iName.toLowerCase().contains(q)) {
            hits.add(
              _SearchHit(
                label: iName,
                subtitle: '${kra.code} · Indicator',
                icon: Icons.description_outlined,
                color: AppColors.kra(kra),
                onTap: (context) => _openExplorer(
                  context,
                  KraExplorerLaunch(
                    kra: kra,
                    criterionId: cId,
                    indicatorId: iId,
                  ),
                ),
              ),
            );
          }
        }
      }
    }
    return hits;
  }

  void _openExplorer(BuildContext context, KraExplorerLaunch launch) {
    Navigator.pushNamed(context, AppRoutes.kraExplorer, arguments: launch);
  }

  Future<void> _openFilters() async {
    DocumentStatus? status = _statusFilter;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModal) {
            return Padding(
              padding: EdgeInsets.fromLTRB(
                20,
                12,
                20,
                20 + MediaQuery.paddingOf(context).bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Filter by status',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ChoiceChip(
                        label: const Text('All statuses'),
                        selected: status == null,
                        onSelected: (_) => setModal(() => status = null),
                      ),
                      for (final value in DocumentStatus.values
                          .where((v) => v != DocumentStatus.draft))
                        ChoiceChip(
                          label: Text(value.label),
                          selected: status == value,
                          onSelected: (_) => setModal(() => status = value),
                        ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: () {
                      setState(() => _statusFilter = status);
                      Navigator.pop(context);
                    },
                    child: const Text('Apply'),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AppState.instance,
      builder: (context, _) {
        final allDocs = AppState.instance.documents;
        final docs = _filtered(allDocs);
        final query = _search.text.trim();
        final searching = query.isNotEmpty;
        final catalogHits = _catalogHits(query);
        final hasActiveFilter = _statusFilter != null || searching;

        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            title: const Text('My Documents'),
            actions: [
              IconButton(
                tooltip: 'Refresh',
                onPressed: AppState.instance.isSignedIn
                    ? () => AppState.instance.refreshData(
                          label: 'Refreshing documents...',
                        )
                    : null,
                icon: const Icon(Icons.refresh_rounded),
              ),
              IconButton(
                tooltip: 'Filter',
                onPressed: _openFilters,
                icon: Badge(
                  isLabelVisible: _statusFilter != null,
                  child: const Icon(Icons.filter_list_rounded),
                ),
              ),
            ],
          ),
          floatingActionButton: FloatingActionButton.extended(
            backgroundColor: AppColors.navy,
            foregroundColor: Colors.white,
            onPressed: () {
              Navigator.pushNamed(context, AppRoutes.uploadDocument);
            },
            icon: const Icon(Icons.add),
            label: const Text('Add document'),
          ),
          body: _loading
              ? const LoadingState(message: 'Loading your documents…')
              : RefreshIndicator(
                  onRefresh: () => AppState.instance.refreshData(
                    label: 'Refreshing documents...',
                  ),
                  child: CustomScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    slivers: [
                      const SliverPadding(
                        padding: EdgeInsets.fromLTRB(16, 12, 16, 8),
                        sliver: SliverToBoxAdapter(
                          child: PreparationPeriodCard(compact: true),
                        ),
                      ),
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                        sliver: SliverToBoxAdapter(
                          child: KraFolderOverview(
                            documents: _statusFilter == null
                                ? allDocs
                                : allDocs
                                    .where((d) => d.status == _statusFilter)
                                    .toList(),
                          ),
                        ),
                      ),
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                        sliver: SliverToBoxAdapter(
                          child: TextField(
                            controller: _search,
                            onChanged: (_) => setState(() {}),
                            decoration: InputDecoration(
                              hintText: 'Search KRA, criterion, indicator, or file',
                              prefixIcon: const Icon(Icons.search_rounded),
                              filled: true,
                              fillColor: Colors.white,
                              suffixIcon: _search.text.isEmpty
                                  ? null
                                  : IconButton(
                                      onPressed: () {
                                        _search.clear();
                                        setState(() {});
                                      },
                                      icon: const Icon(Icons.close_rounded),
                                    ),
                            ),
                          ),
                        ),
                      ),
                      if (searching) ...[
                        SliverPadding(
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                          sliver: SliverToBoxAdapter(
                            child: Text(
                              'Search results',
                              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.navy,
                                  ),
                            ),
                          ),
                        ),
                        if (catalogHits.isNotEmpty)
                          SliverList(
                            delegate: SliverChildBuilderDelegate(
                              (context, index) {
                                final hit = catalogHits[index];
                                return Padding(
                                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                                  child: _SearchResultTile(hit: hit),
                                );
                              },
                              childCount: catalogHits.length,
                            ),
                          ),
                        if (docs.isNotEmpty)
                          SliverList(
                            delegate: SliverChildBuilderDelegate(
                              (context, index) {
                                final doc = docs[index];
                                return Padding(
                                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                                  child: _DocumentSearchTile(
                                    document: doc,
                                    onOpenDocument: () {
                                      Navigator.pushNamed(
                                        context,
                                        AppRoutes.documentDetails,
                                        arguments: doc.id,
                                      );
                                    },
                                    onOpenLocation: () {
                                      if (doc.indicatorId != null) {
                                        _openExplorer(
                                          context,
                                          KraExplorerLaunch(
                                            kra: doc.kra,
                                            criterionId: doc.criterionId,
                                            indicatorId: doc.indicatorId,
                                          ),
                                        );
                                      } else {
                                        _openExplorer(
                                          context,
                                          KraExplorerLaunch(kra: doc.kra),
                                        );
                                      }
                                    },
                                  ),
                                );
                              },
                              childCount: docs.length,
                            ),
                          ),
                        if (catalogHits.isEmpty && docs.isEmpty)
                          SliverFillRemaining(
                            hasScrollBody: false,
                            child: EmptyState(
                              icon: Icons.search_off_rounded,
                              title: 'No matches',
                              message: hasActiveFilter
                                  ? 'Try another term or clear filters.'
                                  : 'Try a KRA name, criterion, indicator, or file title.',
                              actionLabel: 'Clear search',
                              onAction: () {
                                setState(() {
                                  _search.clear();
                                  _statusFilter = null;
                                });
                              },
                            ),
                          ),
                      ],
                      const SliverPadding(padding: EdgeInsets.only(bottom: 100)),
                    ],
                  ),
                ),
        );
      },
    );
  }
}

class _SearchHit {
  const _SearchHit({
    required this.label,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String label;
  final String subtitle;
  final IconData icon;
  final Color color;
  final void Function(BuildContext context) onTap;
}

class _SearchResultTile extends StatelessWidget {
  const _SearchResultTile({required this.hit});

  final _SearchHit hit;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => hit.onTap(context),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.divider),
          ),
          child: Row(
            children: [
              Icon(hit.icon, color: hit.color),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      hit.label,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppColors.navy,
                      ),
                    ),
                    Text(
                      hit.subtitle,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

class _DocumentSearchTile extends StatelessWidget {
  const _DocumentSearchTile({
    required this.document,
    required this.onOpenDocument,
    required this.onOpenLocation,
  });

  final FacultyDocument document;
  final VoidCallback onOpenDocument;
  final VoidCallback onOpenLocation;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onOpenDocument,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppColors.divider),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.insert_drive_file_outlined, color: AppColors.kra(document.kra)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      document.title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppColors.navy,
                      ),
                    ),
                    Text(
                      '${document.kra.code} · ${document.status.label}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Open in folder',
                onPressed: onOpenLocation,
                icon: const Icon(Icons.folder_open_outlined, size: 20),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
