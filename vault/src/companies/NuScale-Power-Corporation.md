```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "NuScale-Power-Corporation" or company = "NuScale Power Corporation")
sort location, dt_announce desc
```
