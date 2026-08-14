function [converged, iterations, max_mismatch, V, theta] = gridflex_solve(..
    base_mva, bus_type, bus_v0, bus_theta0, bus_p_spec, bus_q_spec, ..
    lines, line_count, tolerance, max_iterations)

    n = length(bus_type);

    G = zeros(n, n);
    B = zeros(n, n);
    for k = 1:line_count
        i = lines(k, 1);
        j = lines(k, 2);
        r = lines(k, 3);
        x = lines(k, 4);
        b = lines(k, 5);
        z = r + %i * x;
        ys = 1 / z;
        ysh = %i * b / 2;
        G(i, i) = G(i, i) + real(ys) + real(ysh);
        B(i, i) = B(i, i) + imag(ys) + imag(ysh);
        G(j, j) = G(j, j) + real(ys) + real(ysh);
        B(j, j) = B(j, j) + imag(ys) + imag(ysh);
        G(i, j) = G(i, j) - real(ys);
        B(i, j) = B(i, j) - imag(ys);
        G(j, i) = G(j, i) - real(ys);
        B(j, i) = B(j, i) - imag(ys);
    end

    V = bus_v0;
    theta = bus_theta0 * %pi / 180;

    converged = %f;
    iterations = 0;
    max_mismatch = 0;

    for it = 1:max_iterations
        P = zeros(1, n);
        Q = zeros(1, n);
        for i = 1:n
            for j = 1:n
                d = theta(i) - theta(j);
                P(i) = P(i) + V(i) * V(j) * (G(i, j) * cos(d) + B(i, j) * sin(d));
                Q(i) = Q(i) + V(i) * V(j) * (G(i, j) * sin(d) - B(i, j) * cos(d));
            end
        end

        H = zeros(n, n);
        Nm = zeros(n, n);
        Jm = zeros(n, n);
        Lm = zeros(n, n);
        for i = 1:n
            for j = 1:n
                d = theta(i) - theta(j);
                if i == j
                    H(i, i) = -Q(i) - B(i, i) * V(i)^2;
                    Nm(i, i) = P(i) + G(i, i) * V(i)^2;
                    Jm(i, i) = P(i) - G(i, i) * V(i)^2;
                    Lm(i, i) = Q(i) - B(i, i) * V(i)^2;
                else
                    H(i, j) = V(i) * V(j) * (G(i, j) * sin(d) - B(i, j) * cos(d));
                    Nm(i, j) = V(i) * V(j) * (G(i, j) * cos(d) + B(i, j) * sin(d));
                    Jm(i, j) = -V(i) * V(j) * (G(i, j) * cos(d) + B(i, j) * sin(d));
                    Lm(i, j) = V(i) * V(j) * (G(i, j) * sin(d) - B(i, j) * cos(d));
                end
            end
        end

        dP = bus_p_spec - P;
        dQ = bus_q_spec - Q;

        nslack = [];
        npq = [];
        for i = 1:n
            if bus_type(i) == 1
                continue;
            end
            nslack = [nslack i];
            if bus_type(i) == 3
                npq = [npq i];
            end
        end

        mismatch = [];
        for i = nslack
            mismatch = [mismatch dP(i)];
        end
        for i = npq
            mismatch = [mismatch dQ(i)];
        end

        max_mismatch = 0;
        for k = 1:length(mismatch)
            if abs(mismatch(k)) > max_mismatch
                max_mismatch = abs(mismatch(k));
            end
        end

        if max_mismatch < tolerance
            converged = %t;
            iterations = it;
            return;
        end

        ntheta = length(nslack);
        J = [];
        for i = 1:ntheta
            row = [];
            for j = 1:ntheta
                row = [row H(nslack(i), nslack(j))];
            end
            for j = 1:length(npq)
                row = [row Nm(nslack(i), npq(j))];
            end
            J = [J; row];
        end
        for i = 1:length(npq)
            row = [];
            for j = 1:ntheta
                row = [row Jm(npq(i), nslack(j))];
            end
            for j = 1:length(npq)
                row = [row Lm(npq(i), npq(j))];
            end
            J = [J; row];
        end

        delta = J \ mismatch';

        for k = 1:ntheta
            theta(nslack(k)) = theta(nslack(k)) + delta(k);
        end
        for k = 1:length(npq)
            V(npq(k)) = V(npq(k)) * (1 + delta(ntheta + k));
        end
    end

    iterations = max_iterations;
endfunction
