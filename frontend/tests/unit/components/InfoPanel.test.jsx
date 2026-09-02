import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import InfoPanel from "../../../src/components/auth/InfoPanel";

describe("InfoPanel", () => {
  it("muestra el branding y las imagenes informativas", () => {
    render(<InfoPanel />);

    expect(screen.getByText(/sistema academico/i)).toBeInTheDocument();
    expect(screen.getByAltText(/logo/i)).toBeInTheDocument();
    expect(screen.getByAltText(/estudiantes en aula/i)).toBeInTheDocument();
  });
});