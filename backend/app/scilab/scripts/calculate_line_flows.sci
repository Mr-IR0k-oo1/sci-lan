// GridFlex line flow calculator.
//
// Computes per-line complex power at both ends from the solved voltage vector.
// theta is in RADIANS.
//
// Signature:
//   flows = gridflex_line_flows(bus_count, V, theta, lines, line_count)
//
// flows is (line_count x 4): [P_from, Q_from, P_to, Q_to] in per-unit.

function [flows] = gridflex_line_flows(bus_count, V, theta, lines, line_count)

    flows = zeros(line_count, 4);

    for k = 1:line_count
        i = lines(k, 1);
        j = lines(k, 2);
        r = lines(k, 3);
        x = lines(k, 4);
        b = lines(k, 5);

        z = r + %i * x;
        if abs(z) < 1e-12 then
            continue;
        end

        ys = 1 / z;
        ysh = %i * b / 2;

        v_from = V(i) * exp(%i * theta(i));
        v_to = V(j) * exp(%i * theta(j));

        i_from = (v_from - v_to) * ys + v_from * ysh;
        i_to = (v_to - v_from) * ys + v_to * ysh;

        s_from = v_from * conj(i_from);
        s_to = v_to * conj(i_to);

        flows(k, 1) = real(s_from);
        flows(k, 2) = imag(s_from);
        flows(k, 3) = real(s_to);
        flows(k, 4) = imag(s_to);
    end

endfunction
