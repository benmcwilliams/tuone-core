```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Daimler-Trucks" or company = "Daimler Trucks")
sort location, dt_announce desc
```
