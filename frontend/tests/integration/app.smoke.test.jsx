import React from "react";
import { render, screen } from "@testing-library/react";
import App from "../../src/App.jsx";

describe("App", () => {
  it("renderiza pantalla inicial de login", () => {
    render(<App />);
    expect(screen.getByText(/bienvenido/i)).toBeInTheDocument();
  });
});
