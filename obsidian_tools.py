import os
import re
from langchain_core.tools import tool

# =====================================================================
# Helper Functions
# =====================================================================

WIKI_LINK_REGEX = re.compile(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]')

def _get_vault_path() -> str:
    """Helper to retrieve active vault path, defaulting to ./obsidian_vault."""
    path = os.getenv("OBSIDIAN_VAULT_PATH")
    if not path:
        path = os.path.abspath(os.path.join(os.getcwd(), "obsidian_vault"))
    else:
        path = os.path.abspath(path)
    # Ensure directory exists
    os.makedirs(path, exist_ok=True)
    return path

def _update_env_vault_path(vault_path: str):
    """Updates the .env file with the active OBSIDIAN_VAULT_PATH."""
    env_path = os.path.abspath(os.path.join(os.getcwd(), ".env"))
    lines = []
    updated = False
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if line.strip().startswith("OBSIDIAN_VAULT_PATH="):
                lines[i] = f"OBSIDIAN_VAULT_PATH={vault_path}\n"
                updated = True
                break
                
    if not updated:
        lines.append(f"\nOBSIDIAN_VAULT_PATH={vault_path}\n")
        
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        
    # Update environment variable in current process too
    os.environ["OBSIDIAN_VAULT_PATH"] = vault_path

def get_note_mapping(vault_path: str) -> dict[str, str]:
    """Maps lowercase note title to absolute file path."""
    mapping = {}
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                name_without_ext = os.path.splitext(file)[0]
                # Map case-insensitively
                mapping[name_without_ext.lower()] = os.path.join(root, file)
    return mapping

def parse_tags_from_file(content: str) -> list[str]:
    """Parses Obsidian tags from YAML frontmatter and inline hashtags."""
    tags = []
    
    # 1. Match YAML frontmatter at the very start of the file
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        frontmatter = match.group(1)
        # Find tags in list format:
        # tags:
        #   - tag1
        #   - tag2
        tags_section = re.search(r'tags:\s*\n((?:\s*-\s*\S+\s*\n?)+)', frontmatter)
        if tags_section:
            tag_lines = tags_section.group(1).split('\n')
            for line in tag_lines:
                m = re.match(r'^\s*-\s*(\S+)', line)
                if m:
                    tags.append(m.group(1).lstrip('#'))
        
        # Support single-line array tags: tags: [tag1, tag2]
        array_match = re.search(r'tags:\s*\[(.*?)\]', frontmatter)
        if array_match:
            tags.extend([t.strip().lstrip('#') for t in array_match.group(1).split(',') if t.strip()])
            
    # 2. Find inline hashtags: #tag-name (excluding Markdown headers like # Header)
    inline_tags = re.findall(r'(?<!\S)#([a-zA-Z0-9_\-/]+)', content)
    for t in inline_tags:
        if t and not t[0].isdigit():
            tags.append(t)
            
    return list(set(tags))

def parse_links(content: str) -> list[str]:
    """Extracts all wiki-link targets from note content."""
    matches = WIKI_LINK_REGEX.findall(content)
    return list(set(m.strip() for m in matches))

