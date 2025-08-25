import asyncio
import inspect
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

from src.heal.common.logging_config import get_logger, log_performance

# 使用统一日志配置
logger = get_logger("dispatch")


class CommandError(Exception):
    """Base exception for command-related errors."""

    pass


class CommandAlreadyRegistered(CommandError):
    """Raised when attempting to register a command that already exists."""

    pass


class AliasConflictError(CommandError):
    """Raised when a command alias conflicts with an existing command or alias."""

    pass


class CommandNotFound(CommandError):
    """Raised when a command is not found."""

    pass


class PermissionDenied(CommandError):
    """Raised when a user lacks the required permissions to execute a command."""

    pass


class CommandOnCooldown(CommandError):
    """Raised when a command is invoked while it is still on cooldown."""

    pass


@dataclass
class Command:
    handler: Callable[..., Any]
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    cooldown: float = 0.0
    last_used: float = 0.0


class Middleware(Protocol):
    async def __call__(self, *args: Any, **kwargs: Any) -> tuple[Any, ...]: ...


class EventListener(Protocol):
    async def __call__(self, *args: Any, **kwargs: Any) -> None: ...


class CommandDispatcher:
    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}
        self._middleware: List[Middleware] = []
        self._events: Dict[str, List[EventListener]] = {}

    def register_command(
        self,
        command_name: str,
        handler: Callable[..., Any],
        description: str = "",
        aliases: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        cooldown: float = 0.0,
    ) -> None:
        aliases = aliases or []
        permissions = permissions or []

        if command_name in self._commands:
            logger.error(f"Command '{command_name}' is already registered.")
            raise CommandAlreadyRegistered(
                f"Command '{command_name}' is already registered."
            )

        for alias in aliases:
            if alias in self._commands:
                logger.error(f"Alias '{alias}' is already in use.")
                raise AliasConflictError(f"Alias '{alias}' is already in use.")

        command = Command(handler, description, aliases, permissions, cooldown)
        self._commands[command_name] = command

        for alias in aliases:
            self._commands[alias] = command

        logger.info(f"Registered command: '{command_name}' with aliases: {aliases}")

    def unregister_command(self, command_name: str) -> None:
        if command_name not in self._commands:
            logger.error(f"Command '{command_name}' is not registered.")
            raise CommandNotFound(f"Command '{command_name}' is not registered.")

        command = self._commands.pop(command_name)
        for alias in command.aliases:
            self._commands.pop(alias, None)

        logger.info(f"Unregistered command: '{command_name}'")

    async def execute_command(
        self,
        command_name: str,
        *args: Any,
        user_permissions: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Any:
        user_permissions = user_permissions or []

        if command_name not in self._commands:
            logger.error(f"Command '{command_name}' is not registered.")
            raise CommandNotFound(f"Command '{command_name}' is not registered.")

        command = self._commands[command_name]

        if not set(command.permissions).issubset(set(user_permissions)):
            logger.warning(
                f"User lacks permissions for command '{command_name}'. Required: {command.permissions}"
            )
            raise PermissionDenied(
                f"User doesn't have required permissions to execute '{command_name}'."
            )

        current_time = time.time()
        if current_time - command.last_used < command.cooldown:
            remaining = command.cooldown - (current_time - command.last_used)
            logger.warning(
                f"Command '{command_name}' is on cooldown. Try again in {remaining:.2f} seconds."
            )
            raise CommandOnCooldown(
                f"Command '{command_name}' is on cooldown. Try again in {remaining:.2f} seconds."
            )

        try:
            for middleware in self._middleware:
                args, kwargs = await middleware(*args, **kwargs)

            result = await self._execute_callable(command.handler, *args, **kwargs)
            command.last_used = time.time()
            logger.info(f"Executed command: '{command_name}' with result: {result}")
            await self.dispatch_event(f"{command_name}_executed", *args, **kwargs)
            return result
        except Exception as e:
            logger.exception(f"Error executing command '{command_name}': {e}")
            raise

    async def _execute_callable(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def get_command_info(self, command_name: str) -> Optional[Command]:
        return self._commands.get(command_name)

    def list_commands(self) -> Dict[str, str]:
        unique_commands = {
            name: cmd.description
            for name, cmd in self._commands.items()
            if name == cmd.handler.__name__
        }
        return unique_commands

    def command(
        self,
        name: str,
        description: str = "",
        aliases: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        cooldown: float = 0.0,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.register_command(
                name, func, description, aliases, permissions, cooldown
            )

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return func(*args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def auto_register(self, module: Any) -> None:
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if hasattr(obj, "_is_command") and getattr(obj, "_is_command"):
                description = getattr(obj, "_description", "")
                aliases = getattr(obj, "_aliases", [])
                permissions = getattr(obj, "_permissions", [])
                cooldown = getattr(obj, "_cooldown", 0.0)
                try:
                    self.register_command(
                        name, obj, description, aliases, permissions, cooldown
                    )
                except CommandError as e:
                    logger.error(f"Failed to register command '{name}': {e}")

    def add_middleware(self, middleware: Middleware) -> None:
        self._middleware.append(middleware)
        logger.info(
            f"Added middleware: {getattr(middleware, '__name__', str(middleware))}"
        )

    def remove_middleware(self, middleware: Middleware) -> None:
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            logger.info(
                f"Removed middleware: {getattr(middleware, '__name__', str(middleware))}"
            )
        else:
            logger.warning(
                f"Middleware '{getattr(middleware, '__name__', str(middleware))}' not found."
            )

    def add_event_listener(self, event_name: str, listener: EventListener) -> None:
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(listener)
        logger.info(f"Added event listener for event: '{event_name}'")

    def remove_event_listener(self, event_name: str, listener: EventListener) -> None:
        if event_name in self._events and listener in self._events[event_name]:
            self._events[event_name].remove(listener)
            logger.info(f"Removed event listener for event: '{event_name}'")
        else:
            logger.warning(f"Listener for event '{event_name}' not found.")

    async def dispatch_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        listeners = self._events.get(event_name, [])
        if not listeners:
            logger.debug(f"No listeners for event: '{event_name}'")
            return

        logger.info(f"Dispatching event: '{event_name}' to {len(listeners)} listeners.")
        for listener in listeners:
            try:
                await listener(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in event listener for '{event_name}': {e}")

    def batch_execute(
        self, commands: List[Dict[str, Any]]
    ) -> List[Any]:
        async def execute_all() -> List[Any]:
            tasks = []
            for cmd in commands:
                if isinstance(cmd, dict) and "name" in cmd:
                    task = self.execute_command(
                        str(cmd["name"]),
                        *cmd.get("args", []),
                        user_permissions=cmd.get("permissions", []),
                        **cmd.get("kwargs", {}),
                    )
                    tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results

        try:
            results: List[Any] = asyncio.run(execute_all())
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    cmd_name = commands[idx].get('name', 'unknown') if idx < len(commands) else 'unknown'
                    logger.error(
                        f"Error executing command '{cmd_name}': {result}"
                    )
                    results[idx] = None
            return results
        except Exception as e:
            logger.exception(f"Error in batch_execute: {e}")
            return [None for _ in commands]


# Global instance of CommandDispatcher
command_dispatcher = CommandDispatcher()


def command(
    name: str,
    description: str = "",
    aliases: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    cooldown: float = 0.0,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        func._is_command = True  # type: ignore
        func._description = description  # type: ignore
        func._aliases = aliases or []  # type: ignore
        func._permissions = permissions or []  # type: ignore
        func._cooldown = cooldown  # type: ignore

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await func(*args, **kwargs)

            return async_wrapper
        else:
            return wrapper

    return decorator


def some_safe_function() -> str:
    return "This is a safe function accessible from the exec."


# Example middleware
async def logging_middleware(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    logger.info(
        f"Middleware: Command is being executed with args: {args}, kwargs: {kwargs}"
    )
    return args, kwargs


command_dispatcher.add_middleware(logging_middleware)


# Example event listener
async def on_hello_executed(name: str) -> None:
    logger.info(f"Event Listener: 'hello_executed' event triggered with name: {name}")


command_dispatcher.add_event_listener("hello_executed", on_hello_executed)


# Example command registration
@command(
    name="hello",
    description="Say hello",
    aliases=["hi", "greet"],
    permissions=["basic"],
    cooldown=5.0,
)
async def hello(name: str = "World") -> str:
    await asyncio.sleep(1)  # Simulate async operation
    return f"Hello, {name}!"
