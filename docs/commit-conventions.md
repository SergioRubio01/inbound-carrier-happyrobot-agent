# Commit Message Conventions

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, semicolons, etc.)
- **refactor**: Code refactoring without changing functionality
- **perf**: Performance improvements
- **test**: Adding or modifying tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

## Scope (optional)

The scope should be the module or component being affected:
- `api`: API endpoints
- `database`: Database models and migrations
- `infrastructure`: Pulumi/AWS infrastructure
- `auth`: Authentication and authorization
- `loads`: Load management features
- `negotiations`: Negotiation logic
- `calls`: Call handling

## Subject

- Use imperative mood ("add" not "added" or "adds")
- Don't capitalize first letter
- No period at the end
- Max 50 characters

## Examples

### Feature
```
feat(api): add endpoint for carrier verification

Implemented POST /api/v1/carriers/verify endpoint that
validates carrier MC number against FMCSA database.

Closes #123
```

### Bug Fix
```
fix(database): resolve connection pool exhaustion

Increased max connections from 100 to 200 and added
proper connection cleanup in finally blocks.

Fixes #456
```

### Breaking Change
```
feat(api)!: change authentication to use API keys

BREAKING CHANGE: Bearer token authentication has been
replaced with API key authentication. All clients must
update their authentication headers.

Migration guide available in docs/migration/v2.md
```

### Chore
```
chore: update dependencies to latest versions

- fastapi: 0.115.0 -> 0.116.1
- sqlalchemy: 2.0.35 -> 2.0.43
- boto3: 1.35.0 -> 1.40.10
```

## Automated Changelog

Commits following these conventions will be automatically categorized in:
- CHANGELOG.md generation
- GitHub release notes
- Version bumping decisions

## Pre-commit Hook

To ensure commit messages follow conventions, you can use commitizen:

```bash
pip install commitizen
cz commit  # Interactive commit message helper
```

Or add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/commitizen-tools/commitizen
  rev: v3.13.0
  hooks:
    - id: commitizen
```
