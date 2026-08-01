from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Order:
    subtotal_cents: int = 0
    is_member: bool = False
    items: int = 0
    coupons: tuple[str, ...] = ()


@dataclass(frozen=True)
class PriceResult:
    final_price_cents: int = 0
    applied_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RuleContext:
    order: Order
    milestone: int


@dataclass(frozen=True)
class Discount:
    percent: float = 0.0
    flat_cents: int = 0


class PricingRule(ABC):
    priority = 0
    group = ""
    disables_member = False
    is_member_rule = False

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Return the stable rule identifier."""

    @abstractmethod
    def applicable(self, context: RuleContext) -> bool:
        """Return whether this rule matches the order."""

    @abstractmethod
    def discount(self, context: RuleContext) -> Discount:
        """Return this rule's discount contribution."""


RuleFactory = Callable[[RuleContext], PricingRule]


class RuleRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, RuleFactory] = {}

    def register(self, key: str, factory: RuleFactory) -> None:
        self._factories[key] = factory

    def create_all(self, context: RuleContext) -> list[PricingRule]:
        return [factory(context) for factory in self._factories.values()]


DEFAULT_RULE_REGISTRY = RuleRegistry()


def compute_final_price(
    order: Order, milestone: int, registry: RuleRegistry = DEFAULT_RULE_REGISTRY
) -> PriceResult:
    context = RuleContext(order, milestone)
    rules = [
        rule for rule in registry.create_all(context) if rule.applicable(context)
    ]
    percent = min(sum(rule.discount(context).percent for rule in rules), 0.95)
    flat_cents = sum(rule.discount(context).flat_cents for rule in rules)
    price = max(0, round(order.subtotal_cents * (1.0 - percent) - flat_cents))
    return PriceResult(price, sorted(rule.rule_id for rule in rules))
