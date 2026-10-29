# Probabilistic System Dynamics / 概率—系统动力学

Status: candidate derived operational extension to MCF.

Probabilistic System Dynamics (PSD) extends the Multiscale Causal Fabric with first-class probability semantics and system-dynamics objects. PSD is not a new truth layer. It does not replace Foundation, MCF, Function OS, Q12-Q14, or Charter Gate.

## Boundaries

- Deterministic causality can exist without probability.
- A general causal fabric needs probability only when modeling stochastic systems, partial observability, finite knowledge, measurement error, sampling, priors, posterior beliefs, path distributions, or tail risk.
- `P(Y|X)` is not `P(Y|do(X))`.
- High probability is not strong causality. Low probability is not absence of causality.
- Bayesian posterior, frequency probability, physical randomness, model uncertainty, and measurement error must not be mixed.
- System boundaries are observer- and question-conditioned modeling choices. They are not automatically natural unique partitions of the world.
- PSD does not assume Markov, stationary, ergodic, linear, Gaussian, or closed-system structure unless the record declares it.
- Shannon/information entropy and thermodynamic entropy are separate unless a source-specific thermodynamic model links them.

## Objects

- `SystemContext`: boundary, environment, input/output, exchanges, nested systems, observer frame, and purpose.
- `StateSpace`: observed and latent variables, discrete/continuous/hybrid status, constraints, units, scale, and coarse graining.
- `TransitionLaw`: deterministic, stochastic, or hybrid dynamics; update equation; transition kernel; generator; time semantics; assumptions.
- `ProbabilitySemantics`: aleatoric, epistemic, measurement, sampling, subjective prior, posterior, or unknown source.
- `EventIntensityOrHazard`: event rate, risk set, time window, and conditioning set.
- `TrajectoryDistribution`: path space, path probability or weight, initial distribution, and boundary conditions.
- `InterventionDistribution`: observational/interventional separation, policy/action, target, support, and identifiability.
- `NoiseProcess`: exogenous/endogenous noise, additive/multiplicative form, independence/correlation, stationarity status.
- `SystemCoupling`: coupled subsystems, channels, shared environment, bidirectionality, and delay.
- `StabilityAttractorRecord`: equilibrium, attractor, basin, stability, bifurcation, or phase-transition status.
- `ObservabilityControllabilityRecord`: observed variables, hidden variables, controls, and limits.
- `CoarseGrainingEmergenceRecord`: micro/macro map, information loss, effective information comparator, and claim ceiling.
- `RareEventTailRecord`: low-frequency/high-impact event definition, tail model, uncertainty, and risk bearers.
- `ProbabilityCalibrationRecord`: forecast, outcome, score, sample window, and calibration boundary.

## Integration

Foundation decides evidence status and claim ceilings. MCF organizes causal representation. PSD describes how states evolve deterministically or stochastically within declared systems. Function OS can execute specified PSD checks. Q12 decides state-changing action and mechanism sketches. Q13 prevents probability narratives and numerical precision from becoming false certainty. Q14 can project PSD maps, but visual position and numbers are not proof. Charter Gate records who bears probability risk, especially tail risk and irreversible harm.
