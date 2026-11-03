import 'package:flutter/material.dart';

import '../../data/app_state.dart';
import '../../data/criterion_c_catalog.dart';
import '../../data/criterion_c_mapper.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/tappable_card.dart';

enum _CPath { choose, researchType, role, mentorshipDetails }

/// Guided wizard for a new Criterion C accomplishment.
class CriterionCAddWorkScreen extends StatefulWidget {
  const CriterionCAddWorkScreen({super.key});

  @override
  State<CriterionCAddWorkScreen> createState() => _CriterionCAddWorkScreenState();
}

class _CriterionCAddWorkScreenState extends State<CriterionCAddWorkScreen> {
  CriterionCServiceKind? _kind;
  CriterionCResearchType? _researchType;
  CriterionCRole? _role;
  int _stepIndex = 0;

  final _titleCtrl = TextEditingController();
  final _dateCtrl = TextEditingController();
  final _competitionCtrl = TextEditingController();
  final _prizeLevelCtrl = TextEditingController();
  final _prizePlacementCtrl = TextEditingController();

  List<_CPath> get _steps {
    if (_kind == CriterionCServiceKind.mentorship) {
      return [_CPath.choose, _CPath.mentorshipDetails];
    }
    if (_kind == CriterionCServiceKind.research) {
      return [_CPath.choose, _CPath.researchType, _CPath.role];
    }
    return [_CPath.choose];
  }

