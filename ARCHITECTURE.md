# rgi Architecture

## Overview

rgi is an interactive ripgrep wrapper built on fzf. The user edits an `rg` command in fzf's query line, and results update live.

## Key Concepts

### transform vs reload

fzf has two related but different actions:

- **`reload:COMMAND`** - Runs COMMAND, uses its stdout as the new item list
- **`transform:COMMAND`** - Runs COMMAND, interprets its stdout as *fzf actions to execute*

rgi uses both:

```
User types → change event → transform:SCRIPT → outputs "reload:rg ..." → reload runs rg
```

Why the indirection? The transform script can:
1. Read state (pinned mode, config options)
2. Do glob expansion on paths
3. Construct the full rg command dynamically

A direct `reload:` couldn't do this complex preprocessing.

### Pinned vs Inline Mode

- **Pinned mode**: Config options shown in footer, applied implicitly to every search
- **Inline mode**: All options in the query line, footer empty

Toggle with `ctrl-]`. State stored in `/tmp/rgi-pinned-{pid}.state`.

## Files

```
src/rgi/scripts/
├── rgi                 # Main script - builds fzf command
├── rgi-preview         # Preview script - runs bat on selected file
├── rgi-toggle-pinned   # Handles ctrl-\ toggle between modes
└── open-in-editor      # Opens file:line in configured editor
```

## Event Flow

```
┌─────────────────────────────────────────────────────────────┐
│ fzf                                                         │
│                                                             │
│  Query: [rg pattern path]                                   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ change event │───▶│  transform   │───▶│    reload    │   │
│  │ (keystroke)  │    │ (build cmd)  │    │  (run rg)    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                              │                    │         │
│                              ▼                    ▼         │
│                       Read state file      rg | delta       │
│                       Glob expansion       (stdout = list)  │
│                       Output: reload:...                    │
│                                                             │
│  Results: [file:line: matching content...]                  │
│                                                             │
│  Preview: bat showing file context                          │
│                                                             │
│  Footer: [-g '!*.test.go' -g '!*.mock.go' ...]              │
└─────────────────────────────────────────────────────────────┘
```

## Key Bindings

| Key | Action |
|-----|--------|
| `enter` | Open file in editor at line |
| `ctrl-\` | Toggle pinned/inline mode |
| `tab` | Path completion |
| `alt-up/down` | History navigation |

## Output Pipeline

```
rg --json ... | delta --grep-output-type classic
```

- `--json`: rg outputs JSON for delta to parse
- delta: Syntax highlighting and formatting

