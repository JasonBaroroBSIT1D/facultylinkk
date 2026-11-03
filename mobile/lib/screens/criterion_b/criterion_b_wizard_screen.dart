import 'package:flutter/material.dart';

import '../../data/criterion_b_catalog.dart';
import '../../data/criterion_b_ux.dart';
import '../../models/enums.dart';
import '../../navigation/app_routes.dart';
import '../../screens/documents/document_flow_args.dart';
import '../../theme/app_colors.dart';
import '../../widgets/app_buttons.dart';

/// Step-by-step entry for new Criterion B primary claims.
class CriterionBWizardScreen extends StatefulWidget {
  const CriterionBWizardScreen({super.key});

  @override
  State<CriterionBWizardScreen> createState() => _CriterionBWizardScreenState();
}

class _CriterionBWizardScreenState extends State<CriterionBWizardScreen> {
  int _step = 0;
  String? _accomplishmentKind; // instructional_material | academic_program
  String? _indicatorId;

  static const _imChoices = <_Choice>[
    _Choice('kra1-b-textbook-sole', 'Textbook', 'Sole author', Icons.menu_book_outlined),
    _Choice('kra1-b-textbook-co', 'Textbook', 'Co-author', Icons.people_outline),
    _Choice('kra1-b-module-sole', 'Module', 'Sole author', Icons.view_module_outlined),
    _Choice('kra1-b-module-co', 'Module', 'Co-author', Icons.people_outline),
    _Choice('kra1-b-manual-sole', 'Instructional manual', 'Sole author', Icons.build_outlined),
    _Choice('kra1-b-manual-co', 'Instructional manual', 'Co-author', Icons.people_outline),
    _Choice('kra1-b-multimedia-sole', 'Multimedia material', 'Sole author', Icons.play_circle_outline),
    _Choice('kra1-b-multimedia-co', 'Multimedia material', 'Co-author', Icons.people_outline),
  ];

  static const _programChoices = <_Choice>[
    _Choice(
      'kra1-b-program-lead',
      'Program lead',
      'You led development or revision',
      Icons.school_outlined,
    ),
    _Choice(
      'kra1-b-program-contributor',
      'Program contributor',
      'You contributed to an approved program change',
      Icons.group_outlined,
    ),
  ];

  void _next() {
    if (_step < 2) setState(() => _step += 1);
  }

  void _back() {
    if (_step > 0) setState(() => _step -= 1);
  }

