import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/common.dart';
import '../../widgets/kra_card.dart';
import '../../widgets/progress_ring.dart';
import '../../widgets/status_badge.dart';

class AssessmentScreen extends StatefulWidget {
  const AssessmentScreen({super.key});

  @override
  State<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends State<AssessmentScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(
      length: 2,
      vsync: this,
      initialIndex: AppState.instance.assessmentTabIndex.clamp(0, 1),
    );
    _tabs.addListener(_onTabChanged);
    AppState.instance.addListener(_syncFromAppState);
  }

  void _onTabChanged() {
    if (_tabs.indexIsChanging) return;
    if (AppState.instance.assessmentTabIndex != _tabs.index) {
      AppState.instance.setAssessmentTab(_tabs.index);
    }
  }

  void _syncFromAppState() {
    final index = AppState.instance.assessmentTabIndex.clamp(0, 1);
    if (_tabs.index != index) {
      _tabs.animateTo(index);
    }
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_syncFromAppState);
    _tabs.removeListener(_onTabChanged);
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assessment'),
        bottom: TabBar(
          controller: _tabs,
          indicatorColor: AppColors.gold,
          labelColor: Colors.white,
          unselectedLabelColor: const Color(0xFFB7C5D3),
          tabs: const [
            Tab(text: 'KRA scores'),
            Tab(text: 'Compliance'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: const [
          _KraScoresTab(),
          _ComplianceTab(),
        ],
      ),
    );
  }
}

class _KraScoresTab extends StatelessWidget {
  const _KraScoresTab();

  @override
  Widget build(BuildContext context) {
    final scores = AppState.instance.kraScores;
    final total = scores.fold<int>(0, (sum, item) => sum + item.currentPoints);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
      children: [
        const InfoBanner(
          message:
              'Point values are mock previews for this prototype. Official scoring will be applied later.',
        ),
        const SizedBox(height: 14),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                ProgressRing(
                  progress: total / 100,
                  size: 76,
                  child: Text(
                    '$total',
                    style: const TextStyle(
                      fontWeight: FontWeight.w800,
                      color: AppColors.navy,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Total accumulated points',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 16,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '72 of 100 toward Instructor II in this self-assessment preview.',
                        style: TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 13,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        const SectionHeader(title: 'Performance by KRA'),
        for (final score in scores) ...[
          KraCard(
            score: score,
            onTap: () {
              Navigator.pushNamed(
                context,
                AppRoutes.kraDetails,
                arguments: score.type,
              );
            },
          ),
          const SizedBox(height: 10),
        ],
      ],
    );
  }
}

class _ComplianceTab extends StatelessWidget {
  const _ComplianceTab();

  @override
  Widget build(BuildContext context) {
    final items = AppState.instance.requirements;
    final completed =
        items.where((r) => r.status == RequirementStatus.completed).length;
    final missing =
        items.where((r) => r.status == RequirementStatus.missing).length;
    final pending = items
        .where((r) =>
            r.status == RequirementStatus.pending ||
            r.status == RequirementStatus.needsRevision)
        .length;
    final revision = items
        .where((r) => r.status == RequirementStatus.needsRevision)
        .length;
    final ratio = items.isEmpty ? 0.0 : completed / items.length;
    final percent = (ratio * 100).round();

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                Row(
                  children: [
                    ProgressRing(
                      progress: ratio,
                      size: 84,
                      child: Text(
                        items.isEmpty ? '—' : '$percent%',
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          color: AppColors.navy,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        items.isEmpty
                            ? 'No documentary requirements are loaded yet. Upload evidence or refresh after the API is available.'
                            : 'Overall compliance with the documentary requirements in this preview.',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    StatTile(value: '$completed', label: 'Completed', color: AppColors.success),
                    const SizedBox(width: 8),
                    StatTile(value: '$missing', label: 'Missing', color: AppColors.error),
                    const SizedBox(width: 8),
                    StatTile(value: '$pending', label: 'Pending', color: AppColors.warning),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    StatTile(
                      value: '$revision',
                      label: 'Needs revision',
                      color: AppColors.error,
                    ),
                    const SizedBox(width: 8),
                    StatTile(
                      value: '${items.where((r) => r.status == RequirementStatus.pending).length}',
                      label: 'Pending validation',
                      color: AppColors.info,
                    ),
                    const SizedBox(width: 8),
                    StatTile(
                      value: '$completed',
                      label: 'Validated',
                      color: AppColors.navy,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        for (final kra in KraType.values) ...[
          SectionHeader(title: kra.label),
          _KraRequirementGroup(
            kra: kra,
            items: items.where((r) => r.kra == kra).toList(),
          ),
          const SizedBox(height: 16),
        ],
      ],
    );
  }
}

class _KraRequirementGroup extends StatelessWidget {
  const _KraRequirementGroup({required this.kra, required this.items});

  final KraType kra;
  final List<RequirementItem> items;

  int _count(RequirementStatus status) =>
      items.where((r) => r.status == status).length;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Row(
              children: [
                _CountChip(label: 'Completed', value: _count(RequirementStatus.completed), color: AppColors.success),
                const SizedBox(width: 6),
                _CountChip(label: 'Missing', value: _count(RequirementStatus.missing), color: AppColors.error),
                const SizedBox(width: 6),
                _CountChip(
                  label: 'Pending',
                  value: _count(RequirementStatus.pending) +
                      _count(RequirementStatus.needsRevision),
                  color: AppColors.warning,
                ),
              ],
            ),
            const Divider(height: 20),
            for (final item in items)
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  item.title,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                ),
                subtitle: Text(
                  item.description,
                  style: const TextStyle(fontSize: 12),
                ),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    RequirementBadge(status: item.status),
                    if (item.status != RequirementStatus.completed) ...[
                      const SizedBox(height: 6),
                      const Text(
                        'View',
                        style: TextStyle(
                          color: AppColors.navy,
                          fontWeight: FontWeight.w700,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ],
                ),
                onTap: item.status == RequirementStatus.completed
                    ? null
                    : () {
                        Navigator.pushNamed(
                          context,
                          AppRoutes.requirementDetails,
                          arguments: item,
                        );
                      },
              ),
          ],
        ),
      ),
    );
  }
}

