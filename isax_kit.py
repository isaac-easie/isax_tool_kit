"""iSAX Multi-Toolbox: a small, extensible, standard-library CLI toolbox.

Customization area:
	Change these values to personalize the program. To add a tool, define a
	function and add a (label, aliases, function) tuple to a submenu below.
"""

import base64
import builtins
import datetime as dt
import hashlib
import json
import math
import os
import platform
import random
import secrets
import shutil
import socket
import string
import subprocess
import sys
import textwrap
import time
import re
import difflib
import getpass
import uuid
import ssl
import urllib.parse
from pathlib import Path
from typing import Callable, Iterable, Optional


TOOL_NAME = "iSAX Tool-Kit"
VERSION = "1.0"
AUTHOR = "Isaac"
EFFECTS_ENABLED = True

# ANSI theme: set EFFECTS_ENABLED to False for plain output or redirected logs. 
RESET = "\033[0m"
BLACK = "\033[30m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BRIGHT = "\033[1m"
_standard_print = builtins.print
_standard_input = builtins.input


def enable_terminal_colors() -> None:
	if os.name == "nt":
		try:
			import ctypes

			handle = ctypes.windll.kernel32.GetStdHandle(-11)
			mode = ctypes.c_ulong()
			if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
				ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
		except (AttributeError, OSError):
			pass


def themed_print(*values: object, sep: str = " ", end: str = "\n", file: object = None, flush: bool = False) -> None:
	text = sep.join(str(value) for value in values)
	if not EFFECTS_ENABLED or file is not None:
		_standard_print(*values, sep=sep, end=end, file=file, flush=flush)
		return
	lowered = text.casefold()
	if any(word in lowered for word in ("error", "failed", "invalid", "warning", "unavailable", "not reachable")):
		color = RED
	elif text.startswith(("=", "-")) or text.isupper() or "tool-kit" in lowered:
		color = CYAN
	elif text.startswith("Version") or text.startswith("Goodbye"):
		color = YELLOW
	else:
		color = GREEN
	_standard_print(f"{color}{text}{RESET}", end=end, flush=flush)


def themed_input(prompt: str = "") -> str:
	if not EFFECTS_ENABLED:
		return _standard_input(prompt)
	return _standard_input(f"{GREEN}{prompt}{RESET}")


# Existing tool functions use print() and input(); these aliases theme them globally.
print = themed_print
input = themed_input


def clear_screen() -> None:
	if EFFECTS_ENABLED:
		_standard_print("\033[2J\033[H", end="")


def boot_effect() -> None:
	if not EFFECTS_ENABLED:
		return
	_standard_print(f"{DIM}{GREEN}Initializing secure toolbox interface...{RESET}", flush=True)
	for step in ("[ OK ] Loading modules", "[ OK ] Checking terminal", "[ OK ] Ready"):
		_standard_print(f"{GREEN}{step}{RESET}")
		time.sleep(0.04)

Tool = tuple[str, tuple[str, ...], Callable[[], None]]


def clear_line() -> None:
	print("-" * 40)


def pause() -> None:
	input("\nPress Enter to return to the menu...")


def normalized(value: str) -> str:
	return value.strip().casefold()


def ask_nonempty(prompt: str) -> str:
	while True:
		value = input(prompt).strip()
		if value:
			return value
		print("Please enter a value.")


def ask_yes_no(prompt: str, default: Optional[bool] = None) -> bool:
	while True:
		answer = normalized(input(prompt))
		if answer in {"y", "yes"}:
			return True
		if answer in {"n", "no"}:
			return False
		if not answer and default is not None:
			return default
		print("Please answer yes or no (y/n).")


def ask_int(prompt: str, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
	while True:
		try:
			value = int(input(prompt).strip())
			if minimum is not None and value < minimum:
				raise ValueError
			if maximum is not None and value > maximum:
				raise ValueError
			return value
		except ValueError:
			bounds = ""
			if minimum is not None and maximum is not None:
				bounds = f" from {minimum} to {maximum}"
			elif minimum is not None:
				bounds = f" greater than or equal to {minimum}"
			print(f"Invalid number. Please enter a whole number{bounds}.")


def ask_float(prompt: str) -> float:
	while True:
		try:
			return float(input(prompt).strip())
		except ValueError:
			print("Invalid number. Please enter a number such as 12 or 3.5.")


def run_tool(tool: Tool) -> None:
	label, _, function = tool
	while True:
		print(f"\n{label}")
		clear_line()
		try:
			function()
		except KeyboardInterrupt:
			print("\nOperation cancelled.")
		except (OSError, ValueError, json.JSONDecodeError) as error:
			print(f"Something went wrong: {error}")
		except Exception as error:
			print(f"Something went wrong: {error}")
		if not ask_yes_no("\nRun again? (y/n): "):
			return


def run_submenu(title: str, tools: Iterable[Tool]) -> None:
	tools = tuple(tools)
	while True:
		print(f"\n{title.upper()}")
		clear_line()
		for number, (label, _, _) in enumerate(tools, start=1):
			print(f"{number}. {label}")
		print("0. Back")
		choice = normalized(input("\nChoose an option: "))
		if choice in {"0", "back", "b"}:
			return
		selected = next(
			(tool for number, tool in enumerate(tools, start=1)
			 if choice == str(number) or choice in tool[1]),
			None,
		)
		if selected is None:
			print(f"Invalid choice. Please enter a number from 1 to {len(tools)}, or 0 to go back.")
			continue
		run_tool(selected)


def show_system_info() -> None:
	print(f"Operating system: {platform.platform()}")
	print(f"Computer name: {platform.node() or socket.gethostname()}")
	print(f"Python version: {platform.python_version()}")
	print(f"CPU: {platform.processor() or 'Information unavailable'}")
	print(f"CPU cores: {os.cpu_count() or 'Information unavailable'}")
	print(f"RAM: {ram_text()}")
	print(f"Current time: {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")


def ram_text() -> str:
	if hasattr(os, "sysconf"):
		try:
			pages = os.sysconf("SC_PHYS_PAGES")
			page_size = os.sysconf("SC_PAGE_SIZE")
			return f"{pages * page_size / (1024 ** 3):.2f} GB total"
		except (ValueError, OSError):
			pass
	if sys.platform == "win32":
		try:
			import ctypes

			class MemoryStatus(ctypes.Structure):
				_fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
							("total_phys", ctypes.c_ulonglong), ("available_phys", ctypes.c_ulonglong),
							("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
							("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
							("available_extended", ctypes.c_ulonglong)]

			status = MemoryStatus()
			status.length = ctypes.sizeof(status)
			ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
			return f"{status.total_phys / (1024 ** 3):.2f} GB total"
		except (AttributeError, OSError):
			pass
	return "Information unavailable on this platform"


def show_local_ip() -> None:
	hostname = socket.gethostname()
	addresses = sorted({item[4][0] for item in socket.getaddrinfo(hostname, None, socket.AF_INET)})
	print(f"Hostname: {hostname}")
	print("Local IPv4 address(es):")
	print("\n".join(f"  {address}" for address in addresses) or "  No address found")


def test_internet() -> None:
	try:
		with socket.create_connection(("example.com", 80), timeout=5):
			print("Internet connection: available")
	except OSError as error:
		print(f"Internet connection: unavailable ({error})")


def ping_host() -> None:
	host = ask_nonempty("Host to ping: ")
	count_flag = "-n" if sys.platform == "win32" else "-c"
	try:
		result = subprocess.run(
			["ping", count_flag, "4", host], capture_output=True, text=True,
			timeout=15, check=False,
		)
		print(result.stdout.strip() or result.stderr.strip() or f"Ping exited with code {result.returncode}.")
	except FileNotFoundError:
		print("The ping command is not available on this computer.")
	except subprocess.TimeoutExpired:
		print("Ping timed out.")


def show_network_interfaces() -> None:
	command = ["ipconfig"] if sys.platform == "win32" else ["ifconfig"]
	if sys.platform not in {"win32", "darwin"} and shutil.which("ip"):
		command = ["ip", "address"]
	if not shutil.which(command[0]):
		print("A network-interface command is not available on this computer.")
		return
	result = subprocess.run(command, capture_output=True, text=True, check=False)
	print(result.stdout.strip() or result.stderr.strip())


def list_files() -> None:
	directory = Path(input(f"Directory [default: {Path.cwd()}]: ").strip() or Path.cwd()).expanduser()
	if not directory.is_dir():
		print("That directory does not exist.")
		return
	entries = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold()))
	if not entries:
		print("The directory is empty.")
		return
	for entry in entries:
		marker = "[DIR] " if entry.is_dir() else "      "
		print(f"{marker}{entry.name}")


def file_information() -> None:
	path = Path(ask_nonempty("File path: ")).expanduser()
	if not path.is_file():
		print("That file does not exist.")
		return
	stat = path.stat()
	print(f"Name: {path.name}")
	print(f"Absolute path: {path.resolve()}")
	print(f"Size: {stat.st_size:,} bytes")
	print(f"Modified: {dt.datetime.fromtimestamp(stat.st_mtime).astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")


def password_generator() -> None:
	length = ask_int("Password length [12]: ", minimum=4) if input("Use 12-character default? (y/n): ").strip().casefold() not in {"y", "yes", ""} else 12
	alphabet = string.ascii_letters + string.digits + string.punctuation
	password = "".join(secrets.choice(alphabet) for _ in range(length))
	print(f"Generated password: {password}")


def percentage_calculator() -> None:
	percent = ask_float("Percentage: ")
	number = ask_float("Number: ")
	print(f"Result: {percent * number / 100:g}")


def unit_converter() -> None:
	value = ask_float("Value: ")
	source = normalized(ask_nonempty("From unit (km, m, mi, kg, lb, c, f): "))
	target = normalized(ask_nonempty("To unit: "))
	conversions = {
		"km": (1000, "length"), "m": (1, "length"), "mi": (1609.344, "length"),
		"kg": (1, "mass"), "lb": (0.45359237, "mass"),
	}
	if source in conversions and target in conversions and conversions[source][1] == conversions[target][1]:
		result = value * conversions[source][0] / conversions[target][0]
	elif source in {"c", "f"} and target in {"c", "f"}:
		result = value if source == target else (value * 9 / 5 + 32 if source == "c" else (value - 32) * 5 / 9)
	else:
		print("Unsupported or incompatible units.")
		return
	print(f"Result: {result:g} {target}")


def age_calculator() -> None:
	birthday = dt.datetime.strptime(ask_nonempty("Birth date (YYYY-MM-DD): "), "%Y-%m-%d").date()
	today = dt.date.today()
	age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
	print(f"Age: {age} years")


def random_number() -> None:
	first = ask_int("Minimum: ")
	last = ask_int("Maximum: ")
	if first > last:
		first, last = last, first
	print(f"Random number: {random.randint(first, last)}")


def json_formatter() -> None:
	data = json.loads(ask_nonempty("JSON text: "))
	print(json.dumps(data, indent=4, ensure_ascii=False))


def base64_tool() -> None:
	mode = normalized(input("Encode or decode? (e/d): "))
	text = ask_nonempty("Text: ")
	if mode in {"e", "encode"}:
		print(base64.b64encode(text.encode()).decode())
	elif mode in {"d", "decode"}:
		print(base64.b64decode(text).decode())
	else:
		print("Choose e for encode or d for decode.")


def url_tool() -> None:
	mode = normalized(input("Encode or decode? (e/d): "))
	text = ask_nonempty("Text or URL: ")
	if mode in {"e", "encode"}:
		print(urllib.parse.quote(text, safe=""))
	elif mode in {"d", "decode"}:
		print(urllib.parse.unquote(text))
	else:
		print("Choose e for encode or d for decode.")


def hash_text() -> None:
	algorithm = normalized(input("Hash algorithm (sha256, sha512, md5) [sha256]: ") or "sha256")
	if algorithm not in hashlib.algorithms_available:
		print("That hash algorithm is not available.")
		return
	text = ask_nonempty("Text to hash: ")
	print(hashlib.new(algorithm, text.encode()).hexdigest())


def regex_tester() -> None:
	pattern = ask_nonempty("Regular expression: ")
	text = ask_nonempty("Text to test: ")
	try:
		matches = list(re.finditer(pattern, text))
	except re.error as error:
		print(f"Invalid regular expression: {error}")
		return
	if not matches:
		print("No matches found.")
		return
	print(f"Matches found: {len(matches)}")
	for match in matches:
		print(f"  {match.group()!r} at characters {match.start()}-{match.end()}")


def generate_uuid() -> None:
	print(f"UUID4: {uuid.uuid4()}")


def timestamp_converter() -> None:
	mode = normalized(input("Convert Unix timestamp to date, or date to timestamp? (t/d): "))
	if mode in {"t", "timestamp", "unix"}:
		value = ask_float("Unix timestamp: ")
		print(dt.datetime.fromtimestamp(value).astimezone().isoformat())
	elif mode in {"d", "date", "datetime"}:
		value = ask_nonempty("ISO date/time (for example 2026-09-18T12:30:00): ")
		parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
		if parsed.tzinfo is None:
			parsed = parsed.astimezone()
		print(f"Unix timestamp: {parsed.timestamp():.0f}")
	else:
		print("Choose t for timestamp or d for date.")


def compare_files() -> None:
	first = Path(ask_nonempty("First text file: ")).expanduser()
	second = Path(ask_nonempty("Second text file: ")).expanduser()
	if not first.is_file() or not second.is_file():
		print("Both paths must point to existing files.")
		return
	left = first.read_text(encoding="utf-8", errors="replace").splitlines()
	right = second.read_text(encoding="utf-8", errors="replace").splitlines()
	difference = difflib.unified_diff(left, right, fromfile=str(first), tofile=str(second), lineterm="")
	print("\n".join(difference) or "Files are identical.")


def show_environment() -> None:
	search = normalized(input("Filter variable names (blank for all): "))
	items = sorted((key, value) for key, value in os.environ.items() if not search or search in normalized(key))
	if not items:
		print("No matching environment variables found.")
		return
	for key, value in items:
		print(f"{key}={value}")


def inspect_python_module() -> None:
	module_name = ask_nonempty("Python module name: ")
	try:
		module = __import__(module_name)
		print(f"Module: {module.__name__}")
		print(f"Location: {getattr(module, '__file__', 'built-in or namespace module')}")
		print(f"Version: {getattr(module, '__version__', 'not provided')}")
	except ImportError as error:
		print(f"Module could not be imported: {error}")


def hash_file() -> None:
	path = Path(ask_nonempty("File to hash: ")).expanduser()
	algorithm = normalized(input("Algorithm [sha256]: ") or "sha256")
	if not path.is_file():
		print("That file does not exist.")
		return
	if algorithm not in hashlib.algorithms_available:
		print("That hash algorithm is not available.")
		return
	digest = hashlib.new(algorithm)
	with path.open("rb") as handle:
		for block in iter(lambda: handle.read(1024 * 1024), b""):
			digest.update(block)
	print(f"{algorithm}: {digest.hexdigest()}")


def password_strength() -> None:
	password = getpass.getpass("Password to evaluate (not stored): ")
	score = sum((len(password) >= 12, bool(re.search(r"[a-z]", password)),
				 bool(re.search(r"[A-Z]", password)), bool(re.search(r"\d", password)),
				 bool(re.search(r"[^A-Za-z0-9]", password))))
	labels = {0: "very weak", 1: "weak", 2: "fair", 3: "good", 4: "strong", 5: "very strong"}
	print(f"Strength: {labels[score]} ({score}/5)")
	if len(password) < 12:
		print("Tip: use at least 12 characters.")


def scan_for_secrets() -> None:
	path = Path(ask_nonempty("Text file or directory to scan: ")).expanduser()
	if not path.exists():
		print("That path does not exist.")
		return
	patterns = {
		"private key marker": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
		"AWS access key shape": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
		"generic token assignment": re.compile(r"(?i)\b(?:api[_-]?key|secret|token|password)\s*[:=]")
	}
	files = [path] if path.is_file() else [item for item in path.rglob("*") if item.is_file() and item.stat().st_size < 5_000_000]
	found = 0
	for item in files:
		try:
			for line_number, line in enumerate(item.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
				for name, pattern in patterns.items():
					if pattern.search(line):
						print(f"{item}:{line_number}: possible {name}")
						found += 1
		except OSError:
			continue
	print(f"Scan complete. Possible matches: {found}")


def audit_permissions() -> None:
	path = Path(ask_nonempty("File or directory to inspect: ")).expanduser()
	if not path.exists():
		print("That path does not exist.")
		return
	mode = path.stat().st_mode
	print(f"Path: {path.resolve()}")
	print(f"Permissions: {oct(mode & 0o777)}")
	if mode & 0o002:
		print("Warning: writable by everyone.")
	else:
		print("Not world-writable.")
	if path.is_file() and mode & 0o004:
		print("Readable by everyone on this system.")


def dns_lookup() -> None:
	host = ask_nonempty("Hostname: ")
	try:
		name, aliases, addresses = socket.gethostbyname_ex(host)
		print(f"Canonical name: {name}")
		print(f"Aliases: {', '.join(aliases) or 'none'}")
		print(f"IPv4 addresses: {', '.join(addresses) or 'none'}")
	except socket.gaierror as error:
		print(f"DNS lookup failed: {error}")


def check_tcp_port() -> None:
	print("Use this only against systems you own or are authorized to test.")
	host = ask_nonempty("Host: ")
	port = ask_int("TCP port (1-65535): ", 1, 65535)
	try:
		with socket.create_connection((host, port), timeout=3):
			print(f"TCP {port} on {host}: reachable")
	except OSError as error:
		print(f"TCP {port} on {host}: not reachable ({error})")


def inspect_tls_certificate() -> None:
	host = ask_nonempty("HTTPS hostname: ")
	context = ssl.create_default_context()
	try:
		with socket.create_connection((host, 443), timeout=5) as connection:
			with context.wrap_socket(connection, server_hostname=host) as secure:
				certificate = secure.getpeercert()
				print(f"Subject: {certificate.get('subject')}")
				print(f"Issuer: {certificate.get('issuer')}")
				print(f"Valid from: {certificate.get('notBefore')}")
				print(f"Valid until: {certificate.get('notAfter')}")
	except (OSError, ssl.SSLError) as error:
		print(f"TLS inspection failed: {error}")


SYSTEM_TOOLS: tuple[Tool, ...] = (
	("Show system information", ("sys", "info"), show_system_info),

)
NETWORK_TOOLS: tuple[Tool, ...] = (
	("Show local IP and hostname", ("ip", "host"), show_local_ip),
	("Test internet connection", ("internet", "online"), test_internet),
	("Ping a host", ("ping",), ping_host),
	("Show network interfaces", ("interfaces", "ifconfig"), show_network_interfaces),
)
FILE_TOOLS: tuple[Tool, ...] = (
	("List files in a directory", ("list", "ls"), list_files),
	("Show file information", ("info", "stat"), file_information),
)

UTILITY_TOOLS: tuple[Tool, ...] = (
	("Unit converter", ("convert",), unit_converter),
	("Percentage calculator", ("percent",), percentage_calculator),
	("Age calculator", ("age",), age_calculator),
	("Random number generator", ("random",), random_number),
	("Password generator", ("password", "pass"), password_generator),
)
DEVELOPER_TOOLS: tuple[Tool, ...] = (
	("Format/validate JSON", ("json",), json_formatter),
	("Base64 encode/decode", ("base64",), base64_tool),
	("URL encode/decode", ("url",), url_tool),
	("Hash text", ("hash",), hash_text),
	("Regular expression tester", ("regex", "regexp"), regex_tester),
	("Generate UUID4", ("uuid",), generate_uuid),
	("Convert Unix timestamp", ("timestamp", "time"), timestamp_converter),
	("Compare two text files", ("diff", "compare"), compare_files),
	("Inspect environment variables", ("env", "environment"), show_environment),
	("Inspect a Python module", ("module", "import"), inspect_python_module),
)
SECURITY_TOOLS: tuple[Tool, ...] = (
	("Hash a file", ("filehash", "sha"), hash_file),
	("Check password strength", ("strength",), password_strength),
	("Scan files for possible secrets", ("secrets", "scan"), scan_for_secrets),
	("Audit file permissions", ("permissions", "perms"), audit_permissions),
	("DNS lookup", ("dns",), dns_lookup),
	("Check one authorized TCP port", ("port", "tcp"), check_tcp_port),
	("Inspect HTTPS certificate", ("tls", "certificate"), inspect_tls_certificate),
)


CATEGORIES: tuple[Tool, ...] = (
	("System Information", ("system", "sys"), lambda: run_submenu("System Tools", SYSTEM_TOOLS)),
	("Network Information", ("network", "net"), lambda: run_submenu("Network Tools", NETWORK_TOOLS)),
	("IP / Connectivity Tools", ("connectivity", "ip"), lambda: run_submenu("IP / Connectivity Tools", NETWORK_TOOLS)),
	("File Utilities", ("files", "file"), lambda: run_submenu("File Tools", FILE_TOOLS)),
	("Password Generator", ("password", "pass"), lambda: run_tool(("Password Generator", (), password_generator))),
	("Text Utilities", ("text",), lambda: run_submenu("Text Tools", TEXT_TOOLS)),
	("Developer Utilities", ("developer", "dev"), lambda: run_submenu("Developer Tools", DEVELOPER_TOOLS)),
	("Other Tools", ("other", "utilities", "util"), lambda: run_submenu("Other Tools", UTILITY_TOOLS[4:])),
	("Security & Diagnostics", ("security", "sec", "defensive"), lambda: run_submenu("Security & Diagnostics", SECURITY_TOOLS)),
)


def show_banner() -> None:
	clear_screen()
	print("\n" + "=" * 40)
	print(f"        {TOOL_NAME.upper()}")
	print("=" * 40)


def main_menu() -> None:
	while True:
		show_banner()
		print(f"Version {VERSION} | Author: {AUTHOR}\n")
		for number, (label, _, _) in enumerate(CATEGORIES, start=1):
			print(f"{number}. {label}")
		print("0. Exit")
		choice = normalized(input("\nChoose an option: "))
		if choice in {"0", "exit", "quit", "q"}:
			print("Goodbye!")
			return
		selected = next(
			(category for number, category in enumerate(CATEGORIES, start=1)
			 if choice == str(number) or choice in category[1]),
			None,
		)
		if selected is None:
			print("Invalid choice. Please enter a menu number or a category name.")
			continue
		run_tool(selected)


def main() -> None:
	try:
		enable_terminal_colors()
		boot_effect()
		main_menu()
	except KeyboardInterrupt:
		print("\n\nGoodbye!")
	except EOFError:
		print("\n\nInput ended. Goodbye!")


if __name__ == "__main__":
	main()
