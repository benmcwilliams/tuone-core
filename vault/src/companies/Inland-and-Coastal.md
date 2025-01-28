```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Inland-and-Coastal" or company = "Inland and Coastal")
sort location, dt_announce desc
```
