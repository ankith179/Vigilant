# MCP reference

Start `python vigilant.py mcp` from the project directory, or pass an absolute --database URL and script path in your client configuration. Run restore_checkpoint first so saved repository paths point to this installation. No client registration files are modified automatically.

The local stdio adapter negotiates protocol 2025-11-25 and implements initialize, notifications/initialized, ping, tools/list, tools/call, prompts/list, prompts/get, resources/list, resources/templates/list and resources/read. Discovery advertises input and output schemas generated from the same Pydantic models as HTTP/CLI. Errors carry isError and no false successful structured result. Stdio emits newline-delimited JSON-RPC only.

Nine tools are enabled by default. `--allow-record-updates` exposes the tenth, update_unknown, for local evidence-record history. Tools retain local data, so their readOnlyHint is false; they never change repository contents. No HTTP MCP listener, process execution, arbitrary filesystem tool or model inference tool is exposed.

Five prompts name the five recipes. Prompt selections are rendered as untrusted data and do not execute tools by themselves. Retained resources use `vigilant://{repository}/{commit_id}/results/{result_id}`; resources/read performs the same scope, content identity and Git verification as the tool. resources/list is empty; use the template with returned identities.

Input is limited to 100,000 characters per message. Responses are bounded; request smaller pages after budget failures. Cancellation/progress notifications have no background worker to cancel; tools execute synchronously with finite traversal budgets and Git timeouts. No external client interoperability certification is claimed beyond the tested protocol contracts and subprocess smoke.

Protocol sources: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports and https://modelcontextprotocol.io/specification/2025-11-25/server/tools .
