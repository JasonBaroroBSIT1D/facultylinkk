import 'package:flutter/material.dart';

import '../../data/criterion_b_mapper.dart';
import '../../data/criterion_b_teaching_wizard_flow.dart';
import '../../data/criterion_b_ux.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';
import '../../widgets/tappable_card.dart';

/// One question at a time — maps to existing backend indicators.
class CriterionBAddWorkScreen extends StatefulWidget {
  const CriterionBAddWorkScreen({super.key, required this.kind});

  final CriterionBWorkKind kind;

  @override
  State<CriterionBAddWorkScreen> createState() => _CriterionBAddWorkScreenState();
}

class _CriterionBAddWorkScreenState extends State<CriterionBAddWorkScreen> {
  int _index = 0;

  String? _materialKind;
  final _titleCtrl = TextEditingController();
  bool? _withOthers;
  final _percentCtrl = TextEditingController();
  /// Null until the faculty toggles the complete-set switch (never silently false).
  bool? _completeSetDeclared;

  final _programNameCtrl = TextEditingController();
  String? _programKind;
  bool? _isLead;
  final _contributionCtrl = TextEditingController();
  final _committeeCtrl = TextEditingController();

  List<CriterionBTeachingWizardStep> get _teachingSteps =>
      CriterionBTeachingWizardFlow.steps(
        materialKind: _materialKind,
        withOthers: _withOthers,
      );

  int get _pageCount =>
      widget.kind == CriterionBWorkKind.teaching ? _teachingSteps.length : 5;

  CriterionBTeachingWizardStep? get _currentTeachingStep {
    if (widget.kind != CriterionBWorkKind.teaching) return null;
    final steps = _teachingSteps;
    if (_index < 0 || _index >= steps.length) return null;
    return steps[_index];
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _percentCtrl.dispose();
    _programNameCtrl.dispose();
    _contributionCtrl.dispose();
    _committeeCtrl.dispose();
    super.dispose();
  }

  void _clampIndex() {
    final max = _pageCount - 1;
    if (_index > max) {
      setState(() => _index = max);
    }
  }

  void _next() {
    if (!_canAdvance()) return;
    if (_index >= _pageCount - 1) {
      _goUpload();
      return;
    }
    setState(() => _index += 1);
  }

  void _back() {
    if (_index == 0) {
      Navigator.pop(context);
      return;
    }
    setState(() => _index -= 1);
  }

  bool _canAdvance() {
    if (widget.kind == CriterionBWorkKind.teaching) {
      switch (_currentTeachingStep) {
        case CriterionBTeachingWizardStep.material:
          return _materialKind != null;
        case CriterionBTeachingWizardStep.title:
          return _titleCtrl.text.trim().isNotEmpty;
        case CriterionBTeachingWizardStep.authorship:
          return _withOthers != null;
        case CriterionBTeachingWizardStep.contribution:
          final p = int.tryParse(_percentCtrl.text.trim());
          return p != null && p >= 0 && p <= 100;
        case CriterionBTeachingWizardStep.completeSet:
          return _completeSetDeclared == true;
        case CriterionBTeachingWizardStep.almostDone:
        case CriterionBTeachingWizardStep.readyToUpload:
          return true;
        case null:
          return false;
      }
    }
    switch (_index) {
      case 0:
        return _programNameCtrl.text.trim().isNotEmpty;
      case 1:
        return _programKind != null;
      case 2:
        return _isLead != null;
      case 3:
        return _contributionCtrl.text.trim().length >= 8;
      default:
        return true;
    }
  }

