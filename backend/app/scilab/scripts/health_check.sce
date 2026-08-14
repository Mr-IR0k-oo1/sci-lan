// GridFlex health check.
//
// Verifies the Scilab runtime can load the GridFlex solver functions and
// execute a small numerical computation (a two-bus Y-bus). Writes a structured
// status file that Python parses.
//
//     health_check v1
//     status ok|failed
//     message <free text>
//
// If the process fails before writing the file, the Python side treats the
// health check as failed.

function [] = gridflex_health_main()

    fd = mopen('health_check.txt', 'w');
    mfprintf(fd, 'health_check v1\n');
    mfprintf(fd, 'status running\n');
    mfprintf(fd, 'message started\n');
    mclose(fd);

    exec('build_ybus.sci', -1);
    exec('newton_raphson.sci', -1);
    exec('calculate_line_flows.sci', -1);

    n = 2;
    lines_test = [1 2 0.02 0.06 0.03];
    [G, B] = gridflex_build_ybus(n, lines_test, 1);

    if size(G, 1) <> n then
        fd = mopen('health_check.txt', 'w');
        mfprintf(fd, 'health_check v1\n');
        mfprintf(fd, 'status failed\n');
        mfprintf(fd, 'message ybus matrix has unexpected size\n');
        mclose(fd);
        return;
    end

    [converged, iterations, max_mismatch, V, theta, P, Q] = gridflex_newton_raphson(..
        2, [1 3], [1.0 1.0], [0 0], [0 -1], [0 -0.4], ..
        G, B, 1e-6, 20);

    fd = mopen('health_check.txt', 'w');
    mfprintf(fd, 'health_check v1\n');
    mfprintf(fd, 'status ok\n');
    mfprintf(fd, 'message ybus %dx%d, nr converged=%d iter=%d max_mismatch=%.9g\n', ..
        size(G, 1), size(G, 2), converged, iterations, max_mismatch);
    mclose(fd);

endfunction

gridflex_health_main();
exit;