def add_link_to_file(file_path: str, target_title: str, link_text: str = None) -> bool:
    """Inserts a wiki-link to the target note in the source note file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    link_str = f"[[{target_title}|{link_text}]]" if link_text else f"[[{target_title}]]"
    
    # Check if this link is already present to prevent duplicate links
    escaped_target = re.escape(target_title)
    existing_pattern = re.compile(rf'\[\[{escaped_target}(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]', re.IGNORECASE)
    if existing_pattern.search(content):
        return False
        
    # Search for an existing Connections/Links/Related section
    sections = [r'## Connections', r'## Links', r'## Related']
    found_section = None
    for sec in sections:
        sec_pattern = re.compile(rf'^{sec}\s*$', re.MULTILINE | re.IGNORECASE)
        if sec_pattern.search(content):
            found_section = sec
            break
            
    if found_section:
        # Append connection to that section
        sec_pattern = re.compile(rf'^({found_section})\s*$', re.MULTILINE | re.IGNORECASE)
        match = sec_pattern.search(content)
        start_idx = match.end()
        # Find next header or end of file
        next_header = re.search(r'\n#[#\s]', content[start_idx:])
        end_idx = start_idx + next_header.start() if next_header else len(content)
        
        section_content = content[start_idx:end_idx].rstrip()
        new_section_content = section_content + f"\n- {link_str}"
        content = content[:start_idx] + new_section_content + "\n" + content[end_idx:]
    else:
        # Append a new ## Connections section at the end
        if not content.endswith('\n'):
            content += '\n'
        content += f"\n## Connections\n- {link_str}\n"
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

# =====================================================================
# Tools Definitions
# =====================================================================

@tool
def obsidian_set_vault(vault_path: str) -> str:
    """Configure and set the active Obsidian vault directory path.
    
    Creates the directory if it does not exist, and saves the setting
    to the workspace configuration (.env) for persistence.
    
    Args:
        vault_path (str): The directory path of the Obsidian vault.
        
    Returns:
        str: Success confirmation and absolute path, or error.
    """
    try:
        abs_path = os.path.abspath(vault_path)
        os.makedirs(abs_path, exist_ok=True)
        _update_env_vault_path(abs_path)
        return f"Successfully set active Obsidian vault to: {abs_path}"
    except Exception as e:
        return f"Error setting vault path: {str(e)}"

@tool
def obsidian_get_vault() -> str:
    """Retrieve the absolute directory path of the currently active Obsidian vault.
    
    Returns:
        str: Absolute path of the active Obsidian vault.
    """
    try:
        return f"Current active Obsidian vault path: {_get_vault_path()}"
    except Exception as e:
        return f"Error retrieving vault path: {str(e)}"

@tool
def obsidian_create_note(title: str, content: str = "", folder: str = "", tags: list[str] = None, links: list[str] = None) -> str:
    """Create a new note (node) in the active Obsidian vault with optional frontmatter tags and links.
    
    Args:
        title (str): Title of the note (matches filename without .md).
        content (str, optional): The main text content of the note. Defaults to "".
        folder (str, optional): A subdirectory path relative to the vault root. Defaults to "".
        tags (list[str], optional): List of tags to add to the note. Defaults to None.
        links (list[str], optional): List of other note titles to link to. Defaults to None.
        
    Returns:
        str: Success message with filepath, or error.
    """
    try:
        vault_path = _get_vault_path()
        # Clean title to avoid filesystem issues
        safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
        if not safe_title:
            return "Error: Note title must contain valid characters."
            
        note_folder = os.path.join(vault_path, folder) if folder else vault_path
        os.makedirs(note_folder, exist_ok=True)
        
        note_path = os.path.join(note_folder, f"{safe_title}.md")
        
        # Build YAML frontmatter for tags
        frontmatter = ""
        if tags:
            frontmatter = "---\ntags:\n" + "\n".join(f"  - {t.lstrip('#')}" for t in tags) + "\n---\n\n"
            
        full_content = frontmatter + content
        
        # Append connections section if links are provided
        if links:
            if not full_content.endswith('\n'):
                full_content += '\n'
            full_content += "\n## Connections\n" + "\n".join(f"- [[{l}]]" for l in links) + "\n"
            
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        return f"Successfully created note '{safe_title}' at: {os.path.abspath(note_path)}"
    except Exception as e:
        return f"Error creating note: {str(e)}"

@tool
def obsidian_connect_notes(source: str, target: str, link_text: str = None, bidirectional: bool = False) -> str:
    """Connect two notes together by inserting a wiki-link from the source note to the target note.
    
    If the target note does not exist, a blank note is automatically created at the vault root.
    
    Args:
        source (str): Title of the source note.
        target (str): Title of the target note.
        link_text (str, optional): Custom alias/display text for the wiki-link. Defaults to None.
        bidirectional (bool, optional): If True, links back from target to source as well. Defaults to False.
        
    Returns:
        str: Status message detailing the connection results.
    """
    try:
        vault_path = _get_vault_path()
        mapping = get_note_mapping(vault_path)
        
        source_key = source.strip().lower()
        target_key = target.strip().lower()
        
        # Find source note
        if source_key in mapping:
            source_path = mapping[source_key]
        else:
            return f"Error: Source note '{source}' not found in vault."
            
        # Find or create target note
        if target_key in mapping:
            target_path = mapping[target_key]
            actual_target_title = os.path.splitext(os.path.basename(target_path))[0]
        else:
            # Create target note stub
            safe_target = "".join(c for c in target if c not in r'\/:*?"<>|').strip()
            target_path = os.path.join(vault_path, f"{safe_target}.md")
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(f"---\ntags:\n  - auto-created\n---\n\n# {safe_target}\n\nAuto-created stub note.\n")
            actual_target_title = safe_target
            # Refresh mapping since we created a new file
            mapping = get_note_mapping(vault_path)
            
        # Add link from source to target
        source_title = os.path.splitext(os.path.basename(source_path))[0]
        added_to_source = add_link_to_file(source_path, actual_target_title, link_text)
        
        msg = f"Connected '{source_title}' -> '{actual_target_title}'" if added_to_source else f"Link from '{source_title}' to '{actual_target_title}' already exists."
        
        if bidirectional:
            added_to_target = add_link_to_file(target_path, source_title)
            if added_to_target:
                msg += f" and bidirectional link '{actual_target_title}' -> '{source_title}' created."
            else:
                msg += f" (Bidirectional link already existed)."
                
        return msg
    except Exception as e:
        return f"Error connecting notes: {str(e)}"

@tool
def obsidian_get_connections(title: str) -> str:
    """Retrieve all outgoing links and incoming backlinks for a specific note.
    
    Args:
        title (str): Title of the note.
        
    Returns:
        str: Formatted text summarizing incoming and outgoing connections.
    """
    try:
        vault_path = _get_vault_path()
        mapping = get_note_mapping(vault_path)
        
        note_key = title.strip().lower()
        if note_key not in mapping:
            return f"Error: Note '{title}' not found in vault."
            
        note_path = mapping[note_key]
        actual_title = os.path.splitext(os.path.basename(note_path))[0]
        
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find outgoing links
        outgoing_raw = parse_links(content)
        
        # Resolve outgoing links to check if they exist
        outgoing_status = []
        for out in outgoing_raw:
            if out.lower() in mapping:
                outgoing_status.append(f"• [[{out}]] (exists)")
            else:
                outgoing_status.append(f"• [[{out}]] (missing/stub)")
                
        # Find incoming links (backlinks) by walking the vault
        incoming = []
        for other_title, other_path in mapping.items():
            if other_title == note_key:
                continue
            try:
                with open(other_path, 'r', encoding='utf-8') as f:
                    other_content = f.read()
                other_links = parse_links(other_content)
                if any(ol.lower() == note_key for ol in other_links):
                    other_actual_title = os.path.splitext(os.path.basename(other_path))[0]
                    incoming.append(f"• [[{other_actual_title}]]")
            except Exception:
                pass
                
        report = [
            f"Connections report for: **{actual_title}**",
            f"Path: {os.path.abspath(note_path)}",
            "\nOutgoing Links (Connections from this note):",
            "\n".join(outgoing_status) if outgoing_status else "  (None)",
            "\nIncoming Backlinks (Connections to this note):",
            "\n".join(incoming) if incoming else "  (None)"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"Error retrieving connections: {str(e)}"

@tool
def obsidian_get_vault_stats() -> str:
    """Analyze the active Obsidian vault and return structural statistics.
    
    Includes total notes count, total connections count, tag frequencies,
    orphan nodes (notes with no connections), and highly connected hub notes.
    
    Returns:
        str: Formatted markdown statistics report of the vault.
    """
    try:
        vault_path = _get_vault_path()
        mapping = get_note_mapping(vault_path)
        
        if not mapping:
            return f"The vault at '{vault_path}' is empty or contains no markdown notes."
            
        # Parse all notes
        outgoing_edges = {}
        incoming_edges = {title: [] for title in mapping.keys()}
        tag_counts = {}
        
        for note_key, file_path in mapping.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Tags
                tags = parse_tags_from_file(content)
                for t in tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
                    
                # Outgoing links
                out_links = parse_links(content)
                actual_out_links = []
                for ol in out_links:
                    ol_key = ol.lower()
                    actual_out_links.append(ol)
                    if ol_key in mapping:
                        incoming_edges[ol_key].append(note_key)
                
                actual_name = os.path.splitext(os.path.basename(file_path))[0]
                outgoing_edges[note_key] = (actual_name, actual_out_links)
            except Exception:
                pass
                
        # Calculate degrees
        total_notes = len(mapping)
        total_edges = sum(len(links) for _, links in outgoing_edges.values())
        
        # Identify orphans
        orphans = []
        note_degrees = {}
        for note_key, file_path in mapping.items():
            actual_name = outgoing_edges[note_key][0]
            out_count = len(outgoing_edges[note_key][1])
            in_count = len(incoming_edges[note_key])
            total_deg = out_count + in_count
            note_degrees[actual_name] = (in_count, out_count, total_deg)
            
            if total_deg == 0:
                orphans.append(actual_name)
                
        # Sort notes by total degree to find hubs
        hubs = sorted(note_degrees.items(), key=lambda x: x[1][2], reverse=True)
        top_hubs = [f"• **{name}**: {deg[2]} connections ({deg[0]} in, {deg[1]} out)" for name, deg in hubs[:5] if deg[2] > 0]
        
        # Sort tags by frequency
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = [f"• #{tag}: {count} note(s)" for tag, count in sorted_tags[:10]]
        
        report = [
            f"# Obsidian Vault Analytics",
            f"Vault Location: `{vault_path}`",
            f"\n## General Stats",
            f"• **Total Notes (Nodes)**: {total_notes}",
            f"• **Total Connections (Edges)**: {total_edges}",
            f"\n## Hub Notes (Most Connected)",
            "\n".join(top_hubs) if top_hubs else "  (None yet)",
            f"\n## Orphan Notes (No Connections)",
            ", ".join(f"[[{o}]]" for o in orphans) if orphans else "  (None! All notes are connected.)",
            f"\n## Top Tags",
            "\n".join(top_tags) if top_tags else "  (No tags found)"
        ]
        
        return "\n".join(report)
    except Exception as e:
        return f"Error generating vault stats: {str(e)}"

# Export all defined Obsidian tools as a list
obsidian_toolset = [
    obsidian_set_vault,
    obsidian_get_vault,
    obsidian_create_note,
    obsidian_connect_notes,
    obsidian_get_connections,
    obsidian_get_vault_stats
]
