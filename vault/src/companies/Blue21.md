```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Blue21" or company = "Blue21")
sort location, dt_announce desc
```
