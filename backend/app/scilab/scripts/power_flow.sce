// GridFlex power-flow driver.
//
// Entry point executed in the isolated temporary directory. Loads the input
// variables, runs the Newton-Raphson solve, computes line flows, and writes
// the structured result file. Nothing user-supplied is ever executed; this
// script and the functions it loads are internal GridFlex assets.
//
// Execution is always non-interactive (`-nb -nw`), so the process exits.

exec('inputs.sci', -1);
exec('build_ybus.sci', -1);
exec('newton_raphson.sci', -1);
exec('calculate_line_flows.sci', -1);
exec('export_results.sci', -1);

[G, B] = gridflex_build_ybus(bus_count, lines, line_count);

[converged, iterations, max_mismatch, V, theta_rad, P, Q] = gridflex_newton_raphson(..
    bus_count, bus_type, bus_v0, bus_theta0_deg, bus_p_spec, bus_q_spec, ..
    G, B, tolerance, max_iterations);

flows = gridflex_line_flows(bus_count, V, theta_rad, lines, line_count);

gridflex_export_results(..
    'gridflex_results.txt', converged, iterations, max_mismatch, ..
    V, theta_rad * 180 / %pi, P, Q, flows);

exit;
