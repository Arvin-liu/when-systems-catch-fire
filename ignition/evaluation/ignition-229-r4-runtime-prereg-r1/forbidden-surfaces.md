# Forbidden runtime surfaces

The worker has no model-facing tools. Its request has exactly `tools: []` and `tool_choice: "none"`. The only model input is the fixed prompt/schema/unit-input assembly. The only network request is a direct HTTPS POST to `api.openai.com:443/v1/responses`; the worker follows no redirects and has no proxy or retry behavior.

Do not supply or enable shell, MCP, browser, computer-use, local file, filesystem, search, retrieval, remote function, custom tool, code interpreter, or agent-loop capabilities. Do not attach a conversation, prior response ID, prompt cache key, prior output, another unit, matrix, expected digest, outcome threshold, receipt, evaluator source/result, target answer, score, or label.

The process receives only one frozen unit JSON record and exact frozen prompt/schema file bytes. Use a separate temporary capture directory per request. Do not persist session history. The API key is environment-only and must not be printed, captured in logs, or copied into receipts.

Any unexpected tool-related output or tool call fails closed, is captured as a non-pass, consumes the single attempt, and stops subsequent units. No R4 unit or evaluator is run by this R1 task.
