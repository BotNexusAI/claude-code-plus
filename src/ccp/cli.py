import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
import os
import subprocess
import sys
from dotenv import set_key, get_key, find_dotenv
from typing_extensions import Annotated
from pathlib import Path
import signal

app = typer.Typer(add_completion=False, invoke_without_command=True)
console = Console()
error_console = Console(stderr=True)

# --- Constants ---
PID_FILE = Path(os.getcwd()) / ".ccp.pid"
LOG_FILE = Path(os.getcwd()) / ".ccp.log"

# --- Helper Functions ---
def print_info(message):
    console.print(f"[bold blue][INFO][/bold blue] {message}")

def print_success(message):
    console.print(f"[bold green][SUCCESS][/bold green] {message}")

def print_warning(message):
    console.print(f"[bold yellow][WARNING][/bold yellow] {message}")

def print_error(message):
    error_console.print(f"[bold red][ERROR][/bold red] {message}")

def get_env_path():
    """Finds or creates a .env file path."""
    env_path = find_dotenv()
    if not env_path:
        env_path = os.path.join(os.getcwd(), ".env")
        # Create the file if it doesn't exist
        with open(env_path, "w") as f:
            pass
        print_info(f"Created .env file at: {env_path}")
    return env_path

def is_server_really_running():
    """
    Checks if the server is actually running by verifying the PID.
    Cleans up stale PID files.
    """
    if not PID_FILE.exists():
        return False
    
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        # Check if the process is actually running
        os.kill(pid, 0)
        return True # Process exists
    except (ValueError, FileNotFoundError, ProcessLookupError):
        # PID file is stale or corrupted
        print_warning("Stale PID file found. Cleaning up.")
        PID_FILE.unlink()
        return False

# --- CLI Commands ---

@app.command()
def init():
    """
    Initializes the project by setting up API keys and shell configuration.
    """
    console.rule("[bold]Project Initialization[/bold]")
    print_info("This wizard will guide you through setting up your environment.")

    env_path = get_env_path()

    # --- API Key Configuration ---
    console.print("\n[bold]1. API Keys[/bold]")
    
    # OpenAI Key
    existing_openai_key = get_key(env_path, "OPENAI_API_KEY") or ""
    prompt_text_openai = "Enter your OpenAI API Key"
    if existing_openai_key:
        masked_openai = f"{existing_openai_key[:4]}...{existing_openai_key[-4:]}"
        prompt_text_openai = f"Enter new OpenAI API Key (press Enter to keep {masked_openai})"
    
    openai_key_input = Prompt.ask(prompt_text_openai, password=True, show_default=False)
    final_openai_key = openai_key_input if openai_key_input else existing_openai_key

    # Gemini Key
    existing_gemini_key = get_key(env_path, "GEMINI_API_KEY") or ""
    prompt_text_gemini = "Enter your Gemini API Key"
    if existing_gemini_key:
        masked_gemini = f"{existing_gemini_key[:4]}...{existing_gemini_key[-4:]}"
        prompt_text_gemini = f"Enter new Gemini API Key (press Enter to keep {masked_gemini})"

    gemini_key_input = Prompt.ask(prompt_text_gemini, password=True, show_default=False)
    final_gemini_key = gemini_key_input if gemini_key_input else existing_gemini_key

    set_key(env_path, "OPENAI_API_KEY", final_openai_key)
    set_key(env_path, "GEMINI_API_KEY", final_gemini_key)
    print_success("API keys saved to .env file.")

    # --- Model Configuration ---
    console.print("\n[bold]2. Model Configuration[/bold]")
    preferred_provider = Prompt.ask(
        "Choose your preferred provider",
        choices=["openai", "google"],
        default=get_key(env_path, "PREFERRED_PROVIDER") or "openai"
    )
    big_model = Prompt.ask("Enter the model for 'sonnet' requests", default=get_key(env_path, "BIG_MODEL") or "gpt-4.1")
    small_model = Prompt.ask("Enter the model for 'haiku' requests", default=get_key(env_path, "SMALL_MODEL") or "gpt-4.1-mini")

    set_key(env_path, "PREFERRED_PROVIDER", preferred_provider)
    set_key(env_path, "BIG_MODEL", big_model)
    set_key(env_path, "SMALL_MODEL", small_model)
    print_success("Model configuration saved to .env file.")

    # --- Shell Configuration ---
    console.print("\n[bold]3. Shell Configuration[/bold]")
    if Confirm.ask("Add ANTHROPIC_BASE_URL to your shell startup file? (Recommended)"):
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            rc_file = os.path.expanduser("~/.zshrc")
        elif "bash" in shell:
            rc_file = os.path.expanduser("~/.bashrc")
        else:
            print_warning(f"Unsupported shell: {shell}. Please set ANTHROPIC_BASE_URL manually.")
            return

        url_export = "export ANTHROPIC_BASE_URL=http://localhost:8082"
        if os.path.exists(rc_file) and url_export in open(rc_file).read():
            print_info(f"ANTHROPIC_BASE_URL is already set in {rc_file}.")
        else:
            try:
                with open(rc_file, "a") as f:
                    f.write(f"\n# Added by Anthropic API Proxy\n{url_export}\n")
                print_success(f"Added ANTHROPIC_BASE_URL to {rc_file}.")
                print_info("Please restart your terminal or run 'source ~/{os.path.basename(rc_file)}' to apply changes.")
            except Exception as e:
                print_error(f"Failed to write to {rc_file}: {e}")

