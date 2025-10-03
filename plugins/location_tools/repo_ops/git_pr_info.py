import subprocess
import sys
import os
import json
import re

def parse_git_output_to_json(output):
    """
    Parse git log output into JSON object with commit_id as key
    
    Args:
        output (str): Raw git log output
        
    Returns:
        dict: JSON object with commit_id as key and commit info as value
    """
    
    commits = {}
    current_commit = None
    current_content = []
    
    lines = output.split('\n')
    
    for line in lines:
        # Check if line starts with commit hash (8 hex chars followed by space or colon)
        commit_match = re.match(r'^([a-f0-9]{7,8})\s*[:-]', line)
        
        if commit_match:
            # Save previous commit if exists
            if current_commit:
                commits[current_commit] = '\n'.join(current_content).strip()
            
            # Start new commit
            current_commit = commit_match.group(1)
            current_content = [line]
        else:
            # Add line to current commit content
            if current_commit:
                current_content.append(line)
    
    # Save last commit
    if current_commit:
        commits[current_commit] = '\n'.join(current_content).strip()
    
    return commits

def git_detailed(repo_path, mode="all", limit=50):
    """
    Run git log command to show commits with file changes
    
    Args:
        repo_path (str): Path to the git repository
        mode (str): "prs"/"merges" for PRs only, anything else for all commits
        limit (int): Number of commits to show (default: 50)
    """
    
    # Validate repository path
    if not os.path.exists(repo_path):
        print(f"Error: Repository path '{repo_path}' does not exist", file=sys.stderr)
        return None
    
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: '{repo_path}' is not a git repository", file=sys.stderr)
        return None
    
    # Build the git command
    merge_flag = "--merges" if mode in ["prs", "merges"] else ""
    
    # Print header
    if mode in ["prs", "merges"]:
        print(f"=== Showing PRs/Merges only (last {limit}) ===")
    else:
        print(f"=== Showing all commits (last {limit}) ===")
    
    # Build git command parts - remove username for PRs
    if mode in ["prs", "merges"]:
        pretty_format = "%h : %s%n%n%b"  # No username for PRs
    else:
        pretty_format = "%h - %an, %ar : %s%n%n%b"  # Keep username for regular commits
    
    git_cmd = [
        "git", "log", f"-{limit}"
    ]
    
    # Add merge flag if needed
    if merge_flag:
        git_cmd.append(merge_flag)
    
    # Add remaining flags
    git_cmd.extend([
        "-m", "--first-parent", "--name-status", 
        f"--pretty=format:{pretty_format}"
    ])
    
    # Build sed command
    sed_cmd = [
        "sed", 
        "s/^M\\t/Modified: /; s/^A\\t/Added: /; s/^D\\t/Deleted: /; s/^R[0-9]*\\t/Renamed: /; s/^C[0-9]*\\t/Copied: /"
    ]
    
    try:
        # Run git command
        git_process = subprocess.Popen(
            git_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=repo_path
        )
        
        # Pipe to sed
        sed_process = subprocess.Popen(
            sed_cmd,
            stdin=git_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Close git stdout to allow it to receive SIGPIPE
        git_process.stdout.close()
        
        # Get output
        output, error = sed_process.communicate()
        
        # Check for errors
        if sed_process.returncode != 0:
            print(f"Error: {error}", file=sys.stderr)
            return None
        
        # Parse output into JSON object
        return parse_git_output_to_json(output)
        
    except FileNotFoundError:
        print("Error: Git not found. Make sure git is installed and in PATH.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return None

def main():
    """
    Command line interface for git-detailed function
    Usage: python script.py [mode] [limit]
    """
    
    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    # Run the command
    result = git_detailed(mode, limit)
    
    if result:
        # Pretty print JSON
        print(json.dumps(result, indent=2))
    else:
        sys.exit(1)

# Example usage functions
def show_prs_only(repo_path, limit=50):
    """Show only PRs/merges as JSON"""
    return git_detailed(repo_path, "prs", limit)

def show_all_commits(repo_path, limit=50):
    """Show all commits as JSON"""
    return git_detailed(repo_path, "all", limit)


__all__ = [
    'show_all_commits',
    'show_prs_only'
]

if __name__ == "__main__":
    main()

# Example usage:
# python script.py /path/to/repo prs      # Shows only PRs (last 50) as JSON
# python script.py /path/to/repo prs 20   # Shows only PRs (last 20) as JSON
# python script.py /path/to/repo all      # Shows all commits (last 50) as JSON
# python script.py /path/to/repo all 100  # Shows all commits (last 100) as JSON

# Or use the functions directly:
# result = show_prs_only("/path/to/repo", 20)          # Returns dict
# result = show_all_commits("/path/to/repo", 100)      # Returns dict
# commit_info = get_commit_info("/path/to/repo", "a1b2c3d", "prs", 50)  # Get specific commit

# Example JSON output structure:
# {
#   "a1b2c3d": "a1b2c3d : Merge pull request #123 from feature/auth\n\nFix authentication issues\n\nModified: src/auth.js\nAdded: tests/auth.test.js",
#   "e4f5g6h": "e4f5g6h : Merge pull request #124 from feature/dashboard\n\nAdd new dashboard\n\nAdded: src/dashboard.js"
# }