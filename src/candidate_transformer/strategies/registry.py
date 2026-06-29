from candidate_transformer.interfaces.strategy import Strategy
from candidate_transformer.utils.registry import Registry

strategy_registry = Registry[Strategy]("strategies")
