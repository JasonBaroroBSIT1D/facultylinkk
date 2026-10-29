import 'package:flutter/material.dart';

import '../models/enums.dart';

/// Academic navy, sky-blue, and CHED brick-red palette used across FacultyLink.
abstract final class AppColors {
  static const Color navy = Color(0xFF102A43);
  static const Color navyDark = Color(0xFF0A1628);
  static const Color navyMid = Color(0xFF2563EB);
  static const Color gold = Color(0xFFC4A35A);
  static const Color goldSoft = Color(0xFFF4E8C8);
  static const Color forest = Color(0xFF14382B);
  static const Color forestMid = Color(0xFF1F5C43);
  static const Color forestLight = Color(0xFF2D7A58);
  static const Color mint = Color(0xFFC9EBD6);
  static const Color brick = Color(0xFFA04040);
  static const Color sky = Color(0xFFD1E9F6);
  static const Color skyDeep = Color(0xFFB9DFF0);
  static const Color fieldFill = Color(0xFFF3F6F9);

  static const Color background = Color(0xFFF5F7FA);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceMuted = Color(0xFFEEF2F6);

  static const Color textPrimary = Color(0xFF172B4D);
  static const Color textSecondary = Color(0xFF64748B);
  static const Color textTertiary = Color(0xFF667085);
  static const Color border = Color(0xFFD0D5DD);
  static const Color divider = Color(0xFFE4E7EC);

  static const Color success = Color(0xFF067647);
  static const Color successSoft = Color(0xFFECFDF3);
  static const Color warning = Color(0xFFB54708);
  static const Color warningSoft = Color(0xFFFFFAEB);
  static const Color error = Color(0xFFB42318);
  static const Color errorSoft = Color(0xFFFEF3F2);
  static const Color info = Color(0xFF175CD3);
  static const Color infoSoft = Color(0xFFEFF8FF);
  static const Color processing = Color(0xFF6941C6);
  static const Color processingSoft = Color(0xFFF4EBFF);

  static const Color instruction = Color(0xFF2563EB);
  static const Color research = Color(0xFF0891B2);
  static const Color extension = Color(0xFF059669);
  static const Color professional = Color(0xFFD97706);

  static Color kra(KraType type) {
    switch (type) {
      case KraType.instruction:
        return instruction;
      case KraType.research:
        return research;
      case KraType.extension:
        return extension;
      case KraType.professionalDevelopment:
        return professional;
    }
  }

  static Color kraSoft(KraType type) {
    switch (type) {
      case KraType.instruction:
        return const Color(0xFFEFF6FF);
      case KraType.research:
        return const Color(0xFFECFEFF);
      case KraType.extension:
        return const Color(0xFFECFDF5);
      case KraType.professionalDevelopment:
        return const Color(0xFFFFFBEB);
    }
  }

  static Color status(DocumentStatus status) {
    switch (status) {
      case DocumentStatus.draft:
        return textSecondary;
      case DocumentStatus.validated:
        return success;
      case DocumentStatus.systemApproved:
        return success;
      case DocumentStatus.pendingReview:
        return warning;
      case DocumentStatus.needsRevision:
        return error;
      case DocumentStatus.invalid:
        return textSecondary;
      case DocumentStatus.processing:
        return processing;
    }
  }

  static Color statusSoft(DocumentStatus status) {
    switch (status) {
      case DocumentStatus.draft:
        return surfaceMuted;
      case DocumentStatus.validated:
        return successSoft;
      case DocumentStatus.systemApproved:
        return successSoft;
      case DocumentStatus.pendingReview:
        return warningSoft;
      case DocumentStatus.needsRevision:
        return errorSoft;
      case DocumentStatus.invalid:
        return surfaceMuted;
      case DocumentStatus.processing:
        return processingSoft;
    }
  }
}
