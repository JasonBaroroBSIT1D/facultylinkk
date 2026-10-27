import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/assigned_reviewer_card.dart';
import '../../widgets/app_logo.dart';
import '../../widgets/common.dart';
import '../../widgets/kra_card.dart';
import '../../widgets/preparation_period_card.dart';
import '../../widgets/progress_ring.dart';
import '../../widgets/simulation_result_card.dart';
import '../../widgets/status_badge.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final faculty = state.faculty;
        final dash = state.dashboard;
        final unread = state.unreadNotificationCount;

        return Scaffold(
          body: RefreshIndicator(
            onRefresh: () => state.refreshData(label: 'Refreshing documents...'),
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              slivers: [
              SliverToBoxAdapter(child: _Header(faculty: faculty, unread: unread)),
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
                sliver: SliverList.list(
                  children: [
                    _SimulationSummary(simulation: dash.simulation),
                    const SizedBox(height: 12),
                    const PreparationPeriodCard(compact: true),
                    const SizedBox(height: 12),
                    const AssignedReviewerCard(compact: true),
                    const SizedBox(height: 12),
                    _ProgressOverview(dash: dash),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        StatTile(
                          value: '${state.validatedCount}',
                          label: 'Validated',
                          color: AppColors.success,
                          onTap: () => state.openDocuments(),
                        ),
                        const SizedBox(width: 8),
                        StatTile(
                          value: '${state.pendingCount}',
                          label: 'Pending review',
                          color: AppColors.warning,
                          onTap: () => state.openDocuments(),
                        ),
                        const SizedBox(width: 8),
                        StatTile(
                          value: '${state.actionRequiredCount}',
                          label: 'Needs action',
                          color: AppColors.error,
                          onTap: () => state.openDocuments(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 22),
                    const SectionHeader(title: 'Key Result Areas'),
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      mainAxisSpacing: 10,
                      crossAxisSpacing: 10,
                      childAspectRatio: 0.82,
                      children: [
                        for (final kra in dash.kraScores)
                          KraCard(
                            score: kra,
                            compact: true,
                            onTap: () {
                              Navigator.pushNamed(
                                context,
                                AppRoutes.kraDetails,
                                arguments: kra.type,
                              );
                            },
                          ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    PrimaryButton(
                      label: 'View Assessment',
                      icon: Icons.insights_outlined,
                      onPressed: () {
                        state.openAssessment();
                        Navigator.pushNamed(context, AppRoutes.assessment);
                      },
                    ),
                    const SizedBox(height: 10),
                    SecondaryButton(
                      label: 'Monitor compliance',
                      icon: Icons.fact_check_outlined,
                      onPressed: () {
                        state.openAssessment(innerTab: 1);
                        Navigator.pushNamed(context, AppRoutes.assessment);
                      },
                    ),
                    const SizedBox(height: 22),
                    SectionHeader(
                      title: 'Recent document activity',
                      actionLabel: 'See all',
                      onAction: state.openDocuments,
                    ),
                    ...dash.recentActivity.map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: _ActivityTile(item: item),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SectionHeader(
                      title: 'Recent reviewer feedback',
                      actionLabel: 'Documents',
                      onAction: state.openDocuments,
                    ),
                    ...dash.recentFeedback.map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: _FeedbackTile(item: item),
                      ),
                    ),
                    const SizedBox(height: 12),
                    SectionHeader(
                      title: 'Notifications',
                      actionLabel: 'Open',
                      onAction: state.openNotifications,
                    ),
                    if (state.notifications.isEmpty)
                      const InfoBanner(
                        message: 'You have no notifications right now.',
                      )
                    else
                      ...state.notifications.take(3).map(
                            (n) => Padding(
                              padding: const EdgeInsets.only(bottom: 8),
                              child: ListTile(
                                onTap: state.openNotifications,
                                tileColor: AppColors.surface,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(14),
                                  side: const BorderSide(color: AppColors.divider),
                                ),
                                leading: Icon(n.kind.icon, color: AppColors.navy),
                                title: Text(
                                  n.title,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 13,
                                  ),
                                ),
                                subtitle: Text(
                                  n.message,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                trailing: n.visualState ==
                                        NotificationVisualState.read
                                    ? null
                                    : const Icon(
                                        Icons.circle,
                                        size: 8,
                                        color: AppColors.navy,
                                      ),
                              ),
                            ),
                          ),
                    const SizedBox(height: 8),
                    PrimaryButton(
                      label: 'Simulate Rank Upgrade',
                      icon: Icons.trending_up_rounded,
                      onPressed: state.openSimulation,
                    ),
                  ],
                ),
              ),
            ],
            ),
          ),
        );
      },
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.faculty, required this.unread});

  final FacultyProfile faculty;
  final int unread;

  @override
  Widget build(BuildContext context) {
    final top = MediaQuery.paddingOf(context).top;
    final department = [
      if (faculty.department.trim().isNotEmpty) faculty.department.trim(),
      if (faculty.college.trim().isNotEmpty) faculty.college.trim(),
    ].join(' · ');

    return ClipRRect(
      borderRadius: const BorderRadius.vertical(bottom: Radius.circular(22)),
      child: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.navyDark,
              AppColors.navy,
              Color(0xFF0A4A6E),
            ],
          ),
        ),
        child: Padding(
          padding: EdgeInsets.fromLTRB(16, top + 10, 12, 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Expanded(
                    child: AppLogo(
                      size: 30,
                      showWordmark: true,
                      light: true,
                      horizontal: true,
                    ),
                  ),
                  _HeaderIconButton(
                    tooltip: 'Notifications',
                    onPressed: AppState.instance.openNotifications,
                    child: Badge(
                      isLabelVisible: unread > 0,
                      backgroundColor: AppColors.gold,
                      textColor: AppColors.navyDark,
                      label: Text('$unread'),
                      child: const Icon(
                        Icons.notifications_none_rounded,
                        color: Colors.white,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  InkWell(
                    onTap: AppState.instance.openProfile,
                    customBorder: const CircleBorder(),
                    child: FacultyAvatar(
                      name: faculty.fullName,
                      size: 36,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Welcome back, ${faculty.firstName}',
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.72),
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          faculty.fullName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            height: 1.15,
                          ),
                        ),
                        if (department.isNotEmpty) ...[
                          const SizedBox(height: 2),
                          Text(
                            department,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.58),
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(width: 10),
                  Flexible(
                    child: Align(
                      alignment: Alignment.centerRight,
                      child: _HeaderChip(
                        icon: Icons.workspace_premium_outlined,
                        label: faculty.currentRank,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _HeaderIconButton extends StatelessWidget {
  const _HeaderIconButton({
    required this.tooltip,
    required this.onPressed,
    required this.child,
  });

  final String tooltip;
  final VoidCallback onPressed;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.white.withValues(alpha: 0.10),
        shape: const CircleBorder(),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: onPressed,
          child: SizedBox(
            width: 38,
            height: 38,
            child: Center(child: child),
          ),
        ),
      ),
    );
  }
}

class _HeaderChip extends StatelessWidget {
  const _HeaderChip({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.20),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.gold.withValues(alpha: 0.45)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppColors.goldSoft),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: AppColors.goldSoft,
                fontWeight: FontWeight.w700,
                fontSize: 11,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProgressOverview extends StatelessWidget {
  const _ProgressOverview({required this.dash});

  final DashboardSnapshot dash;

  @override
  Widget build(BuildContext context) {
    final percent = (dash.overallProgress * 100).round();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            ProgressRing(
              progress: dash.overallProgress,
              child: Text(
                '$percent%',
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  color: AppColors.navy,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Overall KRA progress',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${dash.totalPoints} of ${dash.targetPoints} target points',
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Documents ${dash.documentCompletionPercent}% complete',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: AppColors.navy,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Preview scores only. Official evaluation is separate.',
                    style: TextStyle(fontSize: 11, color: AppColors.textTertiary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SimulationSummary extends StatelessWidget {
  const _SimulationSummary({required this.simulation});

  final RankSimulation simulation;

  @override
  Widget build(BuildContext context) {
    return SimulationResultCard(
      simulation: simulation,
      compact: true,
      onTap: AppState.instance.openSimulation,
    );
  }
}

class _ActivityTile extends StatelessWidget {
  const _ActivityTile({required this.item});

  final RecentActivity item;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${item.subtitle} · ${item.timeLabel}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          StatusBadge(status: item.status, compact: true),
        ],
      ),
    );
  }
}

class _FeedbackTile extends StatelessWidget {
  const _FeedbackTile({required this.item});

  final ReviewerFeedbackPreview item;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.warningSoft,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            item.documentTitle,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
          ),
          const SizedBox(height: 4),
          Text(
            item.message,
            style: const TextStyle(
              fontSize: 13,
              height: 1.35,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            item.timeLabel,
            style: const TextStyle(fontSize: 11, color: AppColors.textTertiary),
          ),
        ],
      ),
    );
  }
}
