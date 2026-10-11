import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusChip } from "@/components/StatusChip";

describe("StatusChip", () => {
  it("includes an icon and a readable status label", () => {
    render(<StatusChip status="red" />);
    expect(screen.getByText("Needs attention")).toBeInTheDocument();
    expect(screen.getByText("■")).toBeInTheDocument();
  });
});
