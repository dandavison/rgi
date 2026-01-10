"""
Shell script templates for rgi.

This module contains the bash script fragments used by rgi for:
- Glob expansion with exclusion pattern filtering
- Command reload transforms
- Tab completion
- Cursor positioning

These are separated from the main rgi logic to make the application
code cleaner and to allow independent testing of the scripts.
"""

from __future__ import annotations


def oneline(script: str) -> str:
    """Convert a multiline shell script to a single line.

    Args:
        script: A multiline bash script

    Returns:
        The script collapsed to a single line
    """
    return " ".join(script.split())


# =============================================================================
# Script Templates
# =============================================================================

# Path prefix glob expansion
# Expands last word with glob if it doesn't exist as-is
# Filters matches against exclusion patterns from pinned_opts and cmd
# NOTE: No bash comments - becomes a one-liner where # breaks things
GLOB_EXPAND = """
    if [[ ! "$cmd" =~ [[:space:]]$ ]]; then
        last="${cmd##* }";
        if [[ "$last" != -* && ! -e "$last" && -n "$last" ]]; then
            shopt -s nullglob;
            matches=( ${last}* );
            shopt -u nullglob;
            if [[ ${#matches[@]} -gt 0 ]]; then
                all_opts="$pinned_opts $cmd";
                if echo "$all_opts" | grep -qE "'![^']*'"; then
                    filtered=();
                    for m in "${matches[@]}"; do
                        excluded=false;
                        while IFS= read -r pattern; do
                            if [[ -n "$pattern" && "$(basename "$m")" == $pattern ]]; then
                                excluded=true;
                                break;
                            fi;
                        done < <(echo "$all_opts" | grep -oE "'![^']*'" | sed "s/^'!//;s/'$//");
                        if [[ "$excluded" == false ]]; then
                            filtered+=("$m");
                        fi;
                    done;
                    matches=("${filtered[@]}");
                fi;
                if [[ ${#matches[@]} -gt 0 ]]; then
                    cmd="${cmd% *} ${matches[*]}";
                fi;
            fi;
        fi;
    fi;
"""

# Mode-aware reload transform
# Reads state from RGI_STATE_FILE to determine if pinned opts should be prepended
RELOAD_TRANSFORM = """
    state_file="$RGI_STATE_FILE";
    pinned_opts="";
    if [[ -f "$state_file" ]]; then
        state=$(cat "$state_file");
        mode="${{state%%|*}}";
        if [[ "$mode" == "pinned" ]]; then
            pinned_opts="${{state#*|}}";
        fi;
    fi;
    cmd="$FZF_QUERY";
    {glob_expand}
    if [[ "$cmd" =~ ^rg ]]; then
        cmd="${{cmd#rg}}";
        if [[ -n "$pinned_opts" ]]; then
            cmd="rg $pinned_opts {implicit_opts}$cmd";
        else
            cmd="rg {implicit_opts}$cmd";
        fi;
    fi;
    printf 'reload:RIPGREP_CONFIG_PATH= eval %q 2>/dev/null | {delta}' "$cmd"
"""

# Start reload for pinned mode (config_args prepended)
START_RELOAD_PINNED = """
    pinned_opts="{config_args}";
    cmd={{q}};
    {glob_expand}
    if [[ "$cmd" =~ ^rg ]]; then
        cmd="${{cmd#rg}}";
        cmd="rg {config_args} {implicit_opts}$cmd";
    fi;
    RIPGREP_CONFIG_PATH= eval "$cmd" 2>/dev/null | {delta}
"""

# Start reload for inline mode (no config_args)
START_RELOAD_INLINE = """
    pinned_opts="";
    cmd={{q}};
    {glob_expand}
    if [[ "$cmd" =~ ^rg ]]; then
        cmd="${{cmd#rg}}";
        cmd="rg {implicit_opts}$cmd";
    fi;
    RIPGREP_CONFIG_PATH= eval "$cmd" 2>/dev/null | {delta}
"""

# Tab completion for paths
# Single match: complete fully, add / for directories
# Multiple matches: complete to longest common prefix
TAB_COMPLETE = r"""
    q="$FZF_QUERY";
    last="${q##* }";
    [[ "$last" == -* || -z "$last" ]] && { echo "$q"; exit; };
    IFS=$'\n' read -d '' -ra matches < <(compgen -f -- "$last" 2>/dev/null; printf '\0');
    if [[ ${#matches[@]} -eq 1 ]]; then
        m="${matches[0]}";
        [[ -d "$m" ]] && m="$m/";
        echo "${q% *} $m";
    elif [[ ${#matches[@]} -gt 1 ]]; then
        pfx="${matches[0]}";
        for m in "${matches[@]}"; do
            while [[ "${m:0:${#pfx}}" != "$pfx" && -n "$pfx" ]]; do
                pfx="${pfx:0:-1}";
            done;
        done;
        [[ "$pfx" != "$last" ]] && echo "${q% *} $pfx" || echo "$q";
    else
        echo "$q";
    fi
"""

# Cursor positioning on startup (only if user hasn't typed)
CURSOR_POSITION = (
    '[[ "$FZF_QUERY" == "rg " ]] && '
    'echo "change-query(rg  .)+backward-char+backward-char+unbind(result)" || '
    'echo "unbind(result)"'
)


def build_reload_transform(
    implicit_opts: str,
    delta: str,
) -> str:
    """Build the reload transform script.

    Args:
        implicit_opts: Implicit rg options (e.g., "--json")
        delta: Delta command for output formatting

    Returns:
        One-line shell script for fzf transform
    """
    glob_expand = oneline(GLOB_EXPAND)
    return oneline(
        RELOAD_TRANSFORM.format(
            glob_expand=glob_expand,
            implicit_opts=implicit_opts,
            delta=delta,
        )
    )


def build_start_reload_pinned(
    config_args: str,
    implicit_opts: str,
    delta: str,
) -> str:
    """Build the start reload script for pinned mode.

    Args:
        config_args: Config arguments from RIPGREP_CONFIG_PATH
        implicit_opts: Implicit rg options (e.g., "--json")
        delta: Delta command for output formatting

    Returns:
        One-line shell script for fzf start binding
    """
    glob_expand = oneline(GLOB_EXPAND)
    return oneline(
        START_RELOAD_PINNED.format(
            glob_expand=glob_expand,
            config_args=config_args,
            implicit_opts=implicit_opts,
            delta=delta,
        )
    )


def build_start_reload_inline(
    implicit_opts: str,
    delta: str,
) -> str:
    """Build the start reload script for inline mode.

    Args:
        implicit_opts: Implicit rg options (e.g., "--json")
        delta: Delta command for output formatting

    Returns:
        One-line shell script for fzf start binding
    """
    glob_expand = oneline(GLOB_EXPAND)
    return oneline(
        START_RELOAD_INLINE.format(
            glob_expand=glob_expand,
            implicit_opts=implicit_opts,
            delta=delta,
        )
    )


def build_tab_complete() -> str:
    """Build the tab completion script.

    Returns:
        One-line shell script for tab completion transform
    """
    return oneline(TAB_COMPLETE)