  CriterionBAddWorkDraft _buildDraft() {
    if (widget.kind == CriterionBWorkKind.teaching) {
      final withOthers = _withOthers ?? false;
      final indicator = CriterionBMapper.teachingIndicatorId(
        materialKind: _materialKind!,
        withOthers: withOthers,
      );
      bool? completeForApi;
      if (_materialKind != null &&
          CriterionBMapper.showCompleteSetQuestion(_materialKind!) &&
          _completeSetDeclared != null) {
        completeForApi = _completeSetDeclared;
      }
      return CriterionBAddWorkDraft(
        accomplishmentKind: CriterionBUx.accomplishmentInstructional,
        indicatorId: indicator,
        materialTitle: _titleCtrl.text.trim(),
        materialType: CriterionBMapper.materialTypeForKind(_materialKind!),
        contributionPercent: withOthers ? int.tryParse(_percentCtrl.text.trim()) : null,
        completeSetDeclared: completeForApi,
      );
    }
    final lead = _isLead ?? true;
    return CriterionBAddWorkDraft(
      accomplishmentKind: 'program',
      indicatorId: CriterionBMapper.programIndicatorId(isLead: lead),
      programName: _programNameCtrl.text.trim(),
      programDevelopmentKind: _programKind,
      contributionDescription: _contributionCtrl.text.trim(),
      committeeName: _committeeCtrl.text.trim().isEmpty ? null : _committeeCtrl.text.trim(),
    );
  }

