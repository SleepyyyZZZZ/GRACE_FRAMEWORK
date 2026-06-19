---
name: context7-auto-research
description: Automatically fetch up-to-date library/framework documentation via Context7 MCP. Auto-triggers when you need docs for React, Next.js, Vue, Svelte, TypeScript, Python libraries, and 100+ other frameworks.
---

# Context7 Auto-Research

Automatically provides up-to-date, version-specific documentation for libraries and frameworks through Context7 MCP integration.

## When This Activates

This skill automatically triggers when you:
- Write code using external libraries (React, Next.js, Vue, Svelte, etc.)
- Ask questions about library APIs or features
- Need documentation for frameworks or tools
- Request code examples with specific packages
- Set up or configure frameworks
- Encounter library-related errors

## How It Works

When activated, the skill:
1. Detects which library/framework you're working with
2. Uses Context7 MCP to fetch the latest documentation
3. Provides version-specific code examples and API references
4. Ensures you get accurate, non-hallucinated information

## Supported Libraries

Context7 supports 100+ popular libraries including:
- **Frontend**: React, Next.js, Vue, Svelte, Angular, Solid
- **Backend**: Express, Fastify, NestJS, Django, Flask
- **Databases**: Prisma, Drizzle, Supabase, MongoDB
- **Tools**: TypeScript, Vite, Vitest, Jest, Playwright
- And many more...

## Usage Examples

Simply work naturally - the skill activates automatically:

```
User: "How do I use server actions in Next.js 15?"
→ Context7 fetches latest Next.js 15 docs

User: "Show me Prisma migration commands"
→ Context7 retrieves current Prisma CLI docs

User: "Create a React component with hooks"
→ Context7 ensures latest React patterns
```

## Installation Requirements

**Prerequisites**: Context7 MCP server must be installed first.

Install MCP server:
```bash
# With API key (recommended for higher limits)
claude mcp add context7 -- npx -y @upstash/context7-mcp --api-key YOUR_API_KEY

# Without API key (free tier)
claude mcp add context7 -- npx -y @upstash/context7-mcp
```

Get your free API key at: https://context7.com/dashboard

## Configuration

No additional configuration needed! Once the MCP server is installed, this skill works automatically.

For manual Context7 queries, you can also use:
- "use context7" in your prompts
- Ask directly: "Get Context7 docs for [library]"

## Benefits

✅ Always up-to-date documentation
✅ Version-specific code examples
✅ Prevents API hallucinations
✅ Automatic activation - no manual commands
✅ Token-efficient - only loads when needed
✅ Supports 100+ libraries and frameworks

## Troubleshooting

**Skill not activating?**
- Ensure Context7 MCP server is installed: `claude mcp list`
- Check API key is configured correctly
- Verify you're asking about supported libraries

**Rate limit errors?**
- Get a free API key at context7.com/dashboard
- Free tier has generous limits for personal use

## Related Resources

- Context7 Website: https://context7.com
- GitHub: https://github.com/upstash/context7
- Documentation: https://context7.com/docs/overview
- Supported Libraries: https://context7.com/libraries

## Related Skills

- `react-best-practices` - React optimization patterns
- `ui-ux-pro-max` - UI/UX design guidelines
- `react-native-design` - Mobile app development
