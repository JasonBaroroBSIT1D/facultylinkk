import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../models/enums.dart';
import '../../models/models.dart';
import '../../navigation/app_routes.dart';
import '../../theme/app_colors.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notification_tile.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  Future<void> _openNotification(BuildContext context, String id) async {
    final state = AppState.instance;
    AppNotification? item;
    for (final notification in state.notifications) {
      if (notification.id == id) {
        item = notification;
        break;
      }
    }
    if (item == null) return;
    state.markNotificationRead(id);

    if (item.relatedDocumentId != null) {
      Navigator.pushNamed(
        context,
        AppRoutes.documentDetails,
        arguments: item.relatedDocumentId,
      );
      return;
    }
    if (item.kind == NotificationKind.rankSimulationUpdated) {
      if (ModalRoute.of(context)?.settings.name == AppRoutes.notifications) {
        Navigator.pop(context);
      }
      state.openSimulation();
      return;
    }
    if (item.relatedKra != null) {
      Navigator.pushNamed(
        context,
        AppRoutes.kraDetails,
        arguments: item.relatedKra,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final items = state.notifications;
        return Scaffold(
          appBar: AppBar(
            title: const Text('Notifications'),
            actions: [
              if (items.isNotEmpty)
                PopupMenuButton<String>(
                  onSelected: (value) async {
                    if (value == 'read') {
                      state.markAllNotificationsRead();
                      showAppSnackBar(context, 'All notifications marked as read.');
                    } else if (value == 'clear') {
                      final confirmed = await showConfirmDialog(
                        context: context,
                        title: 'Clear notifications?',
                        message:
                            'This removes all notifications from this preview. They are not stored on a server yet.',
                        confirmLabel: 'Clear',
                        destructive: true,
                      );
                      if (confirmed) state.clearNotifications();
                    }
                  },
                  itemBuilder: (context) => const [
                    PopupMenuItem(
                      value: 'read',
                      child: Text('Mark all as read'),
                    ),
                    PopupMenuItem(
                      value: 'clear',
                      child: Text('Clear notifications'),
                    ),
                  ],
                ),
            ],
          ),
          body: items.isEmpty
              ? const EmptyState(
                  icon: Icons.notifications_none_rounded,
                  title: 'No notifications',
                  message:
                      'Updates about document status, reviewer feedback, and missing requirements will appear here.',
                )
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return Dismissible(
                      key: ValueKey(item.id),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 20),
                        decoration: BoxDecoration(
                          color: AppColors.successSoft,
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Text(
                          'Mark as read',
                          style: TextStyle(
                            color: AppColors.success,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      confirmDismiss: (_) async {
                        state.markNotificationRead(item.id);
                        return false;
                      },
                      child: NotificationTile(
                        notification: item,
                        onTap: () => _openNotification(context, item.id),
                      ),
                    );
                  },
                ),
        );
      },
    );
  }
}
