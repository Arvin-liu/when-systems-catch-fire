"""N7 Cross-Node Composition — integration surface between N1→N2→N3→N4→N5→N6→N9.

Defines the canonical pipeline and validates inter-node data flow.
"""
import json, hashlib
from typing import Dict, Any

class CrossNodePipeline:
    """Canonical Function OS v0.1 pipeline."""
    VERSION = "0.1.0"

    def __init__(self, parser, checker, compiler, interpreter, packager,
                 feedback_loop, val_feedback, registry_store):
        self.parser = parser
        self.checker = checker
        self.compiler = compiler
        self.interpreter = interpreter
        self.packager = packager
        self.feedback_loop = feedback_loop
        self.val_feedback = val_feedback
        self.registry = registry_store

    def full_cycle(self, spec_json: str, test_inputs: dict) -> Dict[str, Any]:
        """Run the complete N1→N2→N3→N4→N5→N6→N9 cycle."""
        log = []

        # N1: Parse
        try:
            spec = self.parser.parse(spec_json)
            log.append({"node": "N1", "action": "parse", "status": "ok"})
        except Exception as e:
            log.append({"node": "N1", "action": "parse", "status": "error", "detail": str(e)})
            return {"ok": False, "error": "PARSE_ERROR", "detail": str(e), "log": log}

        # N1: Semantic check
        issues = self.checker.check(spec)
        if not issues:
            log.append({"node": "N1", "action": "semantic_check", "status": "ok"})
        else:
            semantic_fb = self.feedback_loop.analyze_semantic_issues(issues, spec)
            log.append({"node": "N1", "action": "semantic_check", "status": "issues",
                        "issue_count": len(issues)})
            if any(i.get("severity") == "ERROR" for i in issues):
                return {"ok": False, "error": "SEMANTIC_ERROR", "feedback": semantic_fb.get_revision_guide(), "log": log}

        # N2: Compile
        compile_result = self.compiler.compile(spec)
        if not compile_result.get("ok"):
            compile_fb = self.feedback_loop.analyze_compile_error(compile_result, spec)
            log.append({"node": "N2", "action": "compile", "status": "error",
                        "detail": compile_result.get("error")})
            return {"ok": False, "error": "COMPILE_ERROR",
                    "feedback": compile_fb.get_revision_guide(), "log": log}
        compiled = compile_result["compiled"]
        log.append({"node": "N2", "action": "compile", "status": "ok"})

        # N3: Interpret
        result = self.interpreter.execute(compiled, test_inputs)
        if not result.get("ok"):
            interpret_fb = self.feedback_loop.analyze_interpret_error(result, compiled)
            log.append({"node": "N3", "action": "interpret", "status": "error",
                        "detail": result.get("error")})
            return {"ok": False, "error": "INTERPRET_ERROR",
                    "feedback": interpret_fb.get_revision_guide(), "log": log}
        log.append({"node": "N3", "action": "interpret", "status": "ok",
                     "outputs": result.get("outputs")})

        # N4: Package
        artifact_result = self.packager.package(spec, compiled)
        if not artifact_result.get("ok"):
            log.append({"node": "N4", "action": "package", "status": "error"})
            return {"ok": False, "error": "PACKAGE_ERROR", "log": log}
        artifact = artifact_result["artifact"]
        log.append({"node": "N4", "action": "package", "status": "ok",
                    "artifact_id": artifact_result["artifact_id"]})

        # N4: Verify
        verify_result = self.packager.verify(artifact)
        if not verify_result.get("ok"):
            log.append({"node": "N4", "action": "verify", "status": "fail",
                        "results": verify_result.get("results")})
            return {"ok": False, "error": "VERIFY_ERROR", "log": log}
        log.append({"node": "N4", "action": "verify", "status": "ok"})

        # N6: Validation feedback
        val_fb = self.val_feedback.produce(result, compiled, spec)
        log.append({"node": "N6", "action": "validate", "status": "ok",
                    "recommendation": val_fb["recommendation"]})

        # N9: Register
        manifest = artifact["manifest"]
        ch = self.registry._compute_hash(
            spec["function_id"], spec["spec_hash"],
            manifest.get("artifact_hash", ""), "1"
        )
        record = {
            "function_id": spec["function_id"],
            "revision": 1,
            "spec_hash": spec["spec_hash"],
            "artifact_hash": manifest.get("artifact_hash", ""),
            "compiler_version": self.compiler.VERSION,
            "status": "active",
            "created_at": spec.get("created_at", "2026-07-15T02:20:00Z"),
            "content_hash": ch,
            "spec": {k: spec[k] for k in ["function_id","spec_version","name","inputs","outputs","preconditions","postconditions","effects_declared"] if k in spec},
            "artifact": manifest
        }
        reg_result = self.registry.create(record)
        if not reg_result.get("ok"):
            log.append({"node": "N9", "action": "register", "status": "error",
                        "detail": reg_result})
            return {"ok": False, "error": "REGISTER_ERROR", "detail": reg_result, "log": log}
        log.append({"node": "N9", "action": "register", "status": "ok",
                    "revision": reg_result.get("revision")})

        return {
            "ok": True,
            "outputs": result.get("outputs"),
            "artifact_id": artifact_result["artifact_id"],
            "spec_hash": spec["spec_hash"],
            "n6_recommendation": val_fb["recommendation"],
            "log": log
        }
