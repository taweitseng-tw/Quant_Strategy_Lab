# Genetic Programming Design (Task 031A)

## 1. GP Tree Mapping to Existing Strategy Model
The current strategy engine evaluates conditions iteratively inside a `StrategyBlock`, combining them with a single `logic` operator (AND or OR). To map a Genetic Programming (GP) tree back to this structure without modifying the evaluation engine:
- The GP tree is restricted to a **depth of 2**.
- The **Root Node** must be a Logical Node representing the block's `logic` operator (AND / OR).
- The **Leaf Nodes** (children of the root) must be Condition Nodes representing `core.models.strategy.Condition` instances.
- This fixed-depth tree exactly compiles into a single `StrategyBlock`: `logic = Root.operator`, `conditions = Root.children`.

## 2. Allowed Node Types
- **Logical Nodes (Root only):** `AND`, `OR`.
- **Condition Nodes (Leaves only):** `SMA`, `RSI`, `MACD`, `ATR`.
- **Disallowed Nodes:** Nested Logical Nodes (e.g., `AND` inside `OR`), arithmetic operators, mathematical constants.

## 3. Deterministic Generation
- The initial population of GP trees will be generated using Python's `random.Random(seed)`.
- For each StrategyBlock, the GP generator will randomly select a Root Node (AND/OR) and a random number of Leaf Nodes (1 to `max_conditions`).
- All genetic operations (Crossover, Mutation) will accept the same RNG instance or pass the deterministic seed, ensuring fully reproducible strategy evolution.

## 4. Depth and Complexity Limits
- **Max Depth:** 2 (Root -> Leaves). This restriction ensures 100% compatibility with the current `StrategyBlock` flat evaluation logic.
- **Max Conditions:** 5 conditions per block. This prevents "bloat" (a common issue in GP) and maintains interpretability of the exported rules.
- **Allowed Indicators:** Limited strictly to MVP indicators (SMA, RSI, MACD, ATR).

## 5. Mutation and Crossover (High Level)
- **Crossover:** 
  - Standard one-point or uniform crossover operating on the list of children (Condition Leaves).
  - Given Parent A and Parent B, randomly swap subset(s) of Condition Nodes between them. The Root Node (AND/OR) can also be crossed over.
- **Mutation:**
  - **Node Mutation:** Flip the Root Node logic (e.g., AND -> OR).
  - **Leaf Mutation:** Perturb a Condition Leaf by mutating its indicator type, operator, or shifting its numeric parameters (e.g., RSI period 14 -> 15).
  - **Structural Mutation:** Add a new random Condition Leaf (Grow) or remove a random Condition Leaf (Shrink), subject to the `max_conditions` limit.

## 6. Fitness Adapter Reuse
- The GP evolution process will treat an individual as a collection of 4 GP Trees (Long Entry, Long Exit, Short Entry, Short Exit).
- During fitness evaluation, the 4 GP trees will be compiled directly into a `core.models.strategy.Strategy` object.
- This standard `Strategy` object will be passed exactly as-is into `strategy_engine.ga_fitness.make_fitness_adapter(...)`.
- This ensures zero duplication of backtest, ranking, elimination, or walk-forward logic.

## 7. No Future Leak Assumptions
- The GP generator solely produces declarative `Strategy` configurations. 
- It relies entirely on `strategy_engine.evaluator`, which binds variables via `df.at[i, col]`.
- Because the GP does not introduce any custom inline evaluation expressions or pandas shifts, it strictly inherits the existing engine's zero-future-leak guarantees.

## 8. Concrete Tests for Implementation Phase
When building the actual GP code, the following tests must be implemented:
1. `test_gp_tree_compiles_to_strategy_block`: Verify the depth-2 tree correctly exports `StrategyBlock(conditions=[...], logic=...)`.
2. `test_gp_deterministic_initialization`: Verify that `generate_population(seed=X)` yields identical GP trees across multiple calls.
3. `test_gp_crossover_maintains_depth_limit`: Verify crossover logic strictly limits output to Depth 2 (no nested AND/OR).
4. `test_gp_mutation_maintains_depth_limit`: Verify mutation respects the `max_conditions=5` limit and does not nest logic blocks.
5. `test_gp_fitness_adapter_integration`: Verify that a compiled GP Strategy successfully returns a numeric score from `make_fitness_adapter`.
