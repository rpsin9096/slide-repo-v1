"""FocusGate v3.1 — Dynamic Adaptive Actor Persona Synthesis Tests (Loop 39).

Verifies domain-specific persona synthesis, DynamicSwarmActor tool affinity enforcement,
PersonaRegistry lifecycle management, and CLI dispatch.

100% Python stdlib, zero external dependencies.
"""

import os
import sys
import json
import unittest

from core.grid.persona_synthesizer import (
    ActorPersona,
    PersonaSynthesizer,
    DynamicSwarmActor,
    PersonaRegistry
)
from core.mesh import ActorMeshRouter, ActorMessage


class TestPersonaSynthesizer(unittest.TestCase):
    """Verifies automated persona synthesis from task descriptions and file hints."""

    def setUp(self):
        self.synth = PersonaSynthesizer()

    def test_synthesize_database_persona(self):
        persona = self.synth.synthesize("Create database migration for user accounts table and schema indexes")
        self.assertEqual(persona.domain, "database")
        self.assertIn("actor-database", persona.role_id)
        self.assertIn("schema", persona.tool_affinity)
        self.assertIn("transactional", persona.system_prompt.lower())

    def test_synthesize_security_persona(self):
        persona = self.synth.synthesize("Implement token authentication and sanitize input to avoid injection vulnerabilities")
        self.assertEqual(persona.domain, "security")
        self.assertIn("actor-security", persona.role_id)
        self.assertIn("sanitize", persona.tool_affinity)
        self.assertIn("zero-trust", persona.system_prompt.lower())

    def test_synthesize_frontend_persona(self):
        persona = self.synth.synthesize("Design responsive CSS layout and accessible HTML DOM components")
        self.assertEqual(persona.domain, "frontend")
        self.assertIn("actor-frontend", persona.role_id)
        self.assertIn("dom", persona.tool_affinity)
        self.assertIn("accessible", persona.system_prompt.lower())

    def test_synthesize_performance_persona(self):
        persona = self.synth.synthesize("Optimize CPU throughput and memory cache latency for ring buffer")
        self.assertEqual(persona.domain, "performance")
        self.assertIn("actor-performance", persona.role_id)
        self.assertIn("benchmark", persona.tool_affinity)
        self.assertIn("sub-millisecond", persona.system_prompt.lower())

    def test_synthesize_general_persona(self):
        persona = self.synth.synthesize("Clean up code structure and refactor helper utilities")
        self.assertEqual(persona.domain, "general")
        self.assertIn("actor-general", persona.role_id)


class TestDynamicSwarmActor(unittest.TestCase):
    """Verifies dynamic actor execution and tool affinity filtering."""

    def setUp(self):
        self.persona = ActorPersona(
            role_id="actor-db-tester",
            domain="database",
            description="Database specialized actor",
            system_prompt="Ensure atomic ACID operations.",
            tool_affinity=["sql_query", "schema_inspect", "migrate"],
            verification_invariants=["All queries parameterized", "Rollback on failure"]
        )
        self.actor = DynamicSwarmActor(self.persona)

    def test_actor_properties(self):
        self.assertEqual(self.actor.actor_id, "actor-db-tester")
        self.assertEqual(self.actor.persona.domain, "database")
        d = self.actor.to_dict()
        self.assertEqual(d["actor_id"], "actor-db-tester")
        self.assertEqual(d["domain"], "database")

    def test_tool_affinity_validation(self):
        self.assertTrue(self.actor.is_tool_allowed("sql_query"))
        self.assertTrue(self.actor.is_tool_allowed("schema_inspect"))
        self.assertFalse(self.actor.is_tool_allowed("destroy_all_tables"))

    def test_actor_handles_task_message(self):
        msg = ActorMessage(
            message_id="msg-1",
            source="actor-orchestrator",
            target="actor-db-tester",
            topic="EXECUTE_TASK",
            payload={"task": "Run migration 001", "tool": "migrate"}
        )
        resp = self.actor.handle_message(msg)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.topic, "TASK_COMPLETED")
        self.assertTrue(resp.payload.get("success"))


class TestPersonaRegistry(unittest.TestCase):
    """Verifies persona registration, lookup, and mesh router attachment."""

    def setUp(self):
        self.router = ActorMeshRouter()
        self.registry = PersonaRegistry(router=self.router)

    def test_register_and_route(self):
        persona = ActorPersona(
            role_id="actor-sec-01",
            domain="security",
            description="Security auditor",
            system_prompt="Audit input boundaries.",
            tool_affinity=["sanitize", "sandbox_exec"],
            verification_invariants=["Zero untrusted execution"]
        )
        actor = self.registry.register_persona(persona)
        self.assertEqual(actor.actor_id, "actor-sec-01")
        self.assertIn("actor-sec-01", self.router.actors)

        # Send message through mesh router
        msg = ActorMessage(
            message_id="msg-sec",
            source="verifier-01",
            target="actor-sec-01",
            topic="EXECUTE_TASK",
            payload={"task": "Audit buffer boundaries", "tool": "sanitize"}
        )
        delivered = self.router.send(msg)
        self.assertTrue(delivered)
        self.assertEqual(actor.mailbox.qsize(), 1)



class TestPersonaCLI(unittest.TestCase):
    """Verifies CLI flag --synthesize-persona."""

    def test_cli_synthesize_persona_json(self):
        from core.cli.dispatch import CLIDispatcher
        clean_args = ["--synthesize-persona", "Build SQL index optimizer for Postgres tables"]

        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = CLIDispatcher.dispatch_synthesize_persona(clean_args, is_json=True)

        self.assertEqual(code, 0)
        output = json.loads(stdout.getvalue())
        self.assertEqual(output.get("domain"), "database")
        self.assertIn("actor-database", output.get("role_id", ""))
