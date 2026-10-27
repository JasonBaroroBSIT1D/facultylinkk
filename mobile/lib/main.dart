import 'package:flutter/material.dart';

import 'models/enums.dart';
import 'models/models.dart';
import 'navigation/app_routes.dart';
import 'navigation/main_shell.dart';
import 'screens/auth/forgot_password_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/splash_screen.dart';
import 'screens/assessment/assessment_screen.dart';
import 'screens/documents/document_details_screen.dart';
import 'screens/documents/kra_explorer_screen.dart';
import 'screens/documents/upload_document_screen.dart';
import 'screens/notifications/notifications_screen.dart';
import 'screens/profile/profile_screen.dart';
import 'screens/simulation/simulation_screen.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const FacultyLinkApp());
}

class FacultyLinkApp extends StatelessWidget {
  const FacultyLinkApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FacultyLink',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      initialRoute: AppRoutes.splash,
      onGenerateRoute: (settings) {
        switch (settings.name) {
          case AppRoutes.splash:
            return MaterialPageRoute(builder: (_) => const SplashScreen());
          case AppRoutes.login:
            return MaterialPageRoute(
              builder: (_) => LoginScreen(
                initialEmail: settings.arguments as String?,
              ),
            );
          case AppRoutes.forgotPassword:
            return MaterialPageRoute(
              builder: (_) => ForgotPasswordScreen(
                initialEmail: settings.arguments as String?,
              ),
            );
          case AppRoutes.main:
            return MaterialPageRoute(builder: (_) => const MainShell());
          case AppRoutes.assessment:
            return MaterialPageRoute(
              builder: (_) => const AssessmentScreen(),
            );
          case AppRoutes.notifications:
            return MaterialPageRoute(
              builder: (_) => const NotificationsScreen(),
            );
          case AppRoutes.kraDetails:
            final type = settings.arguments as KraType? ?? KraType.instruction;
            return MaterialPageRoute(
              builder: (_) => KraDetailsScreen(type: type),
            );
          case AppRoutes.documentDetails:
            final id = settings.arguments as String? ?? '';
            return MaterialPageRoute(
              builder: (_) => DocumentDetailsScreen(documentId: id),
            );
          case AppRoutes.uploadDocument:
            final kra = settings.arguments as KraType?;
            return MaterialPageRoute(
              builder: (_) => UploadDocumentScreen(initialKra: kra),
            );
          case AppRoutes.kraExplorer:
            final kra = settings.arguments as KraType? ?? KraType.instruction;
            return MaterialPageRoute(
              builder: (_) => KraExplorerScreen(kra: kra),
            );
          case AppRoutes.requirementDetails:
            final item = settings.arguments as RequirementItem;
            return MaterialPageRoute(
              builder: (_) => RequirementDetailsScreen(item: item),
            );
          case AppRoutes.improvementOpportunities:
            return MaterialPageRoute(
              builder: (_) => const ImprovementOpportunitiesScreen(),
            );
          case AppRoutes.editProfile:
            return MaterialPageRoute(builder: (_) => const EditProfileScreen());
          case AppRoutes.changePassword:
            final args = settings.arguments;
            final requiredFirstLogin =
                args is Map && args['requiredFirstLogin'] == true;
            return MaterialPageRoute(
              builder: (_) => ChangePasswordScreen(
                requiredFirstLogin: requiredFirstLogin,
              ),
            );
          case AppRoutes.notificationSettings:
            return MaterialPageRoute(
              builder: (_) => const NotificationSettingsScreen(),
            );
          case AppRoutes.about:
            return MaterialPageRoute(builder: (_) => const AboutScreen());
          default:
            return MaterialPageRoute(builder: (_) => const LoginScreen());
        }
      },
    );
  }
}