@app.command()
def start(
    foreground: Annotated[
        bool,
        typer.Option(
            "-f",
            "--foreground",
            help="Run the server in the foreground.",
        ),
    ] = False,
    auto: Annotated[
        bool,
        typer.Option(
            "--auto",
            help="Automatically launch the Claude Code client after starting the server.",
        ),
    ] = False,
):
    """
    Starts the proxy server.
    """
    console.rule("[bold]Starting Server[/bold]")

    if foreground and auto:
        print_error("The --foreground and --auto flags cannot be used together.")
        sys.exit(1)

    # Use the reliable check
    if is_server_really_running():
        if not auto:
            print_info("Server is already running. Displaying status:")
            status()
            sys.exit(0)
        # If --auto is used, we'll just proceed to launch the client
    else:
        # --- Environment and Dependency Setup ---
        venv_dir = ".venv"
        if not os.path.isdir(venv_dir):
            print_warning("Virtual environment not found. Creating one...")
            try:
                subprocess.run(["python3", "-m", "venv", venv_dir], check=True)
                print_success(f"Virtual environment created at '{venv_dir}'.")
            except subprocess.CalledProcessError as e:
                print_error(f"Failed to create virtual environment: {e}")
                sys.exit(1)

        print_info("Installing/updating dependencies...")
        try:
            pip_executable = os.path.join(venv_dir, "bin", "pip")
            subprocess.run(
                [pip_executable, "install", "-e", "."],
                check=True,
                capture_output=True,
                text=True,
            )
            print_success("Dependencies are up to date.")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e.stderr}")
            sys.exit(1)

        # --- Run Server ---
        uvicorn_executable = os.path.join(venv_dir, "bin", "uvicorn")
        command = [
            uvicorn_executable,
            "src.ccp.server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8082",
        ]

        if foreground:
            print_info("Starting server in foreground...")
            print_info("Run the following command in a new terminal to connect your client:")
            console.print("\n    [bold cyan]ANTHROPIC_BASE_URL=http://localhost:8082 claude[/bold cyan]\n")
            try:
                subprocess.run(command + ["--reload", "--reload-dir", "src"])
            except KeyboardInterrupt:
                print_info("\nServer stopped by user.")
            except Exception as e:
                print_error(f"Failed to start server: {e}")
                sys.exit(1)
            return

        # Start server in background for --auto or default mode
        print_info("Starting server in background...")
        try:
            # Redirect stdout/stderr to a log file
            with open(LOG_FILE, "wb") as log_file:
                process = subprocess.Popen(
                    command, stdout=log_file, stderr=log_file
                )
            
            with open(PID_FILE, "w") as f:
                f.write(str(process.pid))

            print_success(f"Server started in background with PID: {process.pid}")
            print_info("Run the following command in a new terminal to connect your client:")
            console.print("\n    [bold cyan]ANTHROPIC_BASE_URL=http://localhost:8082 claude[/bold cyan]\n")
            print_info("Server is running at: http://localhost:8082")
            print_info(f"Logs are being written to: {LOG_FILE}")
            print_info("Use 'ccp logs' to view logs or 'ccp stop' to stop the server.")

        except Exception as e:
            print_error(f"Failed to start server in background: {e}")
            sys.exit(1)

    if auto:
        # A short pause is always good before launching the client
        print_info("Launching Claude Code client...")
        
        import time
        import shutil
        time.sleep(2) # Give server a moment to start

        if not shutil.which("claude"):
            print_error("The 'claude' command was not found in your PATH.")
            print_info("Please ensure you have run 'npm install -g @anthropic-ai/claude-code'.")
            print_info("The server is still running. Use 'ccp stop' to stop it.")
            sys.exit(1)

        try:
            claude_env = os.environ.copy()
            claude_env["ANTHROPIC_BASE_URL"] = "http://localhost:8082"
            subprocess.run(["claude"], env=claude_env, check=True)
        except KeyboardInterrupt:
            print_info("\nClaude Code client stopped by user.")
        except subprocess.CalledProcessError as e:
            print_error(f"Claude Code client exited with an error: {e}")
        except Exception as e:
            print_error(f"Failed to launch Claude Code client: {e}")
        finally:
            print_info("The proxy server is still running in the background.")
            print_info("Run 'ccp stop' to shut it down.")


