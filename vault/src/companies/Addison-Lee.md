```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Addison-Lee" or company = "Addison Lee")
sort location, dt_announce desc
```
