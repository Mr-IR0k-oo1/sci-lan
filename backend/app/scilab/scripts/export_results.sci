// GridFlex structured result export.
//
// Writes the deterministic, machine-readable result file documented in
// docs/architecture/SCILAB_INTEGRATION.md:
//
//     gridflex_results v1
//     converged <0|1>
//     iterations <int>
//     max_mismatch <float>
//     bus_count <n>
//     bus_v <n floats>
//     bus_theta_deg <n floats>
//     bus_p_pu <n floats>
//     bus_q_pu <n floats>
//     line_count <m>
//     line_flows <4*m floats: P_from Q_from P_to Q_to per line>
//
// This labeled, deterministic format is safe for Python to parse without
// relying on human-readable console output. If `jsonencode` is available the
// same data is also written to <output>.json (see `gridflex_export_json`).
//
// Signature:
//   gridflex_export_results(output_path, converged, iterations, max_mismatch, ..
//       V, theta_deg, P, Q, flows)

function [] = gridflex_write_vector(fd, label, values)
    mfprintf(fd, '%s ', label);
    for k = 1:length(values)
        mfprintf(fd, '%.9g ', values(k));
    end
    mfprintf(fd, '\n');
endfunction

function [] = gridflex_export_results(..
    output_path, converged, iterations, max_mismatch, ..
    V, theta_deg, P, Q, flows)

    fd = mopen(output_path, 'w');

    mfprintf(fd, 'gridflex_results v1\n');
    if converged then
        mfprintf(fd, 'converged 1\n');
    else
        mfprintf(fd, 'converged 0\n');
    end
    mfprintf(fd, 'iterations %d\n', iterations);
    mfprintf(fd, 'max_mismatch %.9g\n', max_mismatch);
    mfprintf(fd, 'bus_count %d\n', length(V));

    gridflex_write_vector(fd, 'bus_v', V);
    gridflex_write_vector(fd, 'bus_theta_deg', theta_deg);
    gridflex_write_vector(fd, 'bus_p_pu', P);
    gridflex_write_vector(fd, 'bus_q_pu', Q);

    mfprintf(fd, 'line_count %d\n', size(flows, 1));
    mfprintf(fd, 'line_flows ');
    for k = 1:size(flows, 1)
        mfprintf(fd, '%.9g %.9g %.9g %.9g ', ..
            flows(k, 1), flows(k, 2), flows(k, 3), flows(k, 4));
    end
    mfprintf(fd, '\n');

    mclose(fd);

endfunction
