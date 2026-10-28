# 083 Quality Window Report

**Date:** 2026-07-13  
**Task:** IGNITION-20260709-083

## Overview

617 adjudication records divided into 6 audit windows. Each window independently assessed for source file existence, anchor coverage, template occupancy, strong assertion gaps, correction queue hits, and escalation routing distribution.

## Window Details

### W1: Records 1-100

| Metric | Value |
|--------|-------|
| Record count | 100 |
| Source file exists | 100/100 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 92 |
| Template: failure_conditions | 92 |
| Template: confidence=0.65 | 82 |
| Strong assertion missed | 0 |
| Correction queue hits | 28 |
| Escalation: MAX_REQUIRED | 55 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 23 |
| Escalation: NO_ESCALATION_NEEDED | 1 |
| Not escalated | 21 |

### W2: Records 101-200

| Metric | Value |
|--------|-------|
| Record count | 100 |
| Source file exists | 100/100 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 92 |
| Template: failure_conditions | 92 |
| Template: confidence=0.65 | 81 |
| Strong assertion missed | 0 |
| Correction queue hits | 15 |
| Escalation: MAX_REQUIRED | 58 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 22 |
| Escalation: NO_ESCALATION_NEEDED | 0 |
| Not escalated | 20 |

### W3: Records 201-300

| Metric | Value |
|--------|-------|
| Record count | 100 |
| Source file exists | 100/100 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 92 |
| Template: failure_conditions | 92 |
| Template: confidence=0.65 | 81 |
| Strong assertion missed | 0 |
| Correction queue hits | 15 |
| Escalation: MAX_REQUIRED | 57 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 21 |
| Escalation: NO_ESCALATION_NEEDED | 1 |
| Not escalated | 21 |

### W4: Records 301-400

| Metric | Value |
|--------|-------|
| Record count | 100 |
| Source file exists | 100/100 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 92 |
| Template: failure_conditions | 92 |
| Template: confidence=0.65 | 84 |
| Strong assertion missed | 0 |
| Correction queue hits | 8 |
| Escalation: MAX_REQUIRED | 59 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 21 |
| Escalation: NO_ESCALATION_NEEDED | 1 |
| Not escalated | 19 |

### W5: Records 401-500

| Metric | Value |
|--------|-------|
| Record count | 100 |
| Source file exists | 100/100 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 92 |
| Template: failure_conditions | 92 |
| Template: confidence=0.65 | 88 |
| Strong assertion missed | 0 |
| Correction queue hits | 44 |
| Escalation: MAX_REQUIRED | 57 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 24 |
| Escalation: NO_ESCALATION_NEEDED | 0 |
| Not escalated | 19 |

### W6: Records 501-617

| Metric | Value |
|--------|-------|
| Record count | 117 |
| Source file exists | 117/117 (100%) |
| Anchor hit rate | 100% |
| Template: hidden_premises | 107 |
| Template: failure_conditions | 107 |
| Template: confidence=0.65 | 88 |
| Strong assertion missed | 0 |
| Correction queue hits | 45 |
| Escalation: MAX_REQUIRED | 67 |
| Escalation: GLM_HIGH_CAN_RESOLVE | 39 |
| Escalation: NO_ESCALATION_NEEDED | 0 |
| Not escalated | 11 |

## Cross-Window Observations

1. Source file existence and anchor coverage are 100% across all windows
2. Template occupancy is consistently high (~91.9%) across all windows, confirming systematic defect
3. Correction queue hits are concentrated in W5 (44) and W6 (45), which contain the D-series records
4. No strong assertion missed escalation in any window
5. Escalation routing is dominated by MAX_REQUIRED across all windows
