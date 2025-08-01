# PocketFlow Requirements
**Required Pattern**: Middleware AsyncNode + Role-Based Access Control
**Cookbook Reference**: pocketflow-fastapi-background
**Node Implementation**: `apps/api/src/nodes/auth/auth_middleware_node.py` (≤150 lines)
**Estimated Line Count**: 148 lines
**AsyncNode Requirements**: Yes - for JWT validation and user role checking
**Shared Store Communication**: Authentication context patterns
