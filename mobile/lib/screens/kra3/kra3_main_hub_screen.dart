import 'package:flutter/material.dart';

import '../../data/kra3_catalog.dart';
import '../../theme/app_colors.dart';
import 'kra3_criterion_hub_screen.dart';
import 'kra3_hub_widgets.dart';

/// KRA III entry — Criteria A–D.
class Kra3MainHubScreen extends StatelessWidget {
  const Kra3MainHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('KRA III — Extension Services'),
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
          const Kra3StepGuide(),
          const SizedBox(height: 24),
          Kra3MainCriterionCard(
            icon: Kra3Catalog.criterionIcon(Kra3Catalog.criterionA),
            iconBackground: Kra3Catalog.criterionIconBackground(Kra3Catalog.criterionA),
            title: Kra3Catalog.mainHubCardTitle(Kra3Catalog.criterionA),
            description: Kra3Catalog.mainHubCardDescription(Kra3Catalog.criterionA),
            criterionLabel: Kra3Catalog.criterionBadge(Kra3Catalog.criterionA),
            onTap: () => _open(context, Kra3Catalog.criterionA),
          ),
          Kra3MainCriterionCard(
            icon: Kra3Catalog.criterionIcon(Kra3Catalog.criterionB),
            iconBackground: Kra3Catalog.criterionIconBackground(Kra3Catalog.criterionB),
            title: Kra3Catalog.mainHubCardTitle(Kra3Catalog.criterionB),
            description: Kra3Catalog.mainHubCardDescription(Kra3Catalog.criterionB),
            criterionLabel: Kra3Catalog.criterionBadge(Kra3Catalog.criterionB),
            onTap: () => _open(context, Kra3Catalog.criterionB),
          ),
          Kra3MainCriterionCard(
            icon: Kra3Catalog.criterionIcon(Kra3Catalog.criterionC),
            iconBackground: Kra3Catalog.criterionIconBackground(Kra3Catalog.criterionC),
            title: Kra3Catalog.mainHubCardTitle(Kra3Catalog.criterionC),
            description: Kra3Catalog.mainHubCardDescription(Kra3Catalog.criterionC),
            criterionLabel: Kra3Catalog.criterionBadge(Kra3Catalog.criterionC),
            onTap: () => _open(context, Kra3Catalog.criterionC),
          ),
          Kra3MainCriterionCard(
            icon: Kra3Catalog.criterionIcon(Kra3Catalog.criterionD),
            iconBackground: Kra3Catalog.criterionIconBackground(Kra3Catalog.criterionD),
            title: Kra3Catalog.mainHubCardTitle(Kra3Catalog.criterionD),
            description: Kra3Catalog.mainHubCardDescription(Kra3Catalog.criterionD),
            criterionLabel: Kra3Catalog.criterionBadge(Kra3Catalog.criterionD),
            onTap: () => _open(context, Kra3Catalog.criterionD),
          ),
        ],
      ),
    );
  }

  void _open(BuildContext context, String criterionId) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => Kra3CriterionHubScreen(criterionId: criterionId)),
    );
  }
}
