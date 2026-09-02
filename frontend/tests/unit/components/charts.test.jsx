import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import LineChartMock from "../../../src/components/charts/LineChartMock";
import BarChartMock from "../../../src/components/charts/BarChartMock";
import PieChartMock from "../../../src/components/charts/PieChartMock";

describe("chart mocks", () => {
  it("muestra sin datos en LineChartMock", () => {
    render(<LineChartMock />);
    expect(screen.getByText(/sin datos/i)).toBeInTheDocument();
  });

  it("muestra barras con etiquetas en BarChartMock", () => {
    render(<BarChartMock data={[10, 20]} labels={["A", "B"]} />);
    expect(screen.getByText("A")).toBeInTheDocument();
    expect(screen.getByText("B")).toBeInTheDocument();
  });

  it("muestra segmentos en PieChartMock", () => {
    render(<PieChartMock segments={[{ label: "Alta", value: 60, color: "#10b981" }]} />);
    expect(screen.getByText(/alta/i)).toBeInTheDocument();
    expect(screen.getAllByText(/60\s*%/i)).toHaveLength(1);
  });
});