  void _goUpload() {
    final draft = _buildDraft();
    TappableCard.scheduleTap(context, () {
      Navigator.pushNamed(
        context,
        AppRoutes.uploadDocument,
        arguments: UploadDocumentLaunch(
          kra: KraType.instruction,
          criterionId: 'kra1-b',
          indicatorId: draft.indicatorId,
          criterionBPrimaryFlow: true,
          criterionBDraft: draft,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    _clampIndex();
    final progressDenominator = _pageCount > 0 ? _pageCount : 1;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Add work'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            child: LinearProgressIndicator(
              value: (_index + 1) / progressDenominator,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
              backgroundColor: AppColors.divider,
              color: AppColors.forestLight,
            ),
          ),
          Expanded(
            child: _stepScroll(
              widget.kind == CriterionBWorkKind.teaching
                  ? _teachingPage(_currentTeachingStep)
                  : _programPage(_index),
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  TextButton(onPressed: _back, child: const Text('Back')),
                  const Spacer(),
                  PrimaryButton(
                    label: _index >= _pageCount - 1 ? 'Upload files' : 'Next',
                    onPressed: _canAdvance() ? _next : null,
                    expand: false,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _teachingPage(CriterionBTeachingWizardStep? step) {
    switch (step) {
      case CriterionBTeachingWizardStep.material:
        return _question(
          'What type of material?',
          'Choose the closest match.',
          _choiceGrid([
            _Choice('book', 'Book or textbook', Icons.menu_book_outlined),
            _Choice('module', 'Module', Icons.view_module_outlined),
            _Choice('manual', 'Instructional manual', Icons.build_outlined),
            _Choice('multimedia', 'Multimedia', Icons.play_circle_outline),
          ], _materialKind, (v) => setState(() {
                _materialKind = v;
                _clampIndex();
              })),
        );
      case CriterionBTeachingWizardStep.title:
        return _question(
          'What is its title?',
          'Use the official title faculty and reviewers will recognize.',
          TextField(
            controller: _titleCtrl,
            decoration: const InputDecoration(
              labelText: 'Title',
              hintText: 'e.g. Introduction to Programming Module',
            ),
            onChanged: (_) => setState(() {}),
          ),
        );
      case CriterionBTeachingWizardStep.authorship:
        return _question(
          'Did you create it alone or with others?',
          null,
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _bigChoice(
                selected: _withOthers == false,
                title: 'I created it alone',
                onTap: () => setState(() {
                  _withOthers = false;
                  _clampIndex();
                }),
              ),
              const SizedBox(height: 10),
              _bigChoice(
                selected: _withOthers == true,
                title: 'I worked with others',
                onTap: () => setState(() {
                  _withOthers = true;
                  _clampIndex();
                }),
              ),
            ],
          ),
        );
      case CriterionBTeachingWizardStep.contribution:
        return _question(
          'What was your contribution?',
          'Enter your share as a whole number from 0 to 100.',
          TextField(
            controller: _percentCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Your contribution (%)'),
            onChanged: (_) => setState(() {}),
          ),
        );
      case CriterionBTeachingWizardStep.completeSet:
        return _completeSetQuestion();
      case CriterionBTeachingWizardStep.almostDone:
        return _question(
          'Almost done',
          'Next you will upload your main file.',
          const SizedBox.shrink(),
        );
      case CriterionBTeachingWizardStep.readyToUpload:
        return _question(
          'Ready to upload',
          'Next you will upload your main file, then any other documents we ask for.',
          const Text(
            'You can return later if you need more time.',
            style: TextStyle(height: 1.45),
          ),
        );
      case null:
        return const SizedBox.shrink();
    }
  }

  Widget _completeSetQuestion() {
    return _question(
      'Complete Instructional Material',
      'I confirm that my module or instructional manual is a complete stand-alone material or complete set, as applicable.',
      SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: const Text('Yes, I confirm'),
        value: _completeSetDeclared ?? false,
        onChanged: (v) => setState(() => _completeSetDeclared = v),
      ),
    );
  }

  Widget _programPage(int index) {
    switch (index) {
      case 0:
        return _question(
          'What is the program name?',
          null,
          TextField(
            controller: _programNameCtrl,
            decoration: const InputDecoration(labelText: 'Program name'),
            onChanged: (_) => setState(() {}),
          ),
        );
      case 1:
        return _question(
          'Is this a new program or a major revision?',
          null,
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _bigChoice(
                selected: _programKind == 'new_program',
                title: 'New program',
                onTap: () => setState(() => _programKind = 'new_program'),
              ),
              const SizedBox(height: 10),
              _bigChoice(
                selected: _programKind == 'substantial_revision',
                title: 'Substantial revision',
                onTap: () => setState(() => _programKind = 'substantial_revision'),
              ),
            ],
          ),
        );
      case 2:
        return _question(
          'What was your role?',
          null,
          Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _bigChoice(
                selected: _isLead == true,
                title: 'I was the lead',
                onTap: () => setState(() => _isLead = true),
              ),
              const SizedBox(height: 10),
              _bigChoice(
                selected: _isLead == false,
                title: 'I was a contributor',
                onTap: () => setState(() => _isLead = false),
              ),
            ],
          ),
        );
      case 3:
        return _question(
          'Describe your contribution',
          'A few sentences about what you actually did.',
          TextField(
            controller: _contributionCtrl,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Your contribution'),
            onChanged: (_) => setState(() {}),
          ),
        );
      default:
        return _question(
          'Anything else? (optional)',
          'Committee name helps reviewers if your program work overlaps other criteria.',
          TextField(
            controller: _committeeCtrl,
            decoration: const InputDecoration(labelText: 'Committee name (optional)'),
          ),
        );
    }
  }

  Widget _stepScroll(Widget step) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: step,
    );
  }

  Widget _question(String title, String? subtitle, Widget body) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 22, color: AppColors.navy)),
        if (subtitle != null) ...[
          const SizedBox(height: 8),
          Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, height: 1.45, fontSize: 15)),
        ],
        const SizedBox(height: 24),
        body,
      ],
    );
  }

  Widget _choiceGrid(List<_Choice> choices, String? selected, ValueChanged<String> onPick) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: choices
          .map(
            (c) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _bigChoice(
                selected: selected == c.id,
                title: c.title,
                icon: c.icon,
                onTap: () => onPick(c.id),
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _bigChoice({
    required bool selected,
    required String title,
    required VoidCallback onTap,
    IconData? icon,
  }) {
    return TappableCard(
      selected: selected,
      borderRadius: BorderRadius.circular(14),
      deferTap: false,
      onTap: onTap,
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          if (icon != null) ...[Icon(icon, color: AppColors.navy), const SizedBox(width: 12)],
          Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16))),
          if (selected) const Icon(Icons.check_circle, color: AppColors.forestLight),
        ],
      ),
    );
  }
}

class _Choice {
  const _Choice(this.id, this.title, this.icon);

  final String id;
  final String title;
  final IconData icon;
}
