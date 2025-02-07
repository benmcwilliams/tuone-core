```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Cumbria-Waste-Repository" or company = "Cumbria Waste Repository")
sort location, dt_announce desc
```
