```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energetica-Industries" or company = "Energetica Industries")
sort location, dt_announce desc
```
