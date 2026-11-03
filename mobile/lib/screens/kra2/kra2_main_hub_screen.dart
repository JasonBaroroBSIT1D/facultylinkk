import 'package:flutter/material.dart';

import '../../data/kra2_catalog.dart';
import '../../theme/app_colors.dart';
import 'kra2_criterion_hub_screen.dart';
import 'kra2_hub_widgets.dart';

/// KRA II entry — Criteria A, B, and C.
class Kra2MainHubScreen extends StatelessWidget {
  const Kra2MainHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Research'),
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
          const Kra2StepGuide(),
          const SizedBox(height: 24),
          Kra2MainCriterionCard(
            icon: Kra2Catalog.criterionIcon(Kra2Catalog.criterionA),
            iconBackground: Kra2Catalog.criterionIconBackground(Kra2Catalog.criterionA),
            title: Kra2Catalog.mainHubCardTitle(Kra2Catalog.criterionA),
            description: Kra2Catalog.mainHubCardDescription(Kra2Catalog.criterionA),
            criterionLabel: Kra2Catalog.criterionBadge(Kra2Catalog.criterionA),
            onTap: () => _open(context, Kra2Catalog.criterionA),
          ),
          Kra2MainCriterionCard(
            icon: Kra2Catalog.criterionIcon(Kra2Catalog.criterionB),
            iconBackground: Kra2Catalog.criterionIconBackground(Kra2Catalog.criterionB),
            title: Kra2Catalog.mainHubCardTitle(Kra2Catalog.criterionB),
            description: Kra2Catalog.mainHubCardDescription(Kra2Catalog.criterionB),
            criterionLabel: Kra2Catalog.criterionBadge(Kra2Catalog.criterionB),
            onTap: () => _open(context, Kra2Catalog.criterionB),
          ),
          Kra2MainCriterionCard(
            icon: Kra2Catalog.criterionIcon(Kra2Catalog.criterionC),
            iconBackground: Kra2Catalog.criterionIconBackground(Kra2Catalog.criterionC),
            title: Kra2Catalog.mainHubCardTitle(Kra2Catalog.criterionC),
            description: Kra2Catalog.mainHubCardDescription(Kra2Catalog.criterionC),
            criterionLabel: Kra2Catalog.criterionBadge(Kra2Catalog.criterionC),
            onTap: () => _open(context, Kra2Catalog.criterionC),
          ),
        ],
      ),
    );
  }

  void _open(BuildContext context, String criterionId) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => Kra2CriterionHubScreen(criterionId: criterionId)),
    );
  }
}
