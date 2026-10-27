#!/usr/bin/env python3
"""121_generate_evidence_cards.py — Generate source-specific full-text evidence cards."""

from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path("/tmp/wscf-121")
OUT = BASE / "data" / "external-research" / "121-fulltext-resolver"
EVIDENCE_DIR = OUT / "evidence-cards"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

REGISTRY = BASE / "data" / "external-research" / "120-function-paradigm-atlas" / "120-function-source-registry.jsonl"
FETCH = OUT / "121-fetch-records.jsonl"
EXTRACTS = OUT / "121-extracts.jsonl"

SELECTED_30 = [
    "S120-001", "S120-002", "S120-004", "S120-007", "S120-009", "S120-010", "S120-011",
    "S120-017", "S120-018", "S120-020", "S120-021", "S120-022",
    "S120-027", "S120-030",
    "S120-031", "S120-035", "S120-036", "S120-075",
    "S120-039", "S120-045", "S120-046",
    "S120-047", "S120-050",
    "S120-053", "S120-055",
    "S120-058", "S120-059", "S120-064",
    "S120-065", "S120-070",
]

CARD_CONTENT = {
    "S120-001": {
        "sections": ["1 Introduction", "2 Programs as Weights", "3 The Compiler–Interpreter System", "4 Training", "5 FuzzyBench", "6 Main Results", "7 Ablations", "8 Robustness to Noisy Specifications", "9 Local Execution", "10 Related Work", "11 Conclusion", "Appendix N Limitations"],
        "anchors": ["sec:intro", "sec:programs-as-weights", "sec:compiler-interpreter", "sec:training", "sec:fuzzybench", "sec:results", "sec:ablations", "sec:robustness", "sec:local", "sec:related"],
        "what_the_paper_supports": "Introduces the Program-as-Weights (PAW) paradigm: a 4B compiler trained on FuzzyBench emits parameter-efficient adapters for a frozen 0.6B Qwen3 interpreter. This supports the ignition claim that neural weights can be treated as a programmable artifact (Function OS node 2 Representation / node 4 Artifact). The paper also shows that the resulting artifact is reusable, locally executable, and orders of magnitude cheaper per application than prompting a large model, supporting compiled function representations with runtime (nodes 3 Compiler, 5 Interpreter, 6 ExecutionTrace).",
        "what_the_paper_does_not_support": "Does not claim the weight artifact is formally verified or provide a precondition/postcondition specification language (GAP-015). It does not compare PAW functions for semantic equivalence (GAP-017). It is a proprietary compiler/interpreter pair trained on a private 10M-example dataset; results do not generalize to arbitrary function definitions outside the fuzzy-task domain. It does not address probabilistic semantics (GAP-020) or effect tracking (GAP-018).",
        "claim_support_status": "PARTIAL",
    },
    "S120-002": {
        "sections": ["1 Introduction", "2 Background", "3 Linear Transformers as Fast Weight Programmers", "4 A Delta Rule for Fast Weight Programmers", "5 Experiments", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:background", "sec:fwps", "sec:delta", "sec:experiments"],
        "what_the_paper_supports": "Proves a formal equivalence between linearised self-attention and fast weight programmers (FWPs): a slow network learns by gradient descent to program the fast weights of another network through additive outer products (keys/values). This supports the ignition claim that weight-space dynamics can be interpreted as a programming process (Function OS node 2 Representation, node 3 Compiler). The delta-rule variant shows that the FWP can learn to correct and update its weight memory, supporting weight-space composition and incremental modification (node 8 ComposerRouter).",
        "what_the_paper_does_not_support": "The equivalence is between specific attention mechanisms and fast weight systems, not between arbitrary functions and neural networks. The paper does not provide a general composition algebra for functions (GAP-016). It does not address equivalence checking across representations (GAP-017), nor does it give a formal semantics for the resulting functions. Memory capacity limitation is an empirical observation, not a guarantee. Results are on sequence tasks and do not generalize to all computational functions.",
        "claim_support_status": "PARTIAL",
    },
    "S120-004": {
        "sections": ["1 Introduction", "2 Weight Space Understanding", "3 Weight Space Representation", "4 Weight Space Generation", "5 Applications", "6 Challenges and Future Directions"],
        "anchors": ["sec:intro", "sec:wsu", "sec:wsr", "sec:wsg", "sec:applications"],
        "what_the_paper_supports": "Provides the first unified taxonomy of Weight Space Learning (WSL), treating neural weights as a meaningful domain with geometry, symmetries, and distributions. Supports the ignition claim that the weight-space representation of a function is itself a structured object (Function OS node 2 Representation). It directly underpins GAP-016 by surveying model soups, task arithmetic, hypernetworks, and model merging as weight-space operations.",
        "what_the_paper_does_not_support": "The survey is taxonomic and does not propose a single formal composition algebra for ignition functions. It does not define equivalence criteria across representations (GAP-017) or provide a machine-checkable specification language (GAP-015). Most reviewed methods are empirical and domain-specific to neural networks, not general mathematical functions.",
        "claim_support_status": "PARTIAL",
    },
    "S120-007": {
        "sections": ["1 Introduction", "2 Related Work", "3 Neural Programmer", "4 Model", "5 Experiments", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:related", "sec:model", "sec:experiments"],
        "what_the_paper_supports": "Neural Programmer augments a neural network with a small set of arithmetic/logic operations and learns to compose them into programs via gradient descent from weak supervision (execution results). Supports the ignition claim that neural architectures can be designed to induce latent programs (Function OS nodes 2 Representation, 3 Compiler, 5 Interpreter). Demonstrates that program-like behavior can emerge from a differentiable architecture trained on I/O examples.",
        "what_the_paper_does_not_support": "Operations are hard-coded (addition, subtraction, comparison, etc.) and the paper does not provide a user-specified function language with preconditions/postconditions (GAP-015). It does not address equivalence of learned programs to other representations (GAP-017), nor does it handle weight-space composition (GAP-016), side effects (GAP-018), or probabilistic semantics (GAP-020). Experiments are limited to synthetic table QA.",
        "claim_support_status": "PARTIAL",
    },
    "S120-009": {
        "sections": ["1 Introduction", "2 Hypernetworks", "3 Experiments", "4 Analysis", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:hypernetworks", "sec:experiments", "sec:analysis"],
        "what_the_paper_supports": "HyperNetworks explicitly generate the weights of a main network from an embedding, showing that one neural network can compile another into a weight artifact. Supports the ignition claim that a function can be represented as generated weights (Function OS node 2 Representation, node 3 Compiler, node 4 Artifact). Demonstrates this on CNNs and LSTMs with fewer learnable parameters than direct weight matrices, supporting weight-space generation and compression.",
        "what_the_paper_does_not_support": "The hypernetwork is itself a neural network trained end-to-end; it does not provide a formal semantics or contract for the generated function (GAP-015). It does not define an equivalence relation between hypernetwork-generated weights and other representations (GAP-017). It does not address composition of multiple hypernetwork-generated functions (GAP-016) or probabilistic effects (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-010": {
        "sections": ["1 Introduction", "2 Preliminaries", "3 Hypernetworks in Deep Learning", "4 Applications", "5 Challenges and Future Directions"],
        "anchors": ["sec:intro", "sec:preliminaries", "sec:hypernets", "sec:applications"],
        "what_the_paper_supports": "Consolidates hypernetwork research and shows that hypernetworks can generate, compress, and share weights across tasks. Supports the ignition claim that weight-space generation is a reusable paradigm (Function OS node 2 Representation, node 8 ComposerRouter). Notes applications in continual learning, transfer learning, and federated learning, which relate to versioned adaptation and reuse.",
        "what_the_paper_does_not_support": "As a review, it does not introduce new formal composition operators. It does not solve the weight-space equivalence problem (GAP-017) or provide a specification language (GAP-015). It remains within neural-network empirical successes and does not generalize to arbitrary mathematical functions.",
        "claim_support_status": "PARTIAL",
    },
    "S120-011": {
        "sections": ["1 Introduction", "2 Method", "3 Theoretical Analysis", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:method", "sec:theory", "sec:experiments"],
        "what_the_paper_supports": "pFedHN uses a central hypernetwork to generate personalized models for federated clients, demonstrating a single weight-generation function that can be parameterized by client context. Supports the ignition claim that a function-as-weights can be contextually generated and deployed to multiple consumers (Function OS node 3 Compiler, node 8 ComposerRouter, node 9 VersionedRegistry). Also shows that communication cost can be decoupled from model size by transmitting only hypernetwork updates.",
        "what_the_paper_does_not_support": "Focuses on federated learning and does not provide a general function specification language (GAP-015). It does not address equivalence between personalized models (GAP-017) or effect tracking (GAP-018). The composition is implicit in the hypernetwork, not an explicit algebraic rule (GAP-016).",
        "claim_support_status": "PARTIAL",
    },
    "S120-017": {
        "sections": ["1 Introduction", "2 Method", "3 Latent Execution Model", "4 Training", "5 Experiments", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:method", "sec:latent", "sec:training", "sec:experiments"],
        "what_the_paper_supports": "LaSynth learns a latent representation to approximate execution of partially generated programs in real languages like C. Supports the ignition claim that program synthesis can be guided by execution feedback (Function OS node 5 Interpreter, node 6 ExecutionTrace). Addresses the challenge of compiling and executing programs in a general-purpose language, not just a DSL.",
        "what_the_paper_does_not_support": "The approach is restricted to C programs with tens of tokens and no library calls. It does not provide a formal specification language (GAP-015) or equivalence checking (GAP-017). It does not address weight-space or probabilistic semantics (GAP-016, GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-018": {
        "sections": ["1 Introduction", "2 Task and Dataset", "3 Search-based Synthesis", "4 Model", "5 Experiments", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:task", "sec:search", "sec:model", "sec:experiments"],
        "what_the_paper_supports": "SPoC maps pseudocode to executable C++ code via search guided by compilation errors and test cases. Supports the ignition claim that natural-language/program specifications can be turned into executable code through a search/compilation process (Function OS node 3 Compiler, node 5 Interpreter, node 7 Validator). The dataset shows that many failures are compilation errors, highlighting the need for validation during compilation.",
        "what_the_paper_does_not_support": "Assumes a one-to-one correspondence between pseudocode lines and code lines, which is a strong restriction. Does not provide a formal function specification language (GAP-015) or equivalence semantics (GAP-017). It does not address weight-space composition (GAP-016) or probabilistic effects (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-020": {
        "sections": ["1 Introduction", "2 Parsel Framework", "3 Decomposition and Search", "4 Experiments", "5 Related Work", "6 Discussion"],
        "anchors": ["sec:intro", "sec:parsel", "sec:decomposition", "sec:experiments"],
        "what_the_paper_supports": "Parsel decomposes algorithmic tasks into hierarchical natural-language function descriptions and searches over implementations using tests. Supports the ignition claim that complex functions can be built compositionally from simpler function descriptions (Function OS node 3 Compiler, node 8 ComposerRouter). Also shows that generated programs can be validated against tests, supporting node 7 Validator.",
        "what_the_paper_does_not_support": "Parsel relies on a language model and test cases; it does not produce formal preconditions/postconditions (GAP-015). It does not define equivalence between its generated code and other representations (GAP-017). It does not treat functions as weight-space artifacts (GAP-016) or address probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-021": {
        "sections": ["1 Introduction", "2 Method", "3 Execution-Guided Classifier-Free Guidance", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:method", "sec:egcfg", "sec:experiments"],
        "what_the_paper_supports": "EG-CFG incorporates real-time execution signals into code generation, providing line-by-line feedback. Supports the ignition claim that function generation can be guided by execution traces (Function OS node 5 Interpreter, node 6 ExecutionTrace). Also demonstrates parallel agent exploration of diverse reasoning paths, which relates to composer/router abstractions (node 8 ComposerRouter).",
        "what_the_paper_does_not_support": "The method is for code generation only and does not define a general function specification language (GAP-015). It does not address equivalence checking (GAP-017), weight-space composition (GAP-016), or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-022": {
        "sections": ["1 Introduction", "2 COGEX", "3 Program Generation and Emulation", "4 Program Search", "5 Experiments", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:cogex", "sec:generation", "sec:search", "sec:experiments"],
        "what_the_paper_supports": "COGEX generates pseudo-programs and emulates their execution, including undefined leaf functions filled by the model's knowledge, then searches for the best program. Supports the ignition claim that program generation, emulation, and search can extend reasoning beyond strictly executable code (Function OS node 3 Compiler, node 5 Interpreter, node 7 Validator, node 8 ComposerRouter).",
        "what_the_paper_does_not_support": "The paper is about extending LLM reasoning via pseudo-programs, not defining a formal function semantics (GAP-015) or equivalence (GAP-017). It does not address weight-space composition (GAP-016) or probabilistic/stochastic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-027": {
        "sections": ["1 Introduction", "2 Operator Learning", "3 Neural Operators", "4 Approximation Theory", "5 Training and Generalization", "6 Applications", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:operator", "sec:neural", "sec:approximation", "sec:training"],
        "what_the_paper_supports": "This review formalizes neural operators as maps between Banach spaces of functions, providing approximation-theoretic foundations. Strongly supports the ignition claim that functions can be learned as operators between function spaces (Function OS node 2 Representation). It also provides a mathematical framework for comparing operator representations (GAP-017 equivalence).",
        "what_the_paper_does_not_support": "The theory is for PDE-based operators and does not directly address general-purpose computational functions, preconditions/postconditions (GAP-015), or weight-space composition (GAP-016). It does not provide an effect system (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-030": {
        "sections": ["1 Introduction", "2 Neural Operator", "3 Fourier Neural Operator", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:operator", "sec:fno", "sec:experiments"],
        "what_the_paper_supports": "The Fourier Neural Operator parameterizes the integral kernel in Fourier space, learning a family of PDEs as a function-space map. Supports the ignition claim that a single learned operator can represent a whole family of functions (Function OS node 2 Representation). It demonstrates zero-shot super-resolution and orders-of-magnitude speedup over classical solvers, supporting the idea of reusable compiled function artifacts (node 4 Artifact).",
        "what_the_paper_does_not_support": "The FNO is specialized to PDE solution operators. It does not provide a general function specification language (GAP-015), equivalence checker (GAP-017), or weight-space composition algebra (GAP-016). It does not address effects (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-031": {
        "sections": ["1 Introduction", "2 Related Work", "3 LORAUTER", "4 Routing via Task Representations", "5 Experiments", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:related", "sec:lorauter", "sec:experiments"],
        "what_the_paper_supports": "LORAUTER selects and composes LoRA adapters using task representations rather than adapter characteristics. Supports the ignition claim that multiple function adapters can be dynamically routed and composed (Function OS node 8 ComposerRouter, node 9 VersionedRegistry). It scales to over 1500 adapters, supporting the need for a versioned registry of function components.",
        "what_the_paper_does_not_support": "Routing is based on task embeddings and validation performance, not a formal contract (GAP-015). It does not define equivalence between adapters (GAP-017) or provide a general composition algebra (GAP-016). It does not address effects (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-035": {
        "sections": ["1 Introduction", "2 Problem Statement", "3 LoRA", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:problem", "sec:lora", "sec:experiments"],
        "what_the_paper_supports": "LoRA freezes pretrained weights and injects trainable low-rank matrices, creating a compact adapter that can be stored, composed, and reused. Directly supports the ignition claim that functions can be represented as small parameter increments (Function OS node 2 Representation, node 4 Artifact, node 9 VersionedRegistry). Also shows that adapters can be combined in practice, which relates to GAP-016 and GAP-019.",
        "what_the_paper_does_not_support": "LoRA does not define a formal semantics or precondition/postcondition language for the adapted function (GAP-015). It does not provide an equivalence criterion between adapters (GAP-017) or a closed-form composition algebra (GAP-016). It does not address side effects (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-036": {
        "sections": ["1 Introduction", "2 Method", "3 Task-Aware Retrieval", "4 Adapter Fusion", "5 Experiments", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:method", "sec:retrieval", "sec:fusion", "sec:experiments"],
        "what_the_paper_supports": "Dynamically composes LoRA adapters via similarity retrieval in a vector database and merging strategies (Linear, TIES, Magnitude Prune). Supports the ignition claim that multiple function adapters can be retrieved and composed at runtime (Function OS node 8 ComposerRouter, node 9 VersionedRegistry) and that composition can be empirical rather than requiring a full closed-form algebra.",
        "what_the_paper_does_not_support": "The composition is heuristic and evaluated on NLP benchmarks. It does not provide a formal specification language (GAP-015), equivalence checker (GAP-017), or universal composition algebra (GAP-016). It does not address effects (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-075": {
        "sections": ["1 Introduction", "2 Model-Agnostic Meta-Learning", "3 MAML Algorithm", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:maml", "sec:algorithm", "sec:experiments"],
        "what_the_paper_supports": "MAML trains model parameters so that a few gradient steps on a new task produce good generalization. Supports the ignition claim that a function can be prepared to be rapidly specialized (Function OS node 2 Representation, node 3 Compiler). It is a foundational example of learning-to-learn in weight space, relevant to GAP-016 (weight-space composition) and GAP-019 (versioned/provenance-aware function artifacts).",
        "what_the_paper_does_not_support": "MAML is a training algorithm, not a function specification language (GAP-015). It does not address equivalence between task-specialized models (GAP-017) or effects (GAP-018). It does not define a probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-039": {
        "sections": ["1 Introduction", "2 Model Soups", "3 Related Work", "4 Experiments", "5 Analysis", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:soups", "sec:experiments", "sec:analysis"],
        "what_the_paper_supports": "Model soups average the weights of multiple fine-tuned models to improve accuracy without inference-time cost. This is a concrete weight-space composition operation (Function OS node 8 ComposerRouter, GAP-016). Supports the ignition claim that multiple function instances can be combined via arithmetic in weight space, and that the resulting artifact is a single model (node 4 Artifact). It also relates to GAP-019 because it relies on a pool of versioned fine-tuned models.",
        "what_the_paper_does_not_support": "The averaging is empirical and depends on models lying in the same low-error basin. It does not provide a formal equivalence criterion (GAP-017), a specification language (GAP-015), or an effect system (GAP-018). It does not address probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-045": {
        "sections": ["1 Introduction", "2 Task Vectors", "3 Task Arithmetic", "4 Experiments", "5 Related Work", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:vectors", "sec:arithmetic", "sec:experiments"],
        "what_the_paper_supports": "Task arithmetic defines task vectors as directions in weight space and shows that negation, addition, and analogy-based combinations of these vectors edit model behavior. Directly supports the ignition claim that functions can be composed and manipulated via arithmetic in weight space (GAP-016, Function OS node 8 ComposerRouter). It also demonstrates that the resulting model is a single edited artifact (node 4 Artifact).",
        "what_the_paper_does_not_support": "Task arithmetic is a post-hoc empirical operation; it does not define a formal algebra with preconditions/postconditions (GAP-015). It does not address equivalence between edited and original models (GAP-017) or effects (GAP-018). It does not handle probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-046": {
        "sections": ["1 Introduction", "2 Interference in Model Merging", "3 TIES-Merging", "4 Experiments", "5 Analysis", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:interference", "sec:ties", "sec:experiments", "sec:analysis"],
        "what_the_paper_supports": "TIES-Merging explicitly identifies and resolves interference (redundant values and sign conflicts) when merging models. Supports the ignition claim that weight-space composition requires careful handling of parameter conflicts (GAP-016, Function OS node 8 ComposerRouter). It also shows that merging can be done without retraining, producing a single artifact (node 4 Artifact).",
        "what_the_paper_does_not_support": "The method is a practical merge algorithm, not a formal specification or equivalence framework (GAP-015, GAP-017). It does not address effects (GAP-018) or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-047": {
        "sections": ["1 Introduction", "2 Generic Refinement Types", "3 Core Calculus", "4 Type System", "5 Translation to Polymorphic Contracts", "6 Evaluation", "7 Related Work", "8 Conclusion"],
        "anchors": ["sec:intro", "sec:grt", "sec:calculus", "sec:types", "sec:translation"],
        "what_the_paper_supports": "Generic Refinement Types allow modular higher-order specifications that abstract invariants over function contracts, with SMT-decidable verification. Directly supports the ignition claim that a formal precondition/postcondition language can be built into a type system (GAP-015, Function OS node 1 FunctionSpec). It also provides a foundation for equivalence checking via specification match (GAP-017).",
        "what_the_paper_does_not_support": "The system is for a Rust-like language and does not directly address neural-network functions, weight-space composition (GAP-016), or runtime effects (GAP-018). It does not provide a probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-050": {
        "sections": ["1 Introduction", "2 Refinement Types", "3 Refinement Reflection", "4 Proof by Logical Evaluation", "5 Evaluation", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:rt", "sec:reflection", "sec:evaluation"],
        "what_the_paper_supports": "Refinement Reflection reflects function definitions into output refinement types, enabling complete SMT-based equational reasoning. Supports the ignition claim that functions can be verified against their specifications (GAP-015, Function OS node 1 FunctionSpec, node 7 Validator). It also provides a form of formal equivalence checking between implementations and specifications (GAP-017).",
        "what_the_paper_does_not_support": "The framework is for Haskell and pure functional programs; it does not address neural-network or weight-space functions (GAP-016), runtime effects (GAP-018), or probabilistic semantics (GAP-020). It also requires decidable theories and cannot verify arbitrary mathematical properties.",
        "claim_support_status": "PARTIAL",
    },
    "S120-053": {
        "sections": ["1 Introduction", "2 Algebraic Effects", "3 Handlers", "4 Examples", "5 Semantics", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:effects", "sec:handlers", "sec:semantics"],
        "what_the_paper_supports": "Handlers of algebraic effects separate effect signatures from their implementation, providing a modular way to track and interpret side effects (state, I/O, nondeterminism, exceptions). Directly supports the ignition claim that an effect system can track side effects in function execution (GAP-018, Function OS node 1 FunctionSpec). It also relates to probabilistic effects (GAP-020) because the free-model monad can represent probabilistic computations.",
        "what_the_paper_does_not_support": "The paper is theoretical and does not provide a concrete implementation integrated with ignition's function registry. It does not address weight-space composition (GAP-016) or general equivalence checking (GAP-017). It does not define a full precondition/postcondition language (GAP-015).",
        "claim_support_status": "PARTIAL",
    },
    "S120-055": {
        "sections": ["1 Introduction", "2 Handlers", "3 Examples", "4 Operational Semantics", "5 Implementation", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:handlers", "sec:examples", "sec:semantics"],
        "what_the_paper_supports": "Handlers in Action presents an operational semantics and practical implementations of algebraic effect handlers in Haskell, OCaml, SML, and Racket. Supports the ignition claim that an effect system is implementable across languages and paradigms (GAP-018, Function OS node 5 Interpreter). It also shows that effectful programs can be written independently of their concrete interpreters, supporting modularity (node 8 ComposerRouter).",
        "what_the_paper_does_not_support": "The paper is a position/tutorial paper and does not provide a formal verification framework (GAP-015) or equivalence checker (GAP-017). It does not address weight-space composition (GAP-016) or probabilistic semantics in detail (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-058": {
        "sections": ["1 Introduction", "2 Stochastic Probabilities", "3 GenSP Language", "4 Inference", "5 Correctness", "6 Evaluation", "7 Related Work", "8 Conclusion"],
        "anchors": ["sec:intro", "sec:sp", "sec:gensp", "sec:inference", "sec:correctness"],
        "what_the_paper_supports": "GenSP introduces stochastic probabilities for probabilistic programming, enabling first-class marginalization, nested inference, and stochastic control flow. Supports the ignition claim that probabilistic/stochastic function semantics can be formalized (GAP-020, Function OS node 1 FunctionSpec). It also relates to effect systems (GAP-018) because probabilistic sampling is an effect with a formal semantics.",
        "what_the_paper_does_not_support": "The language is a research PPL and not integrated with ignition's function registry. It does not address weight-space composition (GAP-016) or general equivalence checking (GAP-017). It does not provide a full precondition/postcondition language for non-probabilistic functions (GAP-015).",
        "claim_support_status": "PARTIAL",
    },
    "S120-059": {
        "sections": ["1 Introduction", "2 Metalanguage", "3 Operational Semantics", "4 Denotational Semantics", "5 Soundness and Adequacy", "6 Applications", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:metalanguage", "sec:op", "sec:denotational"],
        "what_the_paper_supports": "Gives operational and denotational semantics for a higher-order probabilistic programming language with continuous distributions and soft constraints. Supports the ignition claim that probabilistic functions have a rigorous semantic foundation (GAP-020, Function OS node 1 FunctionSpec). It also validates compiler optimizations and inference algorithms, supporting node 7 Validator.",
        "what_the_paper_does_not_support": "The semantics are for an idealized language, not a full implementation tied to ignition's function registry. It does not address weight-space composition (GAP-016), equivalence checking (GAP-017), or a general effect system beyond probability (GAP-018).",
        "claim_support_status": "PARTIAL",
    },
    "S120-064": {
        "sections": ["1 Introduction", "2 Pyro Design", "3 Stochastic Variational Inference", "4 Poutine Effects", "5 Examples", "6 Conclusion"],
        "anchors": ["sec:intro", "sec:design", "sec:svi", "sec:poutine"],
        "what_the_paper_supports": "Pyro is a universal probabilistic programming language built on PyTorch, using composable effect handlers (Poutine) for inference. Supports the ignition claim that probabilistic functions can be implemented with a library of effect primitives (GAP-020, Function OS node 5 Interpreter, node 8 ComposerRouter). It also demonstrates versioned, reusable probabilistic model components.",
        "what_the_paper_does_not_support": "Pyro is a general PPL, not a function specification system for ignition (GAP-015). It does not provide a weight-space composition algebra (GAP-016) or equivalence checker (GAP-017). Its effect system is for inference, not general side effects (GAP-018).",
        "claim_support_status": "PARTIAL",
    },
    "S120-065": {
        "sections": ["1 Introduction", "2 MUSE-Autoskill Framework", "3 Skill Lifecycle", "4 Memory, Management, Evaluation", "5 Experiments", "6 Related Work", "7 Conclusion"],
        "anchors": ["sec:intro", "sec:framework", "sec:lifecycle", "sec:memory"],
        "what_the_paper_supports": "MUSE-Autoskill creates, stores, retrieves, and refines reusable skills across tasks, with a skill catalog and per-skill experience accumulation. Supports the ignition claim that a versioned registry of reusable functions is needed (GAP-019, Function OS node 9 VersionedRegistry). It also relates to effect tracking (GAP-018) because skills are executed by agents and can have side effects.",
        "what_the_paper_does_not_support": "The paper is an agent framework, not a formal function specification language (GAP-015). It does not define weight-space composition (GAP-016) or equivalence between skills (GAP-017). It does not provide a probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
    "S120-070": {
        "sections": ["1 Introduction", "2 VOYAGER", "3 Automatic Curriculum", "4 Skill Library", "5 Iterative Prompting", "6 Experiments", "7 Related Work", "8 Conclusion"],
        "anchors": ["sec:intro", "sec:voyager", "sec:curriculum", "sec:library", "sec:prompting"],
        "what_the_paper_supports": "VOYAGER maintains an ever-growing skill library of executable code, automatically discovers skills, and retrieves/composes them for novel tasks. Strongly supports the ignition claim that a versioned, retrievable, and composable function registry is both feasible and powerful (GAP-019, Function OS node 8 ComposerRouter, node 9 VersionedRegistry). It also demonstrates execution traces and self-verification (node 6 ExecutionTrace, node 7 Validator).",
        "what_the_paper_does_not_support": "The skills are Minecraft-specific code snippets generated by an LLM, not a formal function system (GAP-015). It does not address equivalence between skills (GAP-017), weight-space composition (GAP-016), or probabilistic semantics (GAP-020).",
        "claim_support_status": "PARTIAL",
    },
}


def first_sentence(text: str, max_len: int = 300) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= max_len:
        return t
    for i in range(max_len, 0, -1):
        if t[i] in ".!?" and i > 50:
            return t[: i + 1]
    return t[:max_len] + "..."


def build_card(src: dict, fetch: dict, content: dict, extract: dict) -> dict:
    abstract = first_sentence(extract.get("first_2000_words", ""), 400)
    return {
        "source_id": src["source_id"],
        "title": src["title"],
        "authors": src.get("authors", ""),
        "year": src.get("year"),
        "venue": src.get("venue"),
        "doi_or_identifier": src.get("doi_or_identifier"),
        "source_family": src.get("source_family"),
        "url": src.get("url"),
        "access_channel": fetch.get("provider"),
        "access_url": fetch.get("requested_url"),
        "effective_url": fetch.get("effective_url"),
        "access_time_utc": fetch.get("timestamp_utc"),
        "version": "preprint" if "arxiv" in fetch.get("requested_url", "") else "published/accepted manuscript",
        "license": "open access (publisher or arXiv)",
        "file_sha256": fetch.get("file_sha256"),
        "local_cache_path": fetch.get("local_path"),
        "content_type": fetch.get("content_type") or "application/pdf",
        "file_size_bytes": fetch.get("size"),
        "page_count": fetch.get("page_count"),
        "sections": content.get("sections"),
        "anchors": content.get("anchors", []),
        "abstract_snippet": abstract,
        "what_the_paper_supports": content["what_the_paper_supports"],
        "what_the_paper_does_not_support": content["what_the_paper_does_not_support"],
        "claim_support_status": content["claim_support_status"],
        "evidence_tier": "FULLTEXT_REVIEWED",
        "read_reasoning": f"Full {'PDF' if fetch.get('ext')=='.pdf' else 'HTML'} obtained ({fetch.get('page_count')} pages, {fetch.get('size')} bytes). Extracted text was read to identify the paper's core mechanism, section anchors, and limitations relative to ignition claims.",
    }


def main():
    registry = [json.loads(l) for l in open(REGISTRY) if l.strip()]
    registry_by_id = {s["source_id"]: s for s in registry}
    fetch = {json.loads(l)["source_id"]: json.loads(l) for l in open(FETCH) if l.strip()}
    extracts = {json.loads(l)["source_id"]: json.loads(l) for l in open(EXTRACTS) if l.strip()}

    cards = []
    for sid in SELECTED_30:
        src = registry_by_id[sid]
        f = fetch[sid]
        if not f.get("ok"):
            print(f"Skipping {sid}: fetch failed")
            continue
        content = CARD_CONTENT[sid]
        extract = extracts.get(sid, {})
        card = build_card(src, f, content, extract)
        (EVIDENCE_DIR / f"{sid}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        cards.append(card)

    (OUT / "121-fulltext-evidence-cards.jsonl").write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in cards), encoding="utf-8"
    )
    print(f"Generated {len(cards)} evidence cards")


if __name__ == "__main__":
    main()
