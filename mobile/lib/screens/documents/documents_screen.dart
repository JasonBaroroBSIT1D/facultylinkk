import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/mock_kra_catalog.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
// KraExplorerScreen opened via AppRoutes.kraExplorer
import '../../theme/app_colors.dart';
import '../../widgets/common.dart';
import '../../widgets/document_card.dart';
import '../../widgets/preparation_period_card.dart';
class DocumentsScreen extends StatefulWidget {
  const DocumentsScreen({super.key});

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  final _search = TextEditingController();
  KraType _activeKra = KraType.instruction;
  DocumentStatus? _statusFilter;
  bool _loading = true;
  Map<String, String> _criterionNames = {};
  Map<String, String> _indicatorNames = {};
  final Set<String> _collapsedCriteria = {};

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      final catalog = await MockKraCatalog.load();
      final names = <String, String>{};
      final indicators = <String, String>{};
      final raw = catalog['kras'];
      if (raw is List) {
        for (final kra in raw.whereType<Map>()) {
          for (final criterion in (kra['criteria'] as List? ?? []).whereType<Map>()) {
            names[criterion['id']?.toString() ?? ''] = criterion['name']?.toString() ?? '';
            for (final indicator in (criterion['indicators'] as List? ?? []).whereType<Map>()) {
              indicators[indicator['id']?.toString() ?? ''] =
                  indicator['name']?.toString() ?? '';
            }
          }
        }
      }
      if (mounted) {
        setState(() {
          _criterionNames = names;
          _indicatorNames = indicators;
        });
      }
    } catch (_) {
      // Keep list usable without labels.
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
          doc.category.label.toLowerCase().contains(query);
      final matchesStatus = _statusFilter == null || doc.status == _statusFilter;
      return matchesQuery && matchesStatus;
    }).toList();
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
                      for (final value in DocumentStatus.values)
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
        final docs = _filtered(AppState.instance.documents);
        final hasActiveFilter = _statusFilter != null || _search.text.isNotEmpty;
        final kraCounts = {
          for (final kra in KraType.values)
            kra: docs.where((d) => d.kra == kra).length,
        };
        final activeDocs = docs.where((d) => d.kra == _activeKra).toList();
        final groups = _criterionGroups(activeDocs);

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
                        child: _KraFolderOverview(
                          documents: AppState.instance.documents,
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
                            hintText: 'Search KRA, criterion, or file',
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
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                      sliver: SliverToBoxAdapter(
                        child: _KraTabBar(
                          active: _activeKra,
                          counts: kraCounts,
                          onSelected: (kra) => setState(() => _activeKra = kra),
                        ),
                      ),
                    ),
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                      sliver: SliverToBoxAdapter(
                        child: _KraBanner(
                          kra: _activeKra,
                          count: kraCounts[_activeKra] ?? 0,
                        ),
                      ),
                    ),
                    if (docs.isEmpty)
                      SliverFillRemaining(
                        hasScrollBody: false,
                        child: EmptyState(
                          icon: Icons.folder_off_outlined,
                          title: hasActiveFilter
                              ? 'No matching documents'
                              : 'No documents uploaded',
                          message: hasActiveFilter
                              ? 'Try another search or clear your filters.'
                              : 'Upload supporting documents under the correct KRA and criterion.',
                          actionLabel: hasActiveFilter ? 'Clear filters' : 'Upload document',
                          onAction: hasActiveFilter
                              ? () {
                                  setState(() {
                                    _search.clear();
                                    _statusFilter = null;
                                  });
                                }
                              : () {
                                  Navigator.pushNamed(
                                    context,
                                    AppRoutes.uploadDocument,
                                  );
                                },
                        ),
                      )
                    else if (activeDocs.isEmpty)
                      const SliverFillRemaining(
                        hasScrollBody: false,
                        child: EmptyState(
                          icon: Icons.inbox_outlined,
                          title: 'No documents in this KRA',
                          message: 'Switch tabs or upload evidence for this area.',
                        ),
                      )
                    else
                      SliverPadding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 100),
                        sliver: SliverList.builder(
                          itemCount: groups.length,
                          itemBuilder: (context, index) {
                            final entry = groups.entries.elementAt(index);
                            final key = entry.key;
                            final open = !_collapsedCriteria.contains(key);
                            return _CriterionFold(
                              title: key,
                              count: entry.value.length,
                              open: open,
                              onToggle: () {
                                setState(() {
                                  if (open) {
                                    _collapsedCriteria.add(key);
                                  } else {
                                    _collapsedCriteria.remove(key);
                                  }
                                });
                              },
                              children: [
                                for (var i = 0; i < entry.value.length; i++) ...[
                                  if (i > 0)
                                    const Divider(height: 1, color: AppColors.divider),
                                  DocumentCard(
                                    document: entry.value[i],
                                    onTap: () {
                                      Navigator.pushNamed(
                                        context,
                                        AppRoutes.documentDetails,
                                        arguments: entry.value[i].id,
                                      );
                                    },
                                    // Opens basic info first; file opens from details.
                                    onView: () {
                                      Navigator.pushNamed(
                                        context,
                                        AppRoutes.documentDetails,
                                        arguments: entry.value[i].id,
                                      );
                                    },
                                  ),
                                ],
                              ],
                            );
                          },
                        ),
                      ),
                  ],
                ),
              ),
        );
      },
    );
  }

  Map<String, List<FacultyDocument>> _criterionGroups(List<FacultyDocument> docs) {
    final groups = <String, List<FacultyDocument>>{};
    for (final doc in docs) {
      final criterion = doc.criterionId;
      final indicator = doc.indicatorId;
      String label;
      if (criterion != null && (_criterionNames[criterion] ?? '').isNotEmpty) {
        label = _criterionNames[criterion]!;
        if (indicator != null && (_indicatorNames[indicator] ?? '').isNotEmpty) {
          label = '$label · ${_indicatorNames[indicator]}';
        }
      } else if (indicator != null && (_indicatorNames[indicator] ?? '').isNotEmpty) {
        label = _indicatorNames[indicator]!;
      } else {
        label = 'Unclassified (needs criterion)';
      }
      groups.putIfAbsent(label, () => []).add(doc);
    }
    return groups;
  }
}

