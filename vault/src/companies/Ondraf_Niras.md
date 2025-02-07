```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ondraf_Niras" or company = "Ondraf_Niras")
sort location, dt_announce desc
```
