```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Zeeuwse-Energie-Houdstermaatschappij" or company = "Zeeuwse Energie Houdstermaatschappij")
sort location, dt_announce desc
```