  @override
  void initState() {
    super.initState();
    if (!AppState.instance.usesMockAuth && AppState.instance.isSignedIn) {
      AppState.instance.refreshScoringConfiguration(quiet: true);
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _dateCtrl.dispose();
    _competitionCtrl.dispose();
    _prizeLevelCtrl.dispose();
    _prizePlacementCtrl.dispose();
    super.dispose();
  }

  bool _canAdvance() {
    final step = _steps[_stepIndex];
    switch (step) {
      case _CPath.choose:
        return _kind != null;
      case _CPath.researchType:
        return _researchType != null;
      case _CPath.role:
        return _role != null;
      case _CPath.mentorshipDetails:
        return _titleCtrl.text.trim().isNotEmpty && _competitionCtrl.text.trim().isNotEmpty;
    }
  }

  bool get _onLastStep => _stepIndex >= _steps.length - 1;

  String _primaryButtonLabel(_CPath step) {
    if (step == _CPath.role) return 'Upload approval sheet';
    if (step == _CPath.mentorshipDetails) return 'Upload documents';
    return 'Next';
  }

  void _back() {
    if (_stepIndex == 0) {
      Navigator.maybePop(context);
      return;
    }
    setState(() => _stepIndex -= 1);
  }

  Future<bool> _confirmLeave() async {
    if (_kind == null && _titleCtrl.text.isEmpty) return true;
    final leave = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Discard changes?'),
        content: const Text('You have unsaved wizard answers.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Stay')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Leave')),
        ],
      ),
    );
    return leave ?? false;
  }

  void _next() {
    if (_onLastStep) {
      _goUpload();
      return;
    }
    setState(() => _stepIndex += 1);
  }

  CriterionCAddWorkDraft _buildDraft() {
    final kind = _kind!;
    final indicator = CriterionCMapper.indicatorId(
      kind: kind,
      researchType: _researchType,
      role: _role,
    );
    if (kind == CriterionCServiceKind.mentorship) {
      return CriterionCAddWorkDraft(
        serviceKind: 'mentorship',
        indicatorId: indicator,
        projectTitle: _titleCtrl.text.trim(),
        completionDate: _dateCtrl.text.trim().isEmpty ? null : _dateCtrl.text.trim(),
        competitionName: _competitionCtrl.text.trim(),
        prizeLevel: _prizeLevelCtrl.text.trim().isEmpty ? null : _prizeLevelCtrl.text.trim(),
        prizePlacement: _prizePlacementCtrl.text.trim().isEmpty ? null : _prizePlacementCtrl.text.trim(),
      );
    }
    return CriterionCAddWorkDraft(
      serviceKind: 'research',
      indicatorId: indicator,
      ocrFirstResearch: true,
    );
  }

  void _goUpload() {
    if (!AppState.instance.usesMockAuth && !CriterionCCatalog.criterionCScoringReady) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Official scoring configuration is incomplete. Cannot start this accomplishment until configuration is published.',
          ),
        ),
      );
      return;
    }
    final preview = CriterionCMapper.previewPoints(
      kind: _kind ?? CriterionCServiceKind.research,
      researchType: _researchType,
      role: _role,
    );
    if (!AppState.instance.usesMockAuth && preview == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Point value for the selected indicator is unavailable in the published configuration.',
          ),
        ),
      );
      return;
    }
    final draft = _buildDraft();
    Navigator.pushNamed(
      context,
      AppRoutes.uploadDocument,
      arguments: UploadDocumentLaunch(
        kra: KraType.instruction,
        criterionId: CriterionCCatalog.criterionId,
        indicatorId: draft.indicatorId,
        criterionCPrimaryFlow: true,
        criterionCOcrFirstResearch: draft.ocrFirstResearch,
        criterionCDraft: draft,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final steps = _steps;
    final step = steps[_stepIndex.clamp(0, steps.length - 1)];
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (await _confirmLeave()) {
          if (context.mounted) Navigator.pop(context);
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          title: const Text('Add accomplishment'),
          backgroundColor: AppColors.navy,
          foregroundColor: Colors.white,
        ),
        body: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: LinearProgressIndicator(
                value: (_stepIndex + 1) / steps.length,
                minHeight: 8,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: _bodyForStep(step),
              ),
            ),
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    TextButton(onPressed: _back, child: const Text('Back')),
                    const SizedBox(width: 8),
                    Expanded(
                      child: PrimaryButton(
                        label: _primaryButtonLabel(step),
                        onPressed: _canAdvance() ? _next : null,
                        expand: true,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bodyForStep(_CPath step) {
    switch (step) {
      case _CPath.choose:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _heading('What type of service?', 'Choose the category that matches Annex A.'),
            _choice(
              selected: _kind == CriterionCServiceKind.research,
              title: 'Research advising / panel',
              onTap: () => setState(() => _kind = CriterionCServiceKind.research),
            ),
            const SizedBox(height: 10),
            _choice(
              selected: _kind == CriterionCServiceKind.mentorship,
              title: 'Mentorship services',
              onTap: () => setState(() => _kind = CriterionCServiceKind.mentorship),
            ),
          ],
        );
      case _CPath.researchType:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _heading('Research type', null),
            for (final t in CriterionCCatalog.researchTypes)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _choice(
                  selected: _researchType?.id == t.id,
                  title: t.label,
                  onTap: () => setState(() => _researchType = t),
                ),
              ),
          ],
        );
      case _CPath.role:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _heading(
              'Your role',
              'Next, upload the signed approval sheet. OCR runs in the background; your reviewer verifies extracted details.',
            ),
            _choice(
              selected: _role == CriterionCRole.adviser,
              title: 'Adviser',
              onTap: () => setState(() => _role = CriterionCRole.adviser),
            ),
            const SizedBox(height: 10),
            _choice(
              selected: _role == CriterionCRole.panel,
              title: 'Panel member',
              onTap: () => setState(() => _role = CriterionCRole.panel),
            ),
            const SizedBox(height: 16),
            const Text(
              'OCR text reading is advisory only and does not prove eligibility.',
              style: TextStyle(height: 1.45, color: AppColors.textSecondary),
            ),
          ],
        );
      case _CPath.mentorshipDetails:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _heading('Mentorship details', 'Upload your evidence after entering these details.'),
            TextField(
              controller: _titleCtrl,
              decoration: const InputDecoration(labelText: 'Activity title *'),
              onChanged: (_) => setState(() {}),
            ),
            TextField(
              controller: _competitionCtrl,
              decoration: const InputDecoration(labelText: 'Competition or award name *'),
              onChanged: (_) => setState(() {}),
            ),
            TextField(
              controller: _prizeLevelCtrl,
              decoration: const InputDecoration(labelText: 'Prize level (optional)'),
            ),
            TextField(
              controller: _prizePlacementCtrl,
              decoration: const InputDecoration(labelText: 'Placement (optional)'),
            ),
            TextField(
              controller: _dateCtrl,
              decoration: const InputDecoration(labelText: 'Award date (optional)', hintText: 'YYYY-MM-DD'),
            ),
          ],
        );
    }
  }

  Widget _heading(String title, String? subtitle) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy)),
        if (subtitle != null) ...[
          const SizedBox(height: 8),
          Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, height: 1.45)),
        ],
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _choice({required bool selected, required String title, required VoidCallback onTap}) {
    return TappableCard(
      selected: selected,
      onTap: onTap,
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
          if (selected) const Icon(Icons.check_circle, color: AppColors.forestLight),
        ],
      ),
    );
  }
}
