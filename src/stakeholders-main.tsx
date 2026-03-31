import { createRoot } from "react-dom/client";
import { StakeholderSite } from "./stakeholders/StakeholderSite";
import "./stakeholders/stakeholders.css";

createRoot(document.getElementById("stakeholder-root")!).render(<StakeholderSite />);