class _KraFolderOverview extends StatelessWidget {
  const _KraFolderOverview({required this.documents});

  final List<FacultyDocument> documents;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'KRA folders',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            fontSize: 15,
            color: AppColors.navy,
          ),
        ),
        const SizedBox(height: 8),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10,
          crossAxisSpacing: 10,
          childAspectRatio: 1.35,
          children: [
            for (final kra in KraType.values)
              _KraFolderCard(
                kra: kra,
                stats: _statsForKra(documents, kra),
                onTap: () {
                  Navigator.pushNamed(context, AppRoutes.kraExplorer, arguments: kra);
                },
              ),
          ],
        ),
      ],
    );
  }

  static _KraFolderStats _statsForKra(List<FacultyDocument> docs, KraType kra) {
    final rows = docs.where((d) => d.kra == kra).toList();
    var pending = 0;
    var approved = 0;
    var revision = 0;
    for (final doc in rows) {
      switch (doc.status) {
        case DocumentStatus.validated:
        case DocumentStatus.systemApproved:
          approved += 1;
        case DocumentStatus.needsRevision:
          revision += 1;
        case DocumentStatus.pendingReview:
        case DocumentStatus.processing:
          pending += 1;
        case DocumentStatus.draft:
        case DocumentStatus.invalid:
          break;
      }
    }
    return _KraFolderStats(
      total: rows.length,
      pending: pending,
      approved: approved,
      revision: revision,
    );
  }
}

class _KraFolderStats {
  const _KraFolderStats({
    required this.total,
    required this.pending,
    required this.approved,
    required this.revision,
  });

  final int total;
  final int pending;
  final int approved;
  final int revision;
}

class _KraFolderCard extends StatelessWidget {
  const _KraFolderCard({
    required this.kra,
    required this.stats,
    required this.onTap,
  });

  final KraType kra;
  final _KraFolderStats stats;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.divider),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(kra.icon, color: AppColors.kra(kra), size: 22),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      kra.code,
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
                kra.shortLabel,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
              ),
              const Spacer(),
              Text(
                '${stats.total} files · ${stats.pending} pending · ${stats.approved} approved',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppColors.navy,
                ),
              ),
              if (stats.revision > 0)
                Text(
                  '${stats.revision} need revision',
                  style: const TextStyle(fontSize: 10, color: AppColors.warning),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _KraTabBar extends StatelessWidget {
  const _KraTabBar({
    required this.active,
    required this.counts,
    required this.onSelected,
  });

  final KraType active;
  final Map<KraType, int> counts;
  final ValueChanged<KraType> onSelected;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final narrow = constraints.maxWidth < 380;
        return Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final kra in KraType.values)
              SizedBox(
                width: narrow
                    ? (constraints.maxWidth - 8) / 2
                    : (constraints.maxWidth - 24) / 4,
                child: _KraTab(
                  kra: kra,
                  count: counts[kra] ?? 0,
                  selected: kra == active,
                  onTap: () => onSelected(kra),
                ),
              ),
          ],
        );
      },
    );
  }
}

class _KraTab extends StatelessWidget {
  const _KraTab({
    required this.kra,
    required this.count,
    required this.selected,
    required this.onTap,
  });

  final KraType kra;
  final int count;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? AppColors.navy : Colors.white,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: selected ? AppColors.navy : AppColors.divider,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                kra.code,
                style: TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 13,
                  color: selected ? Colors.white : AppColors.navy,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '${kra.shortLabel} · $count',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: selected
                      ? Colors.white.withValues(alpha: 0.78)
                      : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _KraBanner extends StatelessWidget {
  const _KraBanner({required this.kra, required this.count});

  final KraType kra;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${kra.code} — ${kra.label}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    color: AppColors.navy,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  count == 0
                      ? 'No uploaded evidence in this area yet.'
                      : '$count document${count == 1 ? '' : 's'} filed under this KRA.',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.kraSoft(kra),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              '$count',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                color: AppColors.kra(kra),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CriterionFold extends StatelessWidget {
  const _CriterionFold({
    required this.title,
    required this.count,
    required this.open,
    required this.onToggle,
    required this.children,
  });

  final String title;
  final int count;
  final bool open;
  final VoidCallback onToggle;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          InkWell(
            onTap: onToggle,
            borderRadius: BorderRadius.circular(14),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
              child: Row(
                children: [
                  Text(
                    open ? '▾' : '▸',
                    style: const TextStyle(
                      color: Color(0xFF0F766E),
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppColors.navy,
                        height: 1.3,
                      ),
                    ),
                  ),
                  Text(
                    '$count',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (open)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: Column(children: children),
            ),
        ],
      ),
    );
  }
}
