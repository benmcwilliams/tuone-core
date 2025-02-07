```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "General-Fusion" or company = "General Fusion")
sort location, dt_announce desc
```
