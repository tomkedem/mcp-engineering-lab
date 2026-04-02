# Why MCP

## The Problem

Direct model-to-tool connections do not scale.
Every new connection is a new integration with its own format,
authentication, error handling, and security assumptions.
The result is spaghetti code that no one dares to touch.

N models × M tools = N×M integrations to build, test, and maintain.

## The Solution

MCP introduces a single coordination layer.
Every model speaks to the layer.
Every tool exposes itself through the layer.

N×M becomes N+M.

## When MCP Makes Sense

- More than one model needs access to the same tools
- More than one tool needs to serve different models
- The system needs to grow over time
- There are security, permissions, or audit requirements
- Different teams own different parts of the system

## When MCP Is Overkill

- One model, one tool, no plans to expand
- A prototype built to validate an idea
- No security or long-term maintenance requirements
