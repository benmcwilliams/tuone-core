```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Fund for Financing the Decommissioning of the Krško NPP (Fond NEK)"
sort location, dt_announce desc
```
