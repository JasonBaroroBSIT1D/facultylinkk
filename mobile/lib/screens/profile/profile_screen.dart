import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../navigation/app_routes.dart';
import '../../data/app_auth_exception.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/app_logo.dart';
import '../../widgets/app_text_field.dart';
import '../../widgets/assigned_reviewer_card.dart';
import '../../widgets/common.dart';
import '../../widgets/dialogs.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppState.instance;

    return ListenableBuilder(
      listenable: state,
      builder: (context, _) {
        final faculty = state.faculty;
        return Scaffold(
          appBar: AppBar(title: const Text('Profile')),
          body: ListView(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              Center(
                child: Column(
                  children: [
                    FacultyAvatar(name: faculty.fullName, size: 92),
                    const SizedBox(height: 12),
                    Text(
                      faculty.fullName,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      faculty.currentRank,
                      style: const TextStyle(
                        color: AppColors.navy,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      faculty.facultyId,
                      style: const TextStyle(color: AppColors.textTertiary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              const SectionHeader(title: 'Assigned reviewer'),
              const AssignedReviewerCard(),
              const SizedBox(height: 20),
              const SectionHeader(title: 'Academic information'),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: [
                      _ProfileRow(label: 'College', value: faculty.college),
                      _ProfileRow(label: 'Department', value: faculty.department),
                      _ProfileRow(label: 'Campus', value: faculty.campus),
                      _ProfileRow(label: 'Highest degree', value: faculty.highestDegree),
                      _ProfileRow(label: 'Specialization', value: faculty.specialization),
                      _ProfileRow(
                        label: 'Years in service',
                        value: '${faculty.yearsInService} years',
                      ),
                      _ProfileRow(
                        label: 'Employment status',
                        value: faculty.employmentStatus,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const SectionHeader(title: 'Account information'),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    children: [
                      _ProfileRow(label: 'Email', value: faculty.email),
                      _ProfileRow(label: 'Mobile', value: faculty.phone),
                      const _ProfileRow(label: 'Role', value: 'Faculty member'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _SettingsTile(
                icon: Icons.edit_outlined,
                title: 'Edit profile',
                onTap: () => Navigator.pushNamed(context, AppRoutes.editProfile),
              ),
              _SettingsTile(
                icon: Icons.lock_outline_rounded,
                title: 'Change password',
                onTap: () => Navigator.pushNamed(context, AppRoutes.changePassword),
              ),
              _SettingsTile(
                icon: Icons.notifications_outlined,
                title: 'Notification settings',
                onTap: () =>
                    Navigator.pushNamed(context, AppRoutes.notificationSettings),
              ),
              _SettingsTile(
                icon: Icons.info_outline_rounded,
                title: 'About FacultyLink',
                onTap: () => Navigator.pushNamed(context, AppRoutes.about),
              ),
              const SizedBox(height: 12),
              SecondaryButton(
                label: 'Log out',
                icon: Icons.logout_rounded,
                onPressed: () async {
                  final confirmed = await showConfirmDialog(
                    context: context,
                    title: 'Log out?',
                    message: 'You will return to the FacultyLink sign-in screen.',
                    confirmLabel: 'Log out',
                    destructive: true,
                  );
                  if (!confirmed || !context.mounted) return;
                  await AppState.instance.resetSession();
                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    AppRoutes.login,
                    (_) => false,
                  );
                },
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(
              label,
              style: const TextStyle(
                color: AppColors.textTertiary,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  const _SettingsTile({
    required this.icon,
    required this.title,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        onTap: onTap,
        tileColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: AppColors.divider),
        ),
        leading: Icon(icon, color: AppColors.navy),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
        trailing: const Icon(Icons.chevron_right_rounded),
      ),
    );
  }
}

class EditProfileScreen extends StatefulWidget {
  const EditProfileScreen({super.key});

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  late final TextEditingController _name;
  late final TextEditingController _email;
  late final TextEditingController _phone;
  late final TextEditingController _department;
  final _formKey = GlobalKey<FormState>();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final faculty = AppState.instance.faculty;
    _name = TextEditingController(text: faculty.fullName);
    _email = TextEditingController(text: faculty.email);
    _phone = TextEditingController(text: faculty.phone);
    _department = TextEditingController(text: faculty.department);
  }

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _phone.dispose();
    _department.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await AppState.instance.saveFaculty(
        AppState.instance.faculty.copyWith(
          fullName: _name.text.trim(),
          email: _email.text.trim(),
          phone: _phone.text.trim(),
          department: _department.text.trim(),
        ),
      );
      if (!mounted) return;
      await showSuccessDialog(
        context: context,
        title: 'Profile updated',
        message: 'Your faculty profile has been saved.',
      );
      if (mounted) Navigator.pop(context);
    } catch (_) {
      if (!mounted) return;
      showAppSnackBar(context, 'Could not save the profile.', error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit profile')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AppTextField(
              label: 'Full name',
              controller: _name,
              validator: (value) =>
                  value == null || value.trim().isEmpty ? 'Enter your name' : null,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Email',
              controller: _email,
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Mobile',
              controller: _phone,
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Department',
              controller: _department,
            ),
            const SizedBox(height: 20),
            PrimaryButton(
              label: 'Save changes',
              loading: _saving,
              onPressed: _save,
            ),
          ],
        ),
      ),
    );
  }
}

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key, this.requiredFirstLogin = false});

  final bool requiredFirstLogin;

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  bool _obscure = true;
  bool _saving = false;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await AppState.instance.changePassword(
        currentPassword: _current.text,
        newPassword: _next.text,
      );
      if (!mounted) return;
      setState(() => _saving = false);
      if (widget.requiredFirstLogin) {
        Navigator.pushNamedAndRemoveUntil(context, AppRoutes.main, (_) => false);
        return;
      }
      await showSuccessDialog(
        context: context,
        title: 'Password updated',
        message: 'Your FacultyLink password has been updated.',
      );
      if (mounted) Navigator.pop(context);
    } on AppAuthException catch (error) {
      if (!mounted) return;
      setState(() => _saving = false);
      showAppSnackBar(context, error.message, error: true);
    } catch (_) {
      if (!mounted) return;
      setState(() => _saving = false);
      showAppSnackBar(context, 'The password was not updated.', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: !widget.requiredFirstLogin,
      child: Scaffold(
      appBar: AppBar(
        title: Text(widget.requiredFirstLogin ? 'Set new password' : 'Change password'),
        automaticallyImplyLeading: !widget.requiredFirstLogin,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AppTextField(
              label: 'Current password',
              controller: _current,
              obscureText: _obscure,
              suffix: IconButton(
                onPressed: () => setState(() => _obscure = !_obscure),
                icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
              ),
              validator: (value) =>
                  value == null || value.isEmpty ? 'Enter your current password' : null,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'New password',
              controller: _next,
              obscureText: _obscure,
              validator: (value) {
                if (value == null || value.length < 8) {
                  return 'Use at least 8 characters';
                }
                return null;
              },
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Confirm new password',
              controller: _confirm,
              obscureText: _obscure,
              validator: (value) {
                if (value != _next.text) return 'Passwords do not match';
                return null;
              },
            ),
            const SizedBox(height: 20),
            PrimaryButton(
              label: widget.requiredFirstLogin ? 'Continue to FacultyLink' : 'Update password',
              loading: _saving,
              onPressed: _save,
            ),
          ],
        ),
      ),
    ),
    );
  }
}

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() =>
      _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState extends State<NotificationSettingsScreen> {
  bool documentUpdates = true;
  bool reviewerFeedback = true;
  bool missingRequirements = true;
  bool simulationUpdates = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notification settings')),
      body: ListView(
        children: [
          SwitchListTile(
            title: const Text('Document status updates'),
            subtitle: const Text('Validated, pending, or returned documents'),
            value: documentUpdates,
            activeThumbColor: AppColors.navy,
            onChanged: (value) => setState(() => documentUpdates = value),
          ),
          SwitchListTile(
            title: const Text('Reviewer feedback'),
            subtitle: const Text('Comments that need your attention'),
            value: reviewerFeedback,
            activeThumbColor: AppColors.navy,
            onChanged: (value) => setState(() => reviewerFeedback = value),
          ),
          SwitchListTile(
            title: const Text('Missing requirement reminders'),
            subtitle: const Text('Gaps in your KRA documentary evidence'),
            value: missingRequirements,
            activeThumbColor: AppColors.navy,
            onChanged: (value) => setState(() => missingRequirements = value),
          ),
          SwitchListTile(
            title: const Text('Rank simulation updates'),
            subtitle: const Text('Changes to your self-assessment preview'),
            value: simulationUpdates,
            activeThumbColor: AppColors.navy,
            onChanged: (value) => setState(() => simulationUpdates = value),
          ),
        ],
      ),
    );
  }
}

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About FacultyLink')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          Center(
            child: AppLogo(size: 88, showWordmark: true),
          ),
          SizedBox(height: 20),
          Text(
            'Faculty Self-Assessment System  ·  Version 1.0.0 (UI prototype)',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary),
          ),
          SizedBox(height: 16),
          Text(
            'FacultyLink is an intelligent document-validated faculty self-assessment system designed to help faculty members prepare for DBM–CHED Joint Circular No. 01, s. 2026 rank upgrade and reclassification.',
            style: TextStyle(height: 1.45, fontSize: 15),
          ),
          SizedBox(height: 16),
          Text(
            'This mobile application is for faculty members. It helps you manage documentary evidence, monitor KRA scores and compliance, receive reviewer feedback, and simulate a potential rank upgrade before official evaluation.',
            style: TextStyle(height: 1.45, color: AppColors.textSecondary),
          ),
          SizedBox(height: 16),
          InfoBanner(
            message:
                'Scores, validation, and eligibility shown here are mock previews. They do not replace committee evaluation.',
          ),
        ],
      ),
    );
  }
}