  Future<void> _openUpload() async {
    if (_indicatorId == null) return;
    await Navigator.pushNamed(
      context,
      AppRoutes.uploadDocument,
      arguments: UploadDocumentLaunch(
        kra: KraType.instruction,
        criterionId: CriterionBCatalog.criterionId,
        indicatorId: _indicatorId,
      ),
    );
    if (!mounted) return;
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('New accomplishment'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          _WizardProgress(current: _step, total: 3),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(20),
              children: [
                Text(
                  _stepTitle(),
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: AppColors.navy),
                ),
                const SizedBox(height: 8),
                Text(
                  _stepSubtitle(),
                  style: const TextStyle(color: AppColors.textSecondary, height: 1.45),
                ),
                const SizedBox(height: 24),
                if (_step == 0) ..._buildStepChooseType(),
                if (_step == 1) ..._buildStepChooseCategory(),
                if (_step == 2) ..._buildStepUpload(),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              child: Row(
                children: [
                  if (_step > 0)
                    TextButton(onPressed: _back, child: const Text('Back')),
                  const Spacer(),
                  if (_step < 2)
                    PrimaryButton(
                      label: 'Continue',
                      onPressed: _canContinue() ? _next : null,
                    )
                  else
                    PrimaryButton(
                      label: 'Upload main document',
                      onPressed: _indicatorId != null ? _openUpload : null,
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _stepTitle() {
    switch (_step) {
      case 0:
        return 'Step 1 — Choose accomplishment type';
      case 1:
        return _accomplishmentKind == CriterionBUx.accomplishmentProgram
            ? 'Step 2 — Your program role'
            : 'Step 2 — Material type and authorship';
      default:
        return 'Step 3 — Upload your main document';
    }
  }

  String _stepSubtitle() {
    switch (_step) {
      case 0:
        return 'Criterion B covers instructional materials and academic program development. '
            'Pick the type that matches your work.';
      case 1:
        return 'This selects the correct checklist and point category. You can add details after upload.';
      default:
        return 'Upload the primary file for this accomplishment. You will attach supporting documents '
            'in the next screen with a simple checklist.';
    }
  }

  bool _canContinue() {
    if (_step == 0) return _accomplishmentKind != null;
    if (_step == 1) return _indicatorId != null;
    return false;
  }

  List<Widget> _buildStepChooseType() {
    return [
      _TypeCard(
        title: 'Instructional material',
        subtitle: 'Textbook, module, manual, or multimedia teaching material',
        icon: Icons.menu_book_outlined,
        selected: _accomplishmentKind == CriterionBUx.accomplishmentInstructional,
        onTap: () => setState(() {
          _accomplishmentKind = CriterionBUx.accomplishmentInstructional;
          _indicatorId = null;
        }),
      ),
      const SizedBox(height: 12),
      _TypeCard(
        title: 'Academic program',
        subtitle: 'New program or substantial revision you led or contributed to',
        icon: Icons.school_outlined,
        selected: _accomplishmentKind == CriterionBUx.accomplishmentProgram,
        onTap: () => setState(() {
          _accomplishmentKind = CriterionBUx.accomplishmentProgram;
          _indicatorId = null;
        }),
      ),
    ];
  }

  List<Widget> _buildStepChooseCategory() {
    final choices = _accomplishmentKind == CriterionBUx.accomplishmentProgram
        ? _programChoices
        : _imChoices;
    return [
      for (final c in choices)
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _TypeCard(
            title: c.title,
            subtitle: c.subtitle,
            icon: c.icon,
            selected: _indicatorId == c.indicatorId,
            onTap: () => setState(() => _indicatorId = c.indicatorId),
          ),
        ),
    ];
  }

  List<Widget> _buildStepUpload() {
    return [
      Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.divider),
        ),
        child: const Text(
          'After upload, open your submission to complete the evidence checklist. '
          'Each item explains what to attach. Files are sent to your assigned reviewer automatically—'
          'there is no separate “submit” button unless your institution adds one later.',
          style: TextStyle(height: 1.45, fontSize: 14),
        ),
      ),
    ];
  }
}

class _WizardProgress extends StatelessWidget {
  const _WizardProgress({required this.current, required this.total});

  final int current;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        children: List.generate(total, (i) {
          final active = i <= current;
          return Expanded(
            child: Container(
              margin: EdgeInsets.only(right: i < total - 1 ? 6 : 0),
              height: 6,
              decoration: BoxDecoration(
                color: active ? AppColors.forestLight : AppColors.divider,
                borderRadius: BorderRadius.circular(3),
              ),
            ),
          );
        }),
      ),
    );
  }
}

class _TypeCard extends StatelessWidget {
  const _TypeCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? AppColors.mint.withOpacity(0.35) : Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: selected ? AppColors.forestLight : AppColors.divider,
              width: selected ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              Icon(icon, size: 32, color: AppColors.navy),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    const SizedBox(height: 4),
                    Text(subtitle, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.35)),
                  ],
                ),
              ),
              if (selected) const Icon(Icons.check_circle, color: AppColors.forestLight),
            ],
          ),
        ),
      ),
    );
  }
}

class _Choice {
  const _Choice(this.indicatorId, this.title, this.subtitle, this.icon);

  final String indicatorId;
  final String title;
  final String subtitle;
  final IconData icon;
}
