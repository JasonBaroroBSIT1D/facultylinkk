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

  @override
  Widget build(BuildContext context) {
    final sim = widget.simulation;
    final readiness = (sim.progress * 100).round();
    final kraTotal = sim.currentPoints.toDouble();
    final pad = widget.compact ? 16.0 : 20.0;

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
              AnimatedBuilder(
                animation: _motion,
                builder: (context, child) {
                  final pop = Curves.easeOutBack.transform(
                    _motion.value.clamp(0.0, 1.0),
                  );
                  return Transform.scale(scale: 0.86 + (0.14 * pop), child: child);
                },
                child: Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.white.withValues(alpha: 0.45),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.check_rounded,
                    size: 18,
                    color: AppColors.forestMid,
                  ),
                ),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'Simulation Result',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 16,
                    letterSpacing: 0.2,
                  ),
                ),
              ),
              if (widget.onTap != null)
                Icon(
                  Icons.chevron_right_rounded,
                  color: Colors.white.withValues(alpha: 0.75),
                ),
            ],
          ),
          SizedBox(height: widget.compact ? 16 : 20),
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
                padding: const EdgeInsets.only(top: 18),
                child: Icon(
                  Icons.arrow_forward_rounded,
                  color: Colors.white.withValues(alpha: 0.92),
                  size: 18,
                ),
              ),
              Expanded(
                child: _RankBlock(
                  caption: 'Eligible For',
                  value: sim.targetRank,
                  alignEnd: true,
                ),
              ),
            ],
          ),
          SizedBox(height: widget.compact ? 14 : 18),
          Divider(height: 1, color: Colors.white.withValues(alpha: 0.18)),
          SizedBox(height: widget.compact ? 12 : 16),
          AnimatedBuilder(
            animation: _motion,
            builder: (context, _) {
              final t = Curves.easeOutCubic.transform(_motion.value);
              return Row(
                children: [
                  _StatBlock(
                    value: '${(readiness * t).round()}%',
                    label: 'Readiness',
                  ),
                  _StatBlock(
                    value: (kraTotal * t).toStringAsFixed(1),
                    label: 'KRA Total',
                  ),
                  const _StatBlock(
                    value: 'Pending',
                    label: 'Status',
                  ),
                ],
              );
            },
          ),
        ],
      ),
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
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          textAlign: alignEnd ? TextAlign.right : TextAlign.left,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w800,
            fontSize: 16,
            height: 1.2,
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
              fontSize: 22,
              height: 1.1,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: AppColors.mint.withValues(alpha: 0.92),
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
