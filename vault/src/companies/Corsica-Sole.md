```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Corsica-Sole" or company = "Corsica Sole")
sort location, dt_announce desc
```