@app.command()
def stop():
    """
    Stops the background proxy server.
    """
    console.rule("[bold]Stopping Server[/bold]")
    if not PID_FILE.exists():
        print_warning("PID file not found. Is the server running?")
        sys.exit(1)

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
    except (ValueError, FileNotFoundError):
        print_error("Could not read PID from file. It might be corrupted.")
        PID_FILE.unlink() # Clean up corrupted file
        sys.exit(1)

    try:
        os.kill(pid, signal.SIGTERM)
        print_info(f"Sent stop signal to process with PID: {pid}")
    except ProcessLookupError:
        print_warning(f"Process with PID {pid} not found. It may have already stopped.")
    except Exception as e:
        print_error(f"Failed to stop server: {e}")
        sys.exit(1)
    finally:
        # Clean up the PID file
        PID_FILE.unlink()
        print_success("Server stopped and PID file removed.")


@app.command()
def logs():
    """
    Follows the server logs from the background process.
    """
    console.rule("[bold]Server Logs[/bold]")
    if not LOG_FILE.exists():
        print_warning(f"Log file not found: {LOG_FILE}")
        print_info("Start the server in the background first with 'ccp start'.")
        sys.exit(1)

    try:
        print_info(f"Following logs from {LOG_FILE}. Press Ctrl+C to stop.")
        subprocess.run(["tail", "-f", str(LOG_FILE)])
    except FileNotFoundError:
        print_error("The 'tail' command was not found. This feature is not available on your system.")
        sys.exit(1)
    except KeyboardInterrupt:
        print_info("\nStopped following logs.")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        sys.exit(1)


@app.command()
def config():
    """
    Displays the current configuration from the .env file, with sensitive keys masked.
    """
    status()

@app.callback()
def main(ctx: typer.Context):
    """
    Main callback to display status if no command is given.
    """
    check_anthropic_base_url_in_shell_config()
    if ctx.invoked_subcommand is None:
        status()

def check_anthropic_base_url_in_shell_config():
    """Checks shell config for ANTHROPIC_BASE_URL and informs the user of its status."""
    shell = os.environ.get("SHELL", "")
    rc_file = None
    if "zsh" in shell:
        rc_file = os.path.expanduser("~/.zshrc")
    elif "bash" in shell:
        rc_file = os.path.expanduser("~/.bashrc")

    url_export = "export ANTHROPIC_BASE_URL=http://localhost:8082"

    if rc_file and os.path.exists(rc_file):
        try:
            with open(rc_file, "r") as f:
                content = f.read()
                if url_export in content:
                    print_info(f"Found '{url_export}' in your '{os.path.basename(rc_file)}' file. Your client should connect automatically.")
                else:
                    print_warning(
                        f"'{url_export}' not found in your '{os.path.basename(rc_file)}' file.\n"
                        "Your client may not connect to the proxy automatically.\n"
                        "Run 'ccp init' to configure your shell, or use 'ANTHROPIC_BASE_URL=http://localhost:8082 claude'."
                    )
        except Exception as e:
            # Fail silently, not critical enough to stop execution
            print_error(f"Could not check shell config file: {e}")
    else:
        # If no rc file is found, it's likely the user needs to set it manually
        print_warning(
            f"Could not find a shell configuration file ({rc_file}).\n"
            "Ensure 'export ANTHROPIC_BASE_URL=http://localhost:8082' is set in your environment to use the proxy."
        )

def status():
    """
    Displays the server status and current configuration.
    """
    console.rule("[bold]Claude Code Plus Status[/bold]")

    # --- Server Status ---
    console.print("[bold]Server Status[/bold]")
    if is_server_really_running():
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        print_success(f"Running (PID: {pid})")
        console.print(f"Address: http://localhost:8082")
        if LOG_FILE.exists():
            console.print(f"Log File: {LOG_FILE}")
    else:
        print_info("Stopped")

    # --- Configuration ---
    console.print("\n[bold]Configuration[/bold]")
    env_path = find_dotenv()
    if not env_path or not os.path.exists(env_path):
        print_warning("No .env file found. Run 'ccp init' to create one.")
        return

    with open(env_path) as f:
        lines = f.readlines()
        if not lines:
            print_warning("'.env' file is empty. Run 'ccp init' to configure.")
            return
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                key, value = line.split('=', 1)
                if "API_KEY" in key and len(value) > 8:
                    masked_value = f"'{value[:4]}...{value[-4:]}'"
                    console.print(f"{key}={masked_value}")
                else:
                    console.print(line)
            except ValueError:
                console.print(line)


if __name__ == "__main__":
    app()
