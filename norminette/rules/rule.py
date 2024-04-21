from typing import Tuple, Any, Literal

from norminette.context import Context


class Rule:
    __slots__ = ()

    def __new__(cls, context: Context, *args, **kwargs):
        cls.context = context
        cls.name = cls.__name__

        return super().__new__(cls, *args, **kwargs)

    def __repr__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, str):
            return self.name == value
        if isinstance(value, Rule):
            return self.name == value.name
        return super().__eq__(value)

    def __ne__(self, value: Any) -> bool:
        return not (self == value)


class Check:
    __slots__ = ()

    depends_on: Tuple[str, ...] = ()
    runs_on: Tuple[Literal["start", "rule", "end", "traverse"], ...] = ()

    def __init_subclass__(cls):
        if not cls.depends_on and not cls.runs_on:
            cls.runs_on = ("rule", *cls.runs_on)

    @classmethod
    def register(cls, registry):
        for rule in cls.depends_on:
            registry.dependencies[rule].append(cls)
        if "start" in cls.runs_on:
            registry.dependencies["_start"].append(cls)
        if "rule" in cls.runs_on:
            registry.dependencies["_rule"].append(cls)
        if "end" in cls.runs_on:
            registry.dependencies["_end"].append(cls)

    def is_starting(self) -> bool:
        """Returns if this `Check` is being run before `Primary`.

        It is only called if `"start"` is in `runs_on`.
        """
        return self.context.state == "starting"  # type: ignore

    def is_checking(self) -> bool:
        """Returns if this `Check` is being run after a `Primary` rule.

        It is only called if `"rule"` is in `runs_on`.
        """
        return self.context.state == "checking"  # type: ignore

    def is_ending(self) -> bool:
        """Returns if this `Check` is being run after all rules.

        It is only called if `"end"` is in `runs_on`.
        """
        return self.context.state == "ending"  # type: ignore

    def is_traversing(self) -> bool:
        return self.context.state == "traversing"  # type: ignore

    def run(self, context: Context) -> None:
        return


class Primary:
    __slots__ = ()

    priority: int
    scope: Tuple[str, ...]

    def __init_subclass__(cls, **kwargs: Any):
        cls.priority = kwargs.pop("priority", 0)
        if not hasattr(cls, "scope"):
            cls.scope = ()

    def run(self, context: Context) -> Tuple[bool, int]:
        return False, 0
