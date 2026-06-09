# Simulation: MiroFish

## 1. Simulation Decision

MiroFish is the scenario simulation and report lab.

It is not the backend brain, not the memory source of truth, and not an action
executor. It is an external runtime used by Hermes for structured simulation.

## 2. Use Cases

Use MiroFish for:

- product strategy comparison;
- project go/no-go decisions;
- market bull/bear scenarios;
- risk and opportunity rehearsal;
- multi-agent debate;
- execution plan stress tests;
- commercial positioning review.

## 3. Simulation Flow

```text
Obsidian context
  -> Hermes simulation brief
  -> MiroFish multi-agent run
  -> simulation report
  -> PostgreSQL simulation_runs metadata
  -> Obsidian 70-Reports/simulations
  -> decision note in 60-Decisions when owner approves
```

## 4. Simulation Brief

A simulation brief must include:

- question;
- decision owner;
- background;
- known facts;
- unknowns;
- constraints;
- options;
- risk categories;
- evidence links;
- required output format.

## 5. Output Requirements

MiroFish output must include:

- executive summary;
- competing viewpoints;
- assumptions;
- risk matrix;
- opportunity matrix;
- recommended option;
- confidence;
- what would change the recommendation;
- owner decision checkpoint.

No simulation output may directly trigger a high-risk action.

