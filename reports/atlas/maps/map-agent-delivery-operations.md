# map-agent-delivery-operations

Observer: maintainer coordinating AI execution, validation, PR review, and command-bus receipt

Decision question: Which delivery steps should remain human/accountable, which can be automated, and which are rented infrastructure?

Value recipient / affected subject: user, maintainer, reviewers, and future agents

Claim ceiling: `derived_operations_navigation_view`

## Map

```mermaid
flowchart LR
  user_request["User request<br/>GENESIS<br/>preserve"]
  command_bus["1111 command bus<br/>CUSTOM_BUILT<br/>preserve"]
  codex_execution["Codex execution session<br/>PRODUCT_RENTAL<br/>rent"]
  repo_artifacts["Repository artifacts<br/>CUSTOM_BUILT<br/>preserve"]
  local_validation["Local validation<br/>CUSTOM_BUILT<br/>automate"]
  remote_ci["Remote CI<br/>COMMODITY_UTILITY<br/>rent"]
  draft_pr["Draft PR<br/>COMMODITY_UTILITY<br/>standardize"]
  receipt["1111 result receipt<br/>CUSTOM_BUILT<br/>preserve"]
  user_request -->|information_flow| command_bus
  command_bus -->|control_flow| codex_execution
  codex_execution -->|information_flow| repo_artifacts
  repo_artifacts -->|evidence_flow| local_validation
  repo_artifacts -->|evidence_flow| remote_ci
  repo_artifacts -->|control_flow| draft_pr
  draft_pr -->|information_flow| receipt
```

## Unmapped Residue

- residue-human-review-quality: Actual quality and independence of future human/GPT review. (Requires later review behavior, not current repository topology.)
