```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Power to Green Hydrogen Mallorca (P2GH2M)"
sort location, dt_announce desc
```
