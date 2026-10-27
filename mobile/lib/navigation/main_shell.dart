import 'package:flutter/material.dart';

import '../data/app_state.dart';
import '../navigation/app_routes.dart';
import '../screens/dashboard/dashboard_screen.dart';
import '../screens/documents/documents_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/simulation/simulation_screen.dart';
import '../theme/app_colors.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> with WidgetsBindingObserver {
  static const _tabs = [
    DashboardScreen(),
    DocumentsScreen(),
    SimulationScreen(),
    NotificationsScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (AppState.instance.mustChangePassword) {
        Navigator.pushNamedAndRemoveUntil(
          context,
          AppRoutes.changePassword,
          (_) => false,
          arguments: const {'requiredFirstLogin': true},
        );
      }
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      AppState.instance.refreshData(
        label: 'Refreshing documents...',
        soft: true,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final unread = state.unreadNotificationCount;
        return Scaffold(
          body: Column(
            children: [
              if (state.busyMessage != null)
                LinearProgressIndicator(
                  minHeight: 3,
                  backgroundColor: AppColors.divider,
                  color: AppColors.navy,
                ),
              if (state.busyMessage != null)
                Material(
                  color: AppColors.navy.withValues(alpha: 0.06),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      state.busyMessage!,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              Expanded(
                child: IndexedStack(
                  index: state.mainTabIndex,
                  children: _tabs,
                ),
              ),
            ],
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: state.mainTabIndex,
            onDestinationSelected: state.setMainTab,
            destinations: [
              const NavigationDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home_outlined, color: AppColors.navy),
                label: 'Home',
              ),
              const NavigationDestination(
                icon: Icon(Icons.description_outlined),
                selectedIcon: Icon(
                  Icons.description_outlined,
                  color: AppColors.navy,
                ),
                label: 'Documents',
              ),
              const NavigationDestination(
                icon: Icon(Icons.track_changes_outlined),
                selectedIcon: Icon(
                  Icons.track_changes_outlined,
                  color: AppColors.navy,
                ),
                label: 'Simulation',
              ),
              NavigationDestination(
                icon: Badge(
                  isLabelVisible: unread > 0,
                  label: Text('$unread'),
                  backgroundColor: AppColors.error,
                  child: const Icon(Icons.notifications_outlined),
                ),
                selectedIcon: Badge(
                  isLabelVisible: unread > 0,
                  label: Text('$unread'),
                  backgroundColor: AppColors.error,
                  child: const Icon(
                    Icons.notifications_outlined,
                    color: AppColors.navy,
                  ),
                ),
                label: 'Notifications',
              ),
              const NavigationDestination(
                icon: Icon(Icons.person_outline_rounded),
                selectedIcon: Icon(
                  Icons.person_outline_rounded,
                  color: AppColors.navy,
                ),
                label: 'Profile',
              ),
            ],
          ),
        );
      },
    );
  }
}
