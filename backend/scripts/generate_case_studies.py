import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "case_studies"))

sample_grid = {
    "grid_id": "sample",
    "name": "GridFlex Sample Network",
    "base_mva": 100,
    "buses": [
        {"id": "B1", "name": "Slack Bus", "type": "SLACK", "base_voltage": 138, "voltage_magnitude": 1.06, "voltage_angle": 0.0},
        {"id": "B2", "name": "Bus 2", "type": "PV", "base_voltage": 138, "voltage_magnitude": 1.04, "voltage_angle": 0.0},
        {"id": "B3", "name": "Bus 3", "type": "PV", "base_voltage": 138, "voltage_magnitude": 1.02, "voltage_angle": 0.0},
        {"id": "B4", "name": "Bus 4", "type": "PQ", "base_voltage": 138, "voltage_magnitude": 1.0, "voltage_angle": 0.0},
        {"id": "B5", "name": "Bus 5", "type": "PQ", "base_voltage": 138, "voltage_magnitude": 1.0, "voltage_angle": 0.0}
    ],
    "lines": [
        {"id": "L1", "name": "Line 1-2", "from_bus": "B1", "to_bus": "B2", "resistance": 0.02, "reactance": 0.08, "susceptance": 0.02, "thermal_limit": 250},
        {"id": "L2", "name": "Line 1-4", "from_bus": "B1", "to_bus": "B4", "resistance": 0.05, "reactance": 0.20, "susceptance": 0.02, "thermal_limit": 200},
        {"id": "L3", "name": "Line 2-3", "from_bus": "B2", "to_bus": "B3", "resistance": 0.04, "reactance": 0.16, "susceptance": 0.02, "thermal_limit": 150},
        {"id": "L4", "name": "Line 2-5", "from_bus": "B2", "to_bus": "B5", "resistance": 0.03, "reactance": 0.12, "susceptance": 0.02, "thermal_limit": 180},
        {"id": "L5", "name": "Line 3-4", "from_bus": "B3", "to_bus": "B4", "resistance": 0.04, "reactance": 0.16, "susceptance": 0.02, "thermal_limit": 150},
        {"id": "L6", "name": "Line 4-5", "from_bus": "B4", "to_bus": "B5", "resistance": 0.05, "reactance": 0.20, "susceptance": 0.02, "thermal_limit": 120},
        {"id": "L7", "name": "Line 1-3", "from_bus": "B1", "to_bus": "B3", "resistance": 0.08, "reactance": 0.30, "susceptance": 0.03, "thermal_limit": 120}
    ],
    "generators": [
        {"id": "G1", "name": "Slack Generator", "bus_id": "B1", "type": "CONVENTIONAL", "active_power": 0.0, "reactive_power": 0.0, "active_power_min": 0, "active_power_max": 300, "reactive_power_min": -100, "reactive_power_max": 100},
        {"id": "G2", "name": "Thermal Plant", "bus_id": "B2", "type": "CONVENTIONAL", "active_power": 60.0, "reactive_power": 30.0, "active_power_min": 0, "active_power_max": 200, "reactive_power_min": -60, "reactive_power_max": 60},
        {"id": "G3", "name": "Solar Farm", "bus_id": "B3", "type": "SOLAR", "active_power": 40.0, "reactive_power": 0.0, "active_power_min": 0, "active_power_max": 100, "reactive_power_min": -40, "reactive_power_max": 40}
    ],
    "loads": [
        {"id": "D1", "name": "Load 1", "bus_id": "B4", "active_power": 40.0, "reactive_power": 20.0},
        {"id": "D2", "name": "Load 2", "bus_id": "B5", "active_power": 50.0, "reactive_power": 25.0},
        {"id": "D3", "name": "Load 3", "bus_id": "B4", "active_power": 25.0, "reactive_power": 10.0}
    ]
}

cases = [
    {
        "id": "normal_operation",
        "name": "Normal Grid Operation",
        "description": "Demonstrate a healthy grid with no critical violations.",
        "objective": "Verify power flow convergence and baseline health.",
        "grid": sample_grid,
        "scenario": {},
        "expected_conditions": {
            "converged": True,
            "max_voltage_pu": 1.06,
            "min_voltage_pu": 0.95,
            "overloaded_lines": 0
        },
        "readme": "# Normal Operation\n\nPurpose: Demonstrate a healthy grid.\nExpected:\n* Power flow converges.\n* No critical voltage violations.\n* No overloaded lines.\n* Low or moderate stress."
    },
    {
        "id": "renewable_integration",
        "name": "Renewable Integration",
        "description": "Demonstrate increasing solar generation and its impact.",
        "objective": "Show penetration changes, voltage changes, and line loading changes.",
        "grid": sample_grid,
        "scenario": {"solar_output_mw": 80.0},
        "expected_conditions": {
            "converged": True,
            "overloaded_lines": 0
        },
        "readme": "# Renewable Integration\n\nPurpose: Demonstrate increasing solar generation.\nScenarios: Base, Low solar, Medium solar, High solar."
    },
    {
        "id": "over_voltage",
        "name": "Over-Voltage Condition",
        "description": "Demonstrate excessive renewable generation causing measurable voltage impact.",
        "objective": "Detect over-voltage issue and test mitigation.",
        "grid": sample_grid,
        "scenario": {"solar_output_mw": 200.0},
        "expected_conditions": {
            "converged": True,
            "max_voltage_pu": 1.10
        },
        "readme": "# Over-Voltage Condition\n\nPurpose: Demonstrate excessive renewable generation causing measurable voltage impact.\nPossible mitigation: Battery charging or curtailment."
    },
    {
        "id": "line_overload",
        "name": "Line Overload",
        "description": "Demonstrate transmission congestion.",
        "objective": "Increase load to detect overloaded line and recommend mitigation options.",
        "grid": sample_grid,
        "scenario": {"load_scale": 1.5},
        "expected_conditions": {
            "converged": True,
            "overloaded_lines": 1
        },
        "readme": "# Line Overload\n\nPurpose: Demonstrate transmission congestion.\nWorkflow: Increase load -> detect line -> recommend mitigation."
    },
    {
        "id": "battery_support",
        "name": "Battery Support",
        "description": "Demonstrate storage as a scenario tool.",
        "objective": "Compare renewable only vs renewable plus battery.",
        "grid": sample_grid,
        "scenario": {"solar_output_mw": 150.0, "battery_output_mw": -50.0},
        "expected_conditions": {
            "converged": True
        },
        "readme": "# Battery Support\n\nPurpose: Demonstrate storage as a scenario tool.\nCompare: Renewable only vs Renewable plus battery."
    }
]

def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    for case in cases:
        case_dir = os.path.join(BASE_DIR, case["id"])
        os.makedirs(case_dir, exist_ok=True)
        
        # grid.json
        grid = dict(case["grid"])
        grid["grid_id"] = f"case_{case['id']}"
        with open(os.path.join(case_dir, "grid.json"), "w") as f:
            json.dump(grid, f, indent=2)
            
        # scenario.json
        with open(os.path.join(case_dir, "scenario.json"), "w") as f:
            json.dump(case["scenario"], f, indent=2)
            
        # expected_conditions.json
        with open(os.path.join(case_dir, "expected_conditions.json"), "w") as f:
            json.dump(case["expected_conditions"], f, indent=2)
            
        # README.md
        with open(os.path.join(case_dir, "README.md"), "w") as f:
            f.write(case["readme"])
            
        # Metadata
        metadata = {
            "id": case["id"],
            "name": case["name"],
            "description": case["description"],
            "objective": case["objective"]
        }
        with open(os.path.join(case_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    main()
