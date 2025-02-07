```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Max-Planck-Institute-for-Plasma-Physics" or company = "Max Planck Institute for Plasma Physics")
sort location, dt_announce desc
```
