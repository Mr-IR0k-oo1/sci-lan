// GridFlex Y-Bus builder.
//
// Constructs the bus admittance matrix (G + jB) from the line list.
// Lines use 1-based bus indices (as emitted by the Python input renderer).
//
// Signature:
//   [G, B] = gridflex_build_ybus(bus_count, lines, line_count)
//
//   lines(k, :) = [from_index, to_index, resistance, reactance, susceptance]

function [G, B] = gridflex_build_ybus(bus_count, lines, line_count)

    G = zeros(bus_count, bus_count);
    B = zeros(bus_count, bus_count);

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

        G(i, i) = G(i, i) + real(ys) + real(ysh);
        B(i, i) = B(i, i) + imag(ys) + imag(ysh);
        G(j, j) = G(j, j) + real(ys) + real(ysh);
        B(j, j) = B(j, j) + imag(ys) + imag(ysh);

        G(i, j) = G(i, j) - real(ys);
        B(i, j) = B(i, j) - imag(ys);
        G(j, i) = G(j, i) - real(ys);
        B(j, i) = B(j, i) - imag(ys);
    end

endfunction
