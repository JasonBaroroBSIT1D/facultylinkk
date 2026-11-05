import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../theme/app_colors.dart';

class SimulationResultCard extends StatefulWidget {
  const SimulationResultCard({
    super.key,
    required this.simulation,
    this.onTap,
    this.compact = false,
    this.play = true,
  });

  final RankSimulation simulation;
  final VoidCallback? onTap;
  final bool compact;
  final bool play;

  @override
  State<SimulationResultCard> createState() => _SimulationResultCardState();
}

class _SimulationResultCardState extends State<SimulationResultCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _motion;

  @override
  void initState() {
    super.initState();
    _motion = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    if (widget.play) {
      _motion.forward();
    } else {
      _motion.value = 1;
    }
  }

  @override
  void didUpdateWidget(covariant SimulationResultCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.play && !oldWidget.play) {
      _motion.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _motion.dispose();
    super.dispose();
  }

  static String _fmt(num? v) {
    if (v == null) return '—';
    return v.toStringAsFixed(2);
  }

  @override
  Widget build(BuildContext context) {
    final sim = widget.simulation;
    if (sim.isPlaceholder) {
      return Container(
        width: double.infinity,
        padding: EdgeInsets.all(widget.compact ? 16 : 20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Simulation Result',
              style: TextStyle(
                fontWeight: FontWeight.w800,
                fontSize: 16,
                color: AppColors.navy,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              sim.eligibilityLabel,
              style: const TextStyle(
                fontSize: 13,
                height: 1.45,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      );
    }

    final weightedTotal = sim.weightedEstimatedScore;
    final readiness = sim.preparationReadinessPercentage;
    final readinessLabel = readiness != null
        ? '${readiness.round()}%'
        : 'N/A';
    final pad = widget.compact ? 14.0 : 18.0;
    final kraLabels = ['Instruction', 'Research', 'Extension', 'Prof. Dev.'];
    final kraKeys = ['kra1', 'kra2', 'kra3', 'kra4'];

    return AnimatedBuilder(
      animation: _motion,
      builder: (context, child) {
        final glow = 0.16 + (0.12 * math.sin(_motion.value * math.pi));
        final shimmer = (_motion.value * 1.2).clamp(0.0, 1.0);

        return Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF0F2E24),
                AppColors.forest,
                AppColors.forestMid,
                Color(0xFF2A6B4E),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.forest.withValues(alpha: 0.34 + glow * 0.45),
                blurRadius: 24,
                offset: const Offset(0, 12),
              ),
              BoxShadow(
                color: AppColors.gold.withValues(alpha: glow),
                blurRadius: 20,
              ),
            ],
          ),
          foregroundDecoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            gradient: LinearGradient(
              begin: Alignment(-1.5 + (2.5 * shimmer), -0.4),
              end: Alignment(-0.6 + (2.5 * shimmer), 0.5),
              colors: [
                Colors.white.withValues(alpha: 0),
                Colors.white.withValues(alpha: 0.14),
                AppColors.gold.withValues(alpha: 0.12),
                Colors.white.withValues(alpha: 0),
              ],
            ),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(22),
              onTap: widget.onTap,
              child: Padding(
                padding: EdgeInsets.all(pad),
                child: child,
              ),
            ),
          ),
        );
      },
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Simulation Result',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 15,
                    letterSpacing: 0.2,
                  ),
                ),
              ),
              Icon(
                Icons.chevron_right_rounded,
                color: Colors.white.withValues(alpha: 0.75),
              ),
            ],
          ),
          SizedBox(height: widget.compact ? 12 : 14),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _RankBlock(
                  caption: 'Current Rank',
                  value: sim.currentRank,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Icon(
                  Icons.arrow_forward_rounded,
                  color: Colors.white.withValues(alpha: 0.92),
                  size: 16,
                ),
              ),
              Expanded(
                child: _RankBlock(
                  caption: 'Possible Rank',
                  value: sim.displayPossibleRank,
                  alignEnd: true,
                ),
              ),
            ],
          ),
          SizedBox(height: widget.compact ? 10 : 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final narrow = constraints.maxWidth < 340;
              return Column(
                children: [
                  Row(
                    children: [
                      for (var i = 0; i < 4; i++)
                        Expanded(
                          child: _KraMini(
                            label: narrow && i == 3 ? 'Prof.' : kraLabels[i],
                            value: _fmt(sim.contributionForKra(kraKeys[i])),
                          ),
                        ),
                    ],
                  ),
                ],
              );
            },
          ),
          SizedBox(height: widget.compact ? 10 : 12),
          Divider(height: 1, color: Colors.white.withValues(alpha: 0.18)),
          const SizedBox(height: 10),
          Row(
            children: [
              _StatBlock(
                value: _fmt(weightedTotal),
                label: 'Weighted Total',
              ),
              _StatBlock(
                value: readinessLabel,
                label: 'Readiness',
              ),
              _StatBlock(
                value: sim.homeStatusLabel,
                label: 'Status',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _KraMini extends StatelessWidget {
  const _KraMini({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.mint.withValues(alpha: 0.88),
            fontSize: 9.5,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 13,
          ),
        ),
      ],
    );
  }
}

class _RankBlock extends StatelessWidget {
  const _RankBlock({
    required this.caption,
    required this.value,
    this.alignEnd = false,
  });

  final String caption;
  final String value;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Text(
          caption,
          style: TextStyle(
            color: AppColors.mint.withValues(alpha: 0.88),
            fontSize: 10,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 14,
            height: 1.15,
          ),
        ),
      ],
    );
  }
}

class _StatBlock extends StatelessWidget {
  const _StatBlock({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(
            value,
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w800,
              fontSize: 17,
              height: 1.1,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.mint.withValues(alpha: 0.92),
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
