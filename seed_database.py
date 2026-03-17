#!/usr/bin/env python3
"""
Seed database with TM/TrendAI relevant data.
Run once after first setup.

Usage:
  python seed_database.py
"""

import sqlite3
from pathlib import Path


DB_PATH = Path.home() / "Documents" / "Work" / ".claude-mcp" / "memory.db"


def seed():
    db = sqlite3.connect(DB_PATH)

    # ============ ENTITIES ============
    entities = [
        # Products
        ("Vision One", "product", "Trend Micro XDR platform. Central console for all TM products."),
        ("Apex One", "product", "Endpoint security. On-prem and SaaS versions."),
        ("Deep Security", "product", "Server/workload protection. On-prem, being replaced by Cloud One."),
        ("Cloud One", "product", "Cloud security platform: Workload Security, Container Security, File Storage Security, Conformity, Network Security."),
        ("Cloud One File Storage Security", "product", "Scans S3/Azure Blob/GCP Storage. Legacy, migrating to Vision One."),
        ("Vision One File Security", "product", "Current generation file scanning for cloud storage. EventBridge-based."),
        ("Vision One Sandbox", "product", "File/URL sandbox analysis. API: POST /v3.0/sandbox/files/analyze"),
        ("Deep Discovery Analyzer", "product", "On-prem sandbox appliance."),
        ("TrendAI", "product", "Trend Micro AI brand. Used in Vision One and marketing."),
        ("IMSVA", "product", "InterScan Messaging Security Virtual Appliance. Email gateway."),
        ("DDEI", "product", "Deep Discovery Email Inspector. Email sandbox/APT detection."),
        ("Apex Central", "product", "Central management for Apex One and other endpoints."),
        ("TippingPoint", "product", "Network IPS. Hardware appliances."),

        # Internal tools
        ("TrendGPT", "tool", "Internal LLM for TM product knowledge. MCP server available."),
        ("TM Knowledge MCP", "tool", "MCP server for KB, Online Help, Automation Center, Threat Encyclopedia."),

        # APIs
        ("Vision One API", "api", "REST API v3.0. Base: api.xdr.trendmicro.com. Auth: Bearer token."),
        ("Cloud One API", "api", "REST API. Base: cloudone.trendmicro.com/api. Auth: API key."),

        # Concepts
        ("XDR", "concept", "Extended Detection and Response. Cross-layer threat correlation."),
        ("EDR", "concept", "Endpoint Detection and Response. Vision One Endpoint Security."),
        ("ASRM", "concept", "Attack Surface Risk Management. Vision One feature."),
        ("Workbench", "concept", "Vision One investigation console. Shows alerts, incidents."),
        ("Response Actions", "concept", "Vision One automated/manual response: isolate, collect, block."),
    ]

    for name, etype, desc in entities:
        try:
            db.execute(
                "INSERT INTO entities (name, type, description) VALUES (?, ?, ?)",
                (name, etype, desc)
            )
        except sqlite3.IntegrityError:
            pass  # Already exists

    # ============ DECISIONS ============
    decisions = [
        ("File Security product choice",
         "Use Vision One File Security for new deployments, not Cloud One FSS",
         "Vision One is strategic platform. Cloud One FSS is legacy. Same engine, better XDR integration."),

        ("Sandbox integration",
         "Vision One Sandbox API for async file analysis",
         "No built-in sandbox in File Security. Use separate API: POST /v3.0/sandbox/files/analyze"),

        ("IMSVA migration path",
         "Migrate to Cloud Email Gateway Security or DDEI depending on requirements",
         "IMSVA is legacy. Cloud Email Gateway for basic, DDEI for APT/sandbox needs."),
    ]

    for topic, decision, reasoning in decisions:
        db.execute(
            "INSERT INTO decisions (topic, decision, reasoning, status) VALUES (?, ?, ?, 'active')",
            (topic, decision, reasoning)
        )

    # ============ MEMORY ============
    memories = [
        # API patterns
        ("Vision One API auth: Bearer token in Authorization header. Get token from Vision One console > API Keys.", 2.0),
        ("Cloud One API auth: API key in Authorization header. Format: ApiVersion + ApiKey.", 2.0),
        ("Vision One Sandbox quota: check TMV1-Submission-Remaining-Count header in response.", 1.5),

        # Architecture patterns
        ("S3 file scanning pattern: S3 event → EventBridge → Lambda → File Security API → move to clean bucket.", 2.0),
        ("Sandbox async pattern: submit file → get task ID → poll /sandbox/tasks/{id} → get verdict.", 2.0),

        # Common issues
        ("Vision One API error 401: token expired or invalid. Regenerate in console.", 1.5),
        ("Cloud One FSS deployment: CloudFormation templates. All-in-one or separate scanner/storage stacks.", 1.5),

        # URLs
        ("Vision One API endpoints: US api.xdr.trendmicro.com, EU api.eu.xdr.trendmicro.com, SG api.sg.xdr.trendmicro.com", 1.0),
        ("Automation Center docs: automation.trendmicro.com/xdr/api-v3 for Vision One API reference.", 1.0),
        ("KB search: success.trendmicro.com for knowledge base articles.", 1.0),
    ]

    for content, weight in memories:
        db.execute(
            "INSERT INTO memory (content, weight, source) VALUES (?, ?, 'seed')",
            (content, weight)
        )

    # ============ PROJECTS ============
    projects = [
        ("Vision One integrations", "Customer integrations with Vision One API", "active"),
        ("Cloud One migrations", "Migrating customers from legacy to Cloud One/Vision One", "active"),
        ("MCP servers", "Claude Code MCP server development for TM tools", "active"),
    ]

    for name, desc, status in projects:
        try:
            db.execute(
                "INSERT INTO projects (name, description, status) VALUES (?, ?, ?)",
                (name, desc, status)
            )
        except sqlite3.IntegrityError:
            pass

    # ============ QUESTIONS ============
    questions = [
        ("What is the migration path from Deep Security to Cloud One Workload Security?", "products"),
        ("How to integrate Vision One with SIEM (Splunk, QRadar)?", "integrations"),
        ("What file types does Vision One Sandbox support?", "products"),
    ]

    for question, domain in questions:
        db.execute(
            "INSERT INTO questions (question, domain, status) VALUES (?, ?, 'open')",
            (question, domain)
        )

    db.commit()
    db.close()
    print(f"Database seeded: {DB_PATH}")


if __name__ == "__main__":
    seed()
