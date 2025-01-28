```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Alliander" or company = "Alliander")
sort location, dt_announce desc
```
