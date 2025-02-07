```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ailes-Marines" or company = "Ailes Marines")
sort location, dt_announce desc
```
