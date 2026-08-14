// GridFlex Newton-Raphson AC power flow solver.
//
// Supports SLACK (1), PV (2) and PQ (3) buses. Initial voltage magnitudes and
// angles are taken from the input variables. Iterates until the largest
// mismatch falls below `tolerance` or `max_iterations` is reached.
//
// Signature:
//   [converged, iterations, max_mismatch, V, theta] = ...
//       gridflex_newton_raphson(bus_count, bus_type, bus_v0, bus_theta0_deg, ...
//           bus_p_spec, bus_q_spec, G, B, tolerance, max_iterations)
//
// theta is returned in RADIANS.

function [P, Q] = gridflex_power_injections(bus_count, V, theta, G, B)

    P = zeros(1, bus_count);
    Q = zeros(1, bus_count);

    for i = 1:bus_count
        for j = 1:bus_count
            d = theta(i) - theta(j);
            P(i) = P(i) + V(i) * V(j) * (G(i, j) * cos(d) + B(i, j) * sin(d));
            Q(i) = Q(i) + V(i) * V(j) * (G(i, j) * sin(d) - B(i, j) * cos(d));
        end
    end

endfunction

function [converged, iterations, max_mismatch, V, theta, P, Q] = gridflex_newton_raphson(..
    bus_count, bus_type, bus_v0, bus_theta0_deg, bus_p_spec, bus_q_spec, ..
    G, B, tolerance, max_iterations)

    V = bus_v0;
    theta = bus_theta0_deg * %pi / 180;

    converged = %f;
    iterations = 0;
    max_mismatch = 0;

    npv = [];
    npq = [];
    for i = 1:bus_count
        if bus_type(i) == 2 then
            npv = [npv i];
        elseif bus_type(i) == 3 then
            npq = [npq i];
        end
    end
    pvpq = [npv npq];
    m = length(pvpq);
    n2 = length(npq);

    for it = 1:max_iterations

        [P, Q] = gridflex_power_injections(bus_count, V, theta, G, B);

        dP = bus_p_spec - P;
        dQ = bus_q_spec - Q;

        mismatch = [];
        for i = pvpq
            mismatch = [mismatch dP(i)];
        end
        for i = npq
            mismatch = [mismatch dQ(i)];
        end

        max_mismatch = 0;
        for k = 1:length(mismatch)
            if abs(mismatch(k)) > max_mismatch then
                max_mismatch = abs(mismatch(k));
            end
        end

        if max_mismatch < tolerance then
            converged = %t;
            iterations = it;
            return;
        end

        J = zeros(m + n2, m + n2);

        for i = 1:m
            ii = pvpq(i);
            for j = 1:m
                jj = pvpq(j);
                if ii == jj then
                    J(i, j) = -Q(ii) - B(ii, ii) * V(ii)^2;
                else
                    d = theta(ii) - theta(jj);
                    J(i, j) = V(ii) * V(jj) * (G(ii, jj) * sin(d) - B(ii, jj) * cos(d));
                end
            end
            for j = 1:n2
                jj = npq(j);
                if ii == jj then
                    J(i, m + j) = P(ii) + G(ii, ii) * V(ii)^2;
                else
                    d = theta(ii) - theta(jj);
                    J(i, m + j) = V(ii) * V(jj) * (G(ii, jj) * cos(d) + B(ii, jj) * sin(d));
                end
            end
        end

        for i = 1:n2
            ii = npq(i);
            for j = 1:m
                jj = pvpq(j);
                if ii == jj then
                    J(m + i, j) = P(ii) - G(ii, ii) * V(ii)^2;
                else
                    d = theta(ii) - theta(jj);
                    J(m + i, j) = -V(ii) * V(jj) * (G(ii, jj) * cos(d) + B(ii, jj) * sin(d));
                end
            end
            for j = 1:n2
                jj = npq(j);
                if ii == jj then
                    J(m + i, m + j) = Q(ii) - B(ii, ii) * V(ii)^2;
                else
                    d = theta(ii) - theta(jj);
                    J(m + i, m + j) = V(ii) * V(jj) * (G(ii, jj) * sin(d) - B(ii, jj) * cos(d));
                end
            end
        end

        delta = J \ mismatch';

        for k = 1:m
            theta(pvpq(k)) = theta(pvpq(k)) + delta(k);
        end
        for k = 1:n2
            V(npq(k)) = V(npq(k)) * (1 + delta(m + k));
        end
    end

    iterations = max_iterations;

endfunction