class _CountChip extends StatelessWidget {
  const _CountChip({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          children: [
            Text(
              '$value',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
            Text(
              label,
              style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

class KraDetailsScreen extends StatelessWidget {
  const KraDetailsScreen({super.key, required this.type});

  final KraType type;

  @override
  Widget build(BuildContext context) {
    final score = AppState.instance.kraScore(type);
    final docs = AppState.instance.documents.where((d) => d.kra == type).toList();
    final color = AppColors.kra(type);

    return Scaffold(
      appBar: AppBar(title: Text(type.label)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: AppColors.kraSoft(type),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: Icon(type.icon, color: color),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              type.label,
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 18,
                              ),
                            ),
                            Text(
                              score.statusLabel,
                              style: TextStyle(color: color, fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        '${score.currentPoints}',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: color,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  LinearProgressLabeled(progress: score.progress, color: color),
                  const SizedBox(height: 8),
                  Text(
                    '${(score.progress * 100).round()}% of ${score.targetPoints} preview points  ·  ${score.documentCount} supporting documents',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          const SectionHeader(title: 'Breakdown'),
          const InfoBanner(
            message:
                'These line items are illustrative mock values. Scoring rules are not applied in this UI prototype.',
          ),
          const SizedBox(height: 10),
          for (final item in score.breakdown)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                title: Text(
                  item.title,
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                subtitle: Text(item.note),
                trailing: Text(
                  '${item.points} pts',
                  style: TextStyle(
                    fontWeight: FontWeight.w800,
                    color: color,
                  ),
                ),
              ),
            ),
          const SizedBox(height: 8),
          const SectionHeader(title: 'Supporting documents'),
          if (docs.isEmpty)
            const EmptyState(
              icon: Icons.folder_off_outlined,
              title: 'No documents yet',
              message: 'Upload documentary evidence for this KRA to start building your record.',
            )
          else
            for (final doc in docs)
              ListTile(
                contentPadding: const EdgeInsets.symmetric(vertical: 4),
                leading: const Icon(Icons.description_outlined),
                title: Text(doc.title, maxLines: 2, overflow: TextOverflow.ellipsis),
                subtitle: Text(doc.category.label),
                trailing: StatusBadge(status: doc.status, compact: true),
                onTap: () {
                  Navigator.pushNamed(
                    context,
                    AppRoutes.documentDetails,
                    arguments: doc.id,
                  );
                },
              ),
          const SizedBox(height: 12),
          PrimaryButton(
            label: 'Upload a document',
            icon: Icons.upload_file_outlined,
            onPressed: () {
              Navigator.pushNamed(
                context,
                AppRoutes.uploadDocument,
                arguments: type,
              );
            },
          ),
        ],
      ),
    );
  }
}

class RequirementDetailsScreen extends StatelessWidget {
  const RequirementDetailsScreen({super.key, required this.item});

  final RequirementItem item;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Requirement')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          RequirementBadge(status: item.status),
          const SizedBox(height: 12),
          Text(
            item.title,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            item.kra.label,
            style: TextStyle(
              color: AppColors.kra(item.kra),
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            item.description,
            style: const TextStyle(
              fontSize: 15,
              height: 1.45,
              color: AppColors.textSecondary,
            ),
          ),
          if (item.hint != null) ...[
            const SizedBox(height: 16),
            InfoBanner(
              message: item.hint!,
              icon: Icons.lightbulb_outline_rounded,
              color: AppColors.warning,
              background: AppColors.warningSoft,
            ),
          ],
          const SizedBox(height: 24),
          PrimaryButton(
            label: 'Upload supporting document',
            icon: Icons.upload_file_outlined,
            onPressed: () {
              Navigator.pushNamed(
                context,
                AppRoutes.uploadDocument,
                arguments: item.kra,
              );
            },
          ),
        ],
      ),
    );
  }
}
