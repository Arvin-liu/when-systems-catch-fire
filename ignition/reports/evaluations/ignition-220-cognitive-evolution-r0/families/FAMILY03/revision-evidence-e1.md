# FAMILY03 — E1 observed counterexample packet

**Evidence ID:** CE-F03-E1-R0  
**Evidence class:** fresh synthetic cold-chain observations; locators bind trace, interval logger, assay, and custody records.

## Capture and custody record

Six shipments were observed with independently calibrated 15-minute shipment loggers and a second one-minute trace logger at the same product location. Clocks were aligned to within 40 seconds; calibration checks were within ±0.15 °C; seal and custody logs had no gaps. Retained-sample activity assays were run in duplicate by a lab blind to the logger summaries. Source record sets: F03-E1-INTERVAL-LOG, F03-E1-HIGH-RATE-TRACE, F03-E1-ACTIVITY-ASSAY, F03-E1-CUSTODY-CALIBRATION.

The fictional registry identifies formulation groups by their ordinary shipment and handling records. Group S had prior continuous-profile validation in F03-M0-STABILITY-VALIDATION; group P is a separately documented formulation with a different stability response. The ID is not an assignment label for future tasks.

## Exact observations

| Locator | Formulation and trace | 15-minute shipment mean | Highest one-minute interval | Pulse duration above 12 °C | Activity retained | Assay repeat |
|---|---|---:|---:|---:|---:|---:|
| OBS-01 | group P; warm dock handoff trace | 6.1 °C | 14.2 °C | 11 min | 88.4% | 88.1 / 88.7% |
| OBS-02 | group P; repeated route and unit | 6.3 °C | 13.7 °C | 9 min | 90.1% | 89.8 / 90.4% |
| OBS-03 | group P; second unit, separate shipment | 6.0 °C | 14.4 °C | 13 min | 85.9% | 85.4 / 86.4% |
| OBS-04 | group S; matched 15-minute mean, brief dock pulse | 6.2 °C | 14.0 °C | 10 min | 98.7% | 98.3 / 99.1% |
| OBS-05 | group P; no observed pulse, continuous profile | 6.5 °C | 7.1 °C | 0 min | 99.0% | 98.6 / 99.4% |
| OBS-06 | group P; high-rate trace gap across handoff | 6.2 °C | 11.8 °C observed | unknown | 93.0% | 90.5 / 95.5% |

All six shipment-wide and eight-hour means are at or below M0's 8.0 °C cutoff and would produce SCREEN_PASS if identity and 15-minute record completeness alone were considered. The independent assay reference for the synthetic stability protocol is 95% activity retained. OBS-01 through OBS-03 repeatedly fall below that reference while their high-rate traces show short pulses. OBS-04 has a similar pulse record and mean but remains within assay reference on group S. OBS-05 is a within-M0 stable control for group P. OBS-06 has an unresolved trace gap and assay disagreement.

## Competing readings and limits

The source rows establish a reproducible contradiction to mean-only screening for the observed group-P pulse cases while retaining a stable continuous-profile group-P case and a pulsed group-S case. The group and detailed exposure are independently recorded and not inferred from the assay. The records do not support treating every isolated high sample as a confirmed degradation event, and OBS-06 does not identify whether a pulse occurred. The pulse amplitudes/durations observed here do not establish a universal threshold for every formulation or logger cadence.

A tempting but unsupported overreaction is to classify any one-minute reading above 8 °C as a confirmed product failure or to discard all logger-based screening. M0's calibration, custody, continuous-profile behavior, and the product-specific contrast remain separately observable.

## Source locators

- F03-E1-INTERVAL-LOG#OBS-01 … #OBS-06: 15-minute samples and calculated means.
- F03-E1-HIGH-RATE-TRACE#OBS-01 … #OBS-06: one-minute temperatures and trace gaps.
- F03-E1-ACTIVITY-ASSAY#OBS-01 … #OBS-06: duplicate retained-sample assay results.
- F03-E1-CUSTODY-CALIBRATION#ALL: identity, clock, calibration, seal, and custody records.

No replacement statistic, pulse threshold, revised screen, held-out case, sealed target, condition label, or scoring rule is supplied here.
