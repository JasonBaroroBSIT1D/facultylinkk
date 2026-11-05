import 'package:flutter/material.dart';

import '../../data/kra4_catalog.dart';
import '../../theme/app_colors.dart';
import 'kra4_criterion_hub_screen.dart';
import 'kra4_hub_widgets.dart';

/// KRA IV entry — Criteria A–D.
class Kra4MainHubScreen extends StatelessWidget {
  const Kra4MainHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('KRA IV — Professional Development'),
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 32),
        children: [
          const Text(
            'What have you accomplished?',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
              height: 1.25,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Choose what you want to add. We\'ll guide you step by step.',
            style: TextStyle(
              fontSize: 15,
              height: 1.4,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 20),
          const Kra4StepGuide(),
          const SizedBox(height: 24),
          Kra4MainCriterionCard(
            icon: Kra4Catalog.criterionIcon(Kra4Catalog.criterionA),
            iconBackground: Kra4Catalog.criterionIconBackground(Kra4Catalog.criterionA),
            title: Kra4Catalog.mainHubCardTitle(Kra4Catalog.criterionA),
            description: Kra4Catalog.mainHubCardDescription(Kra4Catalog.criterionA),
            criterionLabel: Kra4Catalog.criterionBadge(Kra4Catalog.criterionA),
            onTap: () => _open(context, Kra4Catalog.criterionA),
          ),
          Kra4MainCriterionCard(
            icon: Kra4Catalog.criterionIcon(Kra4Catalog.criterionB),
            iconBackground: Kra4Catalog.criterionIconBackground(Kra4Catalog.criterionB),
            title: Kra4Catalog.mainHubCardTitle(Kra4Catalog.criterionB),
            description: Kra4Catalog.mainHubCardDescription(Kra4Catalog.criterionB),
            criterionLabel: Kra4Catalog.criterionBadge(Kra4Catalog.criterionB),
            onTap: () => _open(context, Kra4Catalog.criterionB),
          ),
          Kra4MainCriterionCard(
            icon: Kra4Catalog.criterionIcon(Kra4Catalog.criterionC),
            iconBackground: Kra4Catalog.criterionIconBackground(Kra4Catalog.criterionC),
            title: Kra4Catalog.mainHubCardTitle(Kra4Catalog.criterionC),
            description: Kra4Catalog.mainHubCardDescription(Kra4Catalog.criterionC),
            criterionLabel: Kra4Catalog.criterionBadge(Kra4Catalog.criterionC),
            onTap: () => _open(context, Kra4Catalog.criterionC),
          ),
          Kra4MainCriterionCard(
            icon: Kra4Catalog.criterionIcon(Kra4Catalog.criterionD),
            iconBackground: Kra4Catalog.criterionIconBackground(Kra4Catalog.criterionD),
            title: Kra4Catalog.mainHubCardTitle(Kra4Catalog.criterionD),
            description: Kra4Catalog.mainHubCardDescription(Kra4Catalog.criterionD),
            criterionLabel: Kra4Catalog.criterionBadge(Kra4Catalog.criterionD),
            onTap: () => _open(context, Kra4Catalog.criterionD),
          ),
        ],
      ),
    );
  }

  void _open(BuildContext context, String criterionId) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => Kra4CriterionHubScreen(criterionId: criterionId)),
    );
  }
}
