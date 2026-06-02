import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { SampleData } from "../SampleData";

describe("SampleData", () => {
  it("renders sequencing and analysis status badges", () => {
    render(<SampleData patientId="DNA-001" enrollmentDate="2026-04-12" />);

    expect(screen.getByText("DNA sequencing")).toBeInTheDocument();
    expect(screen.getByText("Not done")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("opens the modal and marks the sample as analyzed when sequencing data exists", async () => {
    const user = userEvent.setup();

    render(
      <SampleData
        patientId="DNA-002"
        enrollmentDate="2026-04-12"
        genomicData={{
          polygenic: {
            coronaryArteryDisease: 0.61,
            myocardialInfarction: 0.44,
            strokeRisk: 0.22,
            atrialFibrillation: 0.18,
          },
          variants: [],
          pharmacogenomics: [],
          ancestry: {
            european: 0.72,
            african: 0.18,
            asian: 0.06,
            native_american: 0,
            other: 0.04,
          },
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Analyze Sample" }));

    expect(screen.getByText("FASTQ details")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Start Analysis" }));

    expect(screen.getByText("Analyzed")).toBeInTheDocument();
  });